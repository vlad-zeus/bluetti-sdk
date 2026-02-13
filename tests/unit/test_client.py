"""Unit tests for V2Client orchestration layer."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from bluetti_sdk.client import V2Client
from bluetti_sdk.models.profiles import get_device_profile
from bluetti_sdk.protocol.v2.schema import BlockSchema, Field
from bluetti_sdk.protocol.v2.datatypes import UInt16
from bluetti_sdk.protocol.v2.types import ParsedBlock
from bluetti_sdk.models.types import BlockGroup
from bluetti_sdk.errors import TransportError, ProtocolError


@pytest.fixture
def mock_transport():
    """Create mock transport."""
    transport = Mock()
    transport.connect = Mock()
    transport.disconnect = Mock()
    transport.is_connected = Mock(return_value=True)
    transport.send_frame = Mock(return_value=bytes([
        0x01, 0x03, 0x04,  # Header
        0x00, 0x64,  # Data: 100
        0x00, 0xC8,  # Data: 200
        0x00, 0x00  # CRC placeholder
    ]))
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
        ]
    )
    return schema


def test_client_creation(mock_transport, device_profile):
    """Test V2Client creation."""
    client = V2Client(
        transport=mock_transport,
        profile=device_profile,
        device_address=1
    )

    assert client.profile.model == "EL100V2"
    assert client.device is not None
    assert client.transport is mock_transport


def test_client_with_custom_device_address(mock_transport, device_profile):
    """Test V2Client with custom device address."""
    client = V2Client(
        transport=mock_transport,
        profile=device_profile,
        device_address=5
    )

    assert client.device_address == 5


def test_client_connect(mock_transport, device_profile):
    """Test client connect."""
    client = V2Client(
        transport=mock_transport,
        profile=device_profile
    )

    client.connect()

    mock_transport.connect.assert_called_once()


def test_client_disconnect(mock_transport, device_profile):
    """Test client disconnect."""
    client = V2Client(
        transport=mock_transport,
        profile=device_profile
    )

    client.disconnect()

    mock_transport.disconnect.assert_called_once()


def test_client_auto_registers_schemas(mock_transport, device_profile):
    """Test that schemas are auto-registered from SchemaRegistry."""
    client = V2Client(
        transport=mock_transport,
        profile=device_profile
    )

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
    client = V2Client(
        transport=mock_transport,
        profile=device_profile
    )

    state = client.get_device_state()

    assert "device_id" in state
    assert "model" in state
    assert state["model"] == "EL100V2"


def test_client_get_group_state(mock_transport, device_profile):
    """Test getting group state."""
    client = V2Client(
        transport=mock_transport,
        profile=device_profile
    )

    grid_state = client.get_group_state(BlockGroup.GRID)

    assert "frequency" in grid_state
    assert "voltage" in grid_state


def test_client_manual_connect_disconnect(mock_transport, device_profile):
    """Test manual connect and disconnect."""
    client = V2Client(
        transport=mock_transport,
        profile=device_profile
    )

    client.connect()
    client.disconnect()

    # Should connect and disconnect
    mock_transport.connect.assert_called_once()
    mock_transport.disconnect.assert_called_once()


def _make_parsed_block(block_id: int) -> ParsedBlock:
    return ParsedBlock(
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
    """read_group_ex should return both parsed blocks and errors when partial_ok=True."""
    client = V2Client(transport=mock_transport, profile=device_profile)
    client.read_block = Mock(side_effect=[
        _make_parsed_block(1100),
        TransportError("boom"),
        _make_parsed_block(1500),
    ])

    result = client.read_group_ex(BlockGroup.INVERTER, partial_ok=True)

    assert len(result.blocks) == 2
    assert len(result.errors) == 1
    assert result.success is False
    assert result.partial is True
    assert result.errors[0][0] == 1400


def test_read_group_ex_fail_fast_raises(mock_transport, device_profile):
    """read_group_ex should fail fast when partial_ok=False."""
    client = V2Client(transport=mock_transport, profile=device_profile)
    client.read_block = Mock(side_effect=TransportError("boom"))

    with pytest.raises(TransportError, match="boom"):
        client.read_group_ex(BlockGroup.INVERTER, partial_ok=False)


def test_read_group_partial_ok_by_default(mock_transport, device_profile):
    """read_group should return partial results by default (partial_ok=True)."""
    client = V2Client(transport=mock_transport, profile=device_profile)
    client.read_block = Mock(side_effect=[
        _make_parsed_block(1100),
        TransportError("boom"),
        _make_parsed_block(1500),
    ])

    # With default partial_ok=True, should return partial results
    blocks = client.read_group(BlockGroup.INVERTER)
    assert len(blocks) == 2  # Got 2 out of 3 blocks


def test_read_group_fail_fast_explicit(mock_transport, device_profile):
    """read_group should fail fast when partial_ok=False."""
    client = V2Client(transport=mock_transport, profile=device_profile)
    client.read_block = Mock(side_effect=[
        _make_parsed_block(1100),
        TransportError("boom"),
        _make_parsed_block(1500),
    ])

    with pytest.raises(TransportError, match="boom"):
        client.read_group(BlockGroup.INVERTER, partial_ok=False)
