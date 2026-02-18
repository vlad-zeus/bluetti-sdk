"""Unit tests for Client orchestration layer."""

from unittest.mock import Mock

import pytest
from power_sdk.client import Client
from power_sdk.contracts.types import ParsedRecord
from power_sdk.devices.types import BlockGroupDefinition, DeviceProfile
from power_sdk.errors import ProtocolError, TransportError
from power_sdk.models.device import V2Device
from power_sdk.models.types import BlockGroup
from power_sdk.plugins.bluetti.v2.profiles import get_device_profile
from power_sdk.plugins.bluetti.v2.protocol.datatypes import UInt16
from power_sdk.plugins.bluetti.v2.protocol.layer import ModbusProtocolLayer
from power_sdk.plugins.bluetti.v2.protocol.parser import V2Parser
from power_sdk.plugins.bluetti.v2.protocol.schema import BlockSchema, Field
from power_sdk.plugins.bluetti.v2.schemas.registry import SchemaRegistry


def build_test_response(data: bytes) -> bytes:
    """Build valid Modbus response frame with CRC.

    Args:
        data: Raw data bytes (without framing)

    Returns:
        Complete Modbus frame with valid CRC
    """
    # Build frame: [addr][func][count][data...][crc]
    device_addr = 0x01
    function_code = 0x03
    byte_count = len(data)

    frame = bytes([device_addr, function_code, byte_count]) + data

    # Calculate CRC16-Modbus
    crc = 0xFFFF
    for byte in frame:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1

    # Append CRC (little-endian)
    frame_with_crc = frame + bytes([crc & 0xFF, (crc >> 8) & 0xFF])

    return frame_with_crc


@pytest.fixture
def mock_transport():
    """Create mock transport."""
    transport = Mock()
    transport.connect = Mock()
    transport.disconnect = Mock()
    transport.is_connected = Mock(return_value=True)
    # Use valid Modbus response with proper CRC
    transport.send_frame = Mock(
        return_value=build_test_response(bytes([0x00, 0x64, 0x00, 0xC8]))
    )
    return transport


@pytest.fixture
def device_profile():
    """Get EL100V2 device profile."""
    return get_device_profile("EL100V2")


@pytest.fixture
def mock_schema():
    """Create mock schema."""
    schema = BlockSchema(
        block_id=1300,
        name="TEST_BLOCK",
        description="Test block for unit tests",
        min_length=4,
        fields=[
            Field(name="field1", offset=0, type=UInt16()),
            Field(name="field2", offset=2, type=UInt16()),
        ],
    )
    return schema


def test_client_creation(mock_transport, device_profile):
    """Test Client creation."""
    client = Client(
        transport=mock_transport, profile=device_profile, device_address=1
    )

    assert client.profile.model == "EL100V2"
    assert client.device is not None
    assert client.transport is mock_transport


def test_client_with_custom_device_address(mock_transport, device_profile):
    """Test Client with custom device address."""
    client = Client(
        transport=mock_transport, profile=device_profile, device_address=5
    )

    assert client.device_address == 5


def test_client_connect(mock_transport, device_profile):
    """Test client connect."""
    client = Client(transport=mock_transport, profile=device_profile)

    client.connect()

    mock_transport.connect.assert_called_once()


def test_client_disconnect(mock_transport, device_profile):
    """Test client disconnect."""
    client = Client(transport=mock_transport, profile=device_profile)

    client.disconnect()

    mock_transport.disconnect.assert_called_once()


def test_client_auto_registers_schemas(mock_transport, device_profile):
    """Test that schemas are auto-registered from SchemaRegistry."""
    client = Client(transport=mock_transport, profile=device_profile)

    # Schemas should be auto-registered for blocks in profile
    # EL100V2 profile has core=[100], grid=[1300], battery=[6000]
    assert client.parser.get_schema(100) is not None  # APP_HOME_DATA
    assert client.parser.get_schema(1300) is not None  # INV_GRID_INFO
    assert client.parser.get_schema(6000) is not None  # PACK_MAIN_INFO

    # Check names match
    assert client.parser.get_schema(100).name == "APP_HOME_DATA"
    assert client.parser.get_schema(1300).name == "INV_GRID_INFO"
    assert client.parser.get_schema(6000).name == "PACK_MAIN_INFO"


def test_client_get_device_state(mock_transport, device_profile):
    """Test getting device state."""
    client = Client(transport=mock_transport, profile=device_profile)

    state = client.get_device_state()

    assert "device_id" in state
    assert "model" in state
    assert state["model"] == "EL100V2"


def test_client_get_group_state(mock_transport, device_profile):
    """Test getting group state."""
    client = Client(transport=mock_transport, profile=device_profile)

    grid_state = client.get_group_state(BlockGroup.GRID)

    assert "frequency" in grid_state
    assert "voltage" in grid_state


def test_client_manual_connect_disconnect(mock_transport, device_profile):
    """Test manual connect and disconnect."""
    client = Client(transport=mock_transport, profile=device_profile)

    client.connect()
    client.disconnect()

    # Should connect and disconnect
    mock_transport.connect.assert_called_once()
    mock_transport.disconnect.assert_called_once()


def _make_parsed_block(block_id: int) -> ParsedRecord:
    return ParsedRecord(
        block_id=block_id,
        name=f"BLOCK_{block_id}",
        values={"ok": True},
        raw=b"",
        length=0,
        protocol_version=2000,
        schema_version="1.0.0",
        timestamp=0.0,
    )


def test_read_group_ex_partial_collects_errors(mock_transport, device_profile):
    """read_group_ex returns parsed blocks and errors when partial_ok=True."""
    client = Client(transport=mock_transport, profile=device_profile)
    client._group_reader.read_block = Mock(
        side_effect=[
            _make_parsed_block(1100),
            TransportError("boom"),
            _make_parsed_block(1500),
        ]
    )

    result = client.read_group_ex(BlockGroup.INVERTER, partial_ok=True)

    assert len(result.blocks) == 2
    assert len(result.errors) == 1
    assert result.success is False
    assert result.partial is True
    assert result.errors[0][0] == 1400


def test_read_group_ex_fail_fast_raises(mock_transport, device_profile):
    """read_group_ex should fail fast when partial_ok=False."""
    client = Client(transport=mock_transport, profile=device_profile)
    client._group_reader.read_block = Mock(side_effect=TransportError("boom"))

    with pytest.raises(TransportError, match="boom"):
        client.read_group_ex(BlockGroup.INVERTER, partial_ok=False)


def test_read_group_partial_ok_by_default(mock_transport, device_profile):
    """read_group should return partial results by default (partial_ok=True)."""
    client = Client(transport=mock_transport, profile=device_profile)
    client._group_reader.read_block = Mock(
        side_effect=[
            _make_parsed_block(1100),
            TransportError("boom"),
            _make_parsed_block(1500),
        ]
    )

    # With default partial_ok=True, should return partial results
    blocks = client.read_group(BlockGroup.INVERTER)
    assert len(blocks) == 2  # Got 2 out of 3 blocks


def test_read_group_fail_fast_explicit(mock_transport, device_profile):
    """read_group should fail fast when partial_ok=False."""
    client = Client(transport=mock_transport, profile=device_profile)
    client._group_reader.read_block = Mock(
        side_effect=[
            _make_parsed_block(1100),
            TransportError("boom"),
            _make_parsed_block(1500),
        ]
    )

    with pytest.raises(TransportError, match="boom"):
        client.read_group(BlockGroup.INVERTER, partial_ok=False)


def test_dependency_injection_custom_parser(mock_transport, device_profile):
    """Test that custom parser can be injected."""
    mock_parser = Mock()
    mock_parser.get_schema = Mock(return_value=None)

    client = Client(
        transport=mock_transport, profile=device_profile, parser=mock_parser
    )

    assert client.parser is mock_parser


def test_dependency_injection_custom_protocol(mock_transport, device_profile):
    """Test that custom protocol layer can be injected."""
    mock_protocol = Mock()
    mock_protocol.read_block = Mock()

    client = Client(
        transport=mock_transport,
        profile=device_profile,
        protocol=mock_protocol,
    )

    assert client.protocol is mock_protocol


def test_default_protocol_created_when_not_injected(mock_transport, device_profile):
    """Test that default protocol layer is created when not provided."""
    client = Client(transport=mock_transport, profile=device_profile)
    assert isinstance(client.protocol, ModbusProtocolLayer)


def test_unknown_profile_protocol_fails_fast(mock_transport):
    """Client should fail if profile references unknown protocol key."""
    unsupported = DeviceProfile(
        model="X",
        type_id="x",
        protocol="unknown_protocol",
        description="Unsupported protocol profile",
        groups={
            "core": BlockGroupDefinition(
                name="core",
                blocks=[100],
                description="core",
                poll_interval=5,
            )
        },
    )

    with pytest.raises(ProtocolError, match="Unknown protocol"):
        Client(transport=mock_transport, profile=unsupported)


def test_dependency_injection_custom_device(mock_transport, device_profile):
    """Test that custom device model can be injected."""
    mock_device = Mock()

    client = Client(
        transport=mock_transport, profile=device_profile, device=mock_device
    )

    assert client.device is mock_device


def test_dependency_injection_both_custom(mock_transport, device_profile):
    """Test that both parser and device can be injected together."""
    mock_parser = Mock()
    mock_parser.get_schema = Mock(return_value=None)
    mock_device = Mock()

    client = Client(
        transport=mock_transport,
        profile=device_profile,
        parser=mock_parser,
        device=mock_device,
    )

    assert client.parser is mock_parser
    assert client.device is mock_device


def test_default_dependencies_created_when_not_injected(mock_transport, device_profile):
    """Test that default parser and device are created when not provided."""

    client = Client(transport=mock_transport, profile=device_profile)

    # Should create default implementations
    assert isinstance(client.parser, V2Parser)
    assert isinstance(client.device, V2Device)


def test_client_uses_instance_scoped_registry(mock_transport, device_profile):
    """Each client can use its own schema registry instance."""
    reg1 = SchemaRegistry()
    reg2 = SchemaRegistry()

    client1 = Client(
        transport=mock_transport,
        profile=device_profile,
        schema_registry=reg1,
    )
    client2 = Client(
        transport=mock_transport,
        profile=device_profile,
        schema_registry=reg2,
    )

    assert client1.schema_registry is reg1
    assert client2.schema_registry is reg2


def test_schema_conflict_detection():
    """Registry should reject conflicting schemas for same block_id."""
    registry = SchemaRegistry()
    schema1 = BlockSchema(
        block_id=9999,
        name="SCHEMA_A",
        description="A",
        min_length=2,
        fields=[Field(name="f", offset=0, type=UInt16())],
    )
    schema2 = BlockSchema(
        block_id=9999,
        name="SCHEMA_B",
        description="B",
        min_length=2,
        fields=[Field(name="f", offset=0, type=UInt16())],
    )

    registry.register(schema1)
    with pytest.raises(ValueError, match="already registered"):
        registry.register(schema2)


def test_client_schema_isolation_custom_registry(mock_transport, device_profile):
    """Different client registries should remain isolated for custom schemas."""
    reg1 = SchemaRegistry()
    reg2 = SchemaRegistry()
    custom = BlockSchema(
        block_id=9998,
        name="CUSTOM_ONLY_REG1",
        description="custom",
        min_length=2,
        fields=[Field(name="x", offset=0, type=UInt16())],
    )

    reg1.register(custom)
    assert reg1.get(9998) is not None
    assert reg2.get(9998) is None


def test_client_uses_instance_registry_by_default(mock_transport, device_profile):
    """Test that clients without explicit registry use isolated instances.

    Two Client instances created without passing schema_registry parameter
    should have independent registries - custom schemas in one should not
    affect the other.
    """
    # Create two clients without explicit registry
    client1 = Client(transport=mock_transport, profile=device_profile)
    client2 = Client(transport=mock_transport, profile=device_profile)

    # Verify they have different registry instances
    assert client1.schema_registry is not client2.schema_registry

    # Register custom schema in client1's registry
    custom = BlockSchema(
        block_id=9997,
        name="CUSTOM_CLIENT1",
        description="Custom for client1",
        min_length=2,
        fields=[Field(name="val", offset=0, type=UInt16())],
    )
    client1.schema_registry.register(custom)

    # Verify isolation: client2 doesn't see client1's custom schema
    assert client1.schema_registry.get(9997) is not None
    assert client2.schema_registry.get(9997) is None


def test_client_accepts_injected_registry(mock_transport, device_profile):
    """Test that explicitly passed registry is used by the client.

    When a SchemaRegistry instance is passed to Client, it should use
    that exact instance rather than creating a new one.
    """
    from power_sdk.plugins.bluetti.v2.schemas import new_registry_with_builtins

    custom_registry = new_registry_with_builtins()

    client = Client(
        transport=mock_transport,
        profile=device_profile,
        schema_registry=custom_registry,
    )

    # Verify identity: client uses the exact instance we provided
    assert client.schema_registry is custom_registry


def test_connect_retries_on_transport_error_then_succeeds(
    mock_transport, device_profile
):
    """Test connect retries on TransportError and eventually succeeds."""
    from power_sdk.errors import TransportError
    from power_sdk.utils.resilience import RetryPolicy

    # Fail twice, succeed on 3rd attempt
    call_count = 0

    def connect_side_effect():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise TransportError("Transient connection error")

    mock_transport.connect = Mock(side_effect=connect_side_effect)
    mock_transport.is_connected = Mock(return_value=True)

    policy = RetryPolicy(max_attempts=3, initial_delay=0.01, max_delay=0.05)
    client = Client(
        transport=mock_transport, profile=device_profile, retry_policy=policy
    )

    # Should succeed after retries
    client.connect()

    # Verify retry attempts
    assert call_count == 3
    assert mock_transport.connect.call_count == 3


def test_connect_exhausts_retries_and_raises(mock_transport, device_profile):
    """Test connect exhausts retries and raises TransportError."""
    from power_sdk.errors import TransportError
    from power_sdk.utils.resilience import RetryPolicy

    mock_transport.connect = Mock(
        side_effect=TransportError("Persistent connection error")
    )

    policy = RetryPolicy(max_attempts=2, initial_delay=0.01, max_delay=0.05)
    client = Client(
        transport=mock_transport, profile=device_profile, retry_policy=policy
    )

    # Should exhaust retries and raise
    with pytest.raises(TransportError, match="Persistent connection error"):
        client.connect()

    # Verify retry attempts
    assert mock_transport.connect.call_count == 2


def test_read_block_retries_on_transport_error_then_succeeds(
    mock_transport, device_profile
):
    """Test read_block retries on TransportError and eventually succeeds."""
    from power_sdk.errors import TransportError
    from power_sdk.utils.resilience import RetryPolicy

    # Setup: Fail twice, succeed on 3rd
    call_count = 0

    def send_frame_side_effect(frame, timeout):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise TransportError("Transient send error")
        # Success on 3rd attempt - return valid response with proper CRC
        # Block 100: dc_input_power (2 bytes) + ac_output_power (2 bytes)
        return build_test_response(bytes([0x00, 0x64, 0x00, 0xC8]))

    # Setup mock with side effect
    mock_transport.send_frame = Mock(side_effect=send_frame_side_effect)

    policy = RetryPolicy(max_attempts=3, initial_delay=0.01, max_delay=0.05)
    client = Client(
        transport=mock_transport, profile=device_profile, retry_policy=policy
    )

    # Should succeed after retries (block 100 has min 4 bytes)
    result = client.read_block(100)
    assert result is not None
    assert call_count == 3


def test_read_block_exhausts_retries_and_raises(mock_transport, device_profile):
    """Test read_block exhausts retries and raises TransportError."""
    from power_sdk.errors import TransportError
    from power_sdk.utils.resilience import RetryPolicy

    mock_transport.send_frame = Mock(
        side_effect=TransportError("Persistent send error")
    )

    policy = RetryPolicy(max_attempts=2, initial_delay=0.01, max_delay=0.05)
    client = Client(
        transport=mock_transport, profile=device_profile, retry_policy=policy
    )

    # Should exhaust retries and raise
    with pytest.raises(TransportError, match="Persistent send error"):
        client.read_block(100)

    # Verify retry attempts
    assert mock_transport.send_frame.call_count == 2


def test_read_block_no_retry_on_parser_error(mock_transport, device_profile):
    """Test read_block does not retry on ParserError (fail fast)."""
    from power_sdk.errors import ParserError
    from power_sdk.utils.resilience import RetryPolicy

    # Valid Modbus response with proper CRC, but parser will fail
    mock_transport.send_frame = Mock(
        return_value=build_test_response(bytes([0xFF, 0xFF, 0xFF, 0xFF]))
    )

    # Mock parser to raise ParserError
    client = Client(transport=mock_transport, profile=device_profile)
    client.parser.parse_block = Mock(side_effect=ParserError("Invalid field value"))

    policy = RetryPolicy(max_attempts=3, initial_delay=0.01, max_delay=0.05)
    client.retry_policy = policy

    # Should fail immediately without retry
    with pytest.raises(ParserError, match="Invalid field value"):
        client.read_block(100)

    # Verify only 1 attempt (no retries)
    assert mock_transport.send_frame.call_count == 1


def test_read_block_no_retry_on_protocol_error(mock_transport, device_profile):
    """Test read_block does not retry on ProtocolError (fail fast)."""
    from power_sdk.errors import ProtocolError
    from power_sdk.utils.resilience import RetryPolicy

    # Invalid CRC response
    mock_transport.send_frame = Mock(
        return_value=bytes([0x01, 0x03, 0x04, 0x00, 0x64, 0x00, 0xC8, 0xFF, 0xFF])
    )

    policy = RetryPolicy(max_attempts=3, initial_delay=0.01, max_delay=0.05)
    client = Client(
        transport=mock_transport, profile=device_profile, retry_policy=policy
    )

    # Should fail immediately without retry (CRC validation error)
    with pytest.raises(ProtocolError, match="CRC"):
        client.read_block(100)

    # Verify only 1 attempt (no retries)
    assert mock_transport.send_frame.call_count == 1


