"""Unit tests for Client orchestration layer.

These tests are vendor/plugin-neutral: no imports from power_sdk.plugins.bluetti.*.
All plugin-specific behaviour (V2Parser defaults, SchemaRegistry isolation, etc.)
is tested in tests/unit/plugins/ or conformance suites.
"""

from unittest.mock import Mock

import pytest
from power_sdk.client import Client
from power_sdk.contracts.protocol import NormalizedPayload
from power_sdk.contracts.types import ParsedRecord
from power_sdk.devices.types import BlockGroupDefinition, DeviceProfile
from power_sdk.errors import ParserError, ProtocolError, TransportError
from power_sdk.models.device import Device
from power_sdk.models.types import BlockGroup

# test_profile and mock_parser are provided by tests/conftest.py


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_parsed_block(block_id: int) -> ParsedRecord:
    return ParsedRecord(
        block_id=block_id,
        name=f"BLOCK_{block_id}",
        values={"ok": True},
        raw=b"",
        length=0,
        protocol_version=None,
        schema_version="1.0.0",
        timestamp=0.0,
    )


def _make_mock_transport(return_bytes: bytes = b"\x00\x64") -> Mock:
    transport = Mock()
    transport.connect = Mock()
    transport.disconnect = Mock()
    transport.is_connected = Mock(return_value=True)
    transport.send_frame = Mock(return_value=return_bytes)
    return transport


def _make_mock_protocol(return_data: bytes = b"\x00\x64") -> Mock:
    protocol = Mock()
    protocol.read_block = Mock(
        return_value=NormalizedPayload(
            block_id=100,
            data=return_data,
            device_address=1,
        )
    )
    return protocol


def _mock_parser_with_schema(block_id: int = 100, min_length: int = 4) -> Mock:
    """Return a mock_parser that knows about one block schema."""
    from unittest.mock import MagicMock

    mock_schema = MagicMock()
    mock_schema.min_length = min_length

    parser = Mock()
    parser.get_schema = Mock(return_value=mock_schema)
    parser.list_schemas = Mock(return_value={block_id: f"BLOCK_{block_id}"})
    parser.register_schema = Mock()
    parser.parse_block = Mock(return_value=_make_parsed_block(block_id))
    return parser


# ---------------------------------------------------------------------------
# Construction / DI
# ---------------------------------------------------------------------------


def test_client_creation(test_profile, mock_parser):
    transport = _make_mock_transport()
    client = Client(
        transport=transport, profile=test_profile, parser=mock_parser, device_address=1
    )
    assert client.profile.model == "TEST_DEVICE"
    assert client.device is not None
    assert client.transport is transport
    assert client.parser is mock_parser


def test_client_with_custom_device_address(test_profile, mock_parser):
    client = Client(
        transport=_make_mock_transport(),
        profile=test_profile,
        parser=mock_parser,
        device_address=5,
    )
    assert client.device_address == 5


def test_dependency_injection_custom_protocol(test_profile, mock_parser):
    mock_protocol = Mock()
    client = Client(
        transport=_make_mock_transport(),
        profile=test_profile,
        parser=mock_parser,
        protocol=mock_protocol,
    )
    assert client.protocol is mock_protocol


def test_dependency_injection_custom_device(test_profile, mock_parser):
    mock_device = Mock()
    client = Client(
        transport=_make_mock_transport(),
        profile=test_profile,
        parser=mock_parser,
        device=mock_device,
    )
    assert client.device is mock_device


def test_dependency_injection_both_custom(test_profile):
    mock_parser = Mock()
    mock_parser.get_schema = Mock(return_value=None)
    mock_device = Mock()
    client = Client(
        transport=_make_mock_transport(),
        profile=test_profile,
        parser=mock_parser,
        device=mock_device,
    )
    assert client.parser is mock_parser
    assert client.device is mock_device


def test_unknown_profile_protocol_fails_fast(mock_parser):
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
        Client(
            transport=_make_mock_transport(), profile=unsupported, parser=mock_parser
        )


def test_default_v2device_created_when_not_injected(test_profile, mock_parser):
    client = Client(
        transport=_make_mock_transport(), profile=test_profile, parser=mock_parser
    )
    assert isinstance(client.device, Device)


# ---------------------------------------------------------------------------
# Connect / Disconnect
# ---------------------------------------------------------------------------


def test_client_connect(test_profile, mock_parser):
    transport = _make_mock_transport()
    client = Client(transport=transport, profile=test_profile, parser=mock_parser)
    client.connect()
    transport.connect.assert_called_once()


def test_client_disconnect(test_profile, mock_parser):
    transport = _make_mock_transport()
    client = Client(transport=transport, profile=test_profile, parser=mock_parser)
    client.disconnect()
    transport.disconnect.assert_called_once()


def test_client_manual_connect_disconnect(test_profile, mock_parser):
    transport = _make_mock_transport()
    client = Client(transport=transport, profile=test_profile, parser=mock_parser)
    client.connect()
    client.disconnect()
    transport.connect.assert_called_once()
    transport.disconnect.assert_called_once()


# ---------------------------------------------------------------------------
# Device state
# ---------------------------------------------------------------------------


def test_client_get_device_state(test_profile, mock_parser):
    client = Client(
        transport=_make_mock_transport(), profile=test_profile, parser=mock_parser
    )
    state = client.get_device_state()
    assert "device_id" in state
    assert "model" in state
    assert state["model"] == "TEST_DEVICE"


def test_client_get_group_state(test_profile, mock_parser):
    client = Client(
        transport=_make_mock_transport(), profile=test_profile, parser=mock_parser
    )
    grid_state = client.get_group_state(BlockGroup.GRID)
    assert "frequency" in grid_state
    assert "voltage" in grid_state


# ---------------------------------------------------------------------------
# Group read delegation
# ---------------------------------------------------------------------------


def test_read_group_ex_partial_collects_errors(test_profile, mock_parser):
    client = Client(
        transport=_make_mock_transport(),
        profile=test_profile,
        parser=mock_parser,
    )
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


def test_read_group_ex_fail_fast_raises(test_profile, mock_parser):
    client = Client(
        transport=_make_mock_transport(),
        profile=test_profile,
        parser=mock_parser,
    )
    client._group_reader.read_block = Mock(side_effect=TransportError("boom"))
    with pytest.raises(TransportError, match="boom"):
        client.read_group_ex(BlockGroup.INVERTER, partial_ok=False)


def test_read_group_partial_ok_by_default(test_profile, mock_parser):
    client = Client(
        transport=_make_mock_transport(),
        profile=test_profile,
        parser=mock_parser,
    )
    client._group_reader.read_block = Mock(
        side_effect=[
            _make_parsed_block(1100),
            TransportError("boom"),
            _make_parsed_block(1500),
        ]
    )
    blocks = client.read_group(BlockGroup.INVERTER)
    assert len(blocks) == 2


def test_read_group_fail_fast_explicit(test_profile, mock_parser):
    client = Client(
        transport=_make_mock_transport(),
        profile=test_profile,
        parser=mock_parser,
    )
    client._group_reader.read_block = Mock(
        side_effect=[
            _make_parsed_block(1100),
            TransportError("boom"),
        ]
    )
    with pytest.raises(TransportError, match="boom"):
        client.read_group(BlockGroup.INVERTER, partial_ok=False)


# ---------------------------------------------------------------------------
# register_schema passthrough
# ---------------------------------------------------------------------------


def test_register_schema_delegates_to_parser(test_profile, mock_parser):
    client = Client(
        transport=_make_mock_transport(), profile=test_profile, parser=mock_parser
    )
    fake_schema = Mock()
    fake_schema.block_id = 9999
    fake_schema.name = "FAKE"
    client.register_schema(fake_schema)
    mock_parser.register_schema.assert_called_once_with(fake_schema)


def test_get_registered_schemas_delegates_to_parser(test_profile, mock_parser):
    mock_parser.list_schemas = Mock(return_value={100: "BLOCK_100"})
    client = Client(
        transport=_make_mock_transport(), profile=test_profile, parser=mock_parser
    )
    result = client.get_registered_schemas()
    assert result == {100: "BLOCK_100"}
    mock_parser.list_schemas.assert_called_once()


# ---------------------------------------------------------------------------
# Connect retry
# ---------------------------------------------------------------------------


def test_connect_retries_on_transport_error_then_succeeds(test_profile, mock_parser):
    from power_sdk.utils.resilience import RetryPolicy

    call_count = 0

    def connect_side_effect():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise TransportError("Transient connection error")

    transport = _make_mock_transport()
    transport.connect = Mock(side_effect=connect_side_effect)
    transport.is_connected = Mock(return_value=True)

    policy = RetryPolicy(max_attempts=3, initial_delay=0.01, max_delay=0.05)
    client = Client(
        transport=transport,
        profile=test_profile,
        parser=mock_parser,
        retry_policy=policy,
    )
    client.connect()
    assert call_count == 3
    assert transport.connect.call_count == 3


def test_connect_exhausts_retries_and_raises(test_profile, mock_parser):
    from power_sdk.utils.resilience import RetryPolicy

    transport = _make_mock_transport()
    transport.connect = Mock(side_effect=TransportError("Persistent connection error"))

    policy = RetryPolicy(max_attempts=2, initial_delay=0.01, max_delay=0.05)
    client = Client(
        transport=transport,
        profile=test_profile,
        parser=mock_parser,
        retry_policy=policy,
    )
    with pytest.raises(TransportError, match="Persistent connection error"):
        client.connect()
    assert transport.connect.call_count == 2


# ---------------------------------------------------------------------------
# read_block retry — protocol-level mocking (no plugin dependency)
# ---------------------------------------------------------------------------


def test_read_block_retries_on_transport_error_then_succeeds(
    test_profile,
):
    """read_block retries when protocol layer raises TransportError."""
    from power_sdk.utils.resilience import RetryPolicy

    parser = _mock_parser_with_schema(block_id=100)

    call_count = 0

    def protocol_side_effect(transport, device_address, block_id, register_count):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise TransportError("Transient send error")
        return NormalizedPayload(
            block_id=block_id, data=b"\x00\x64\x00\xC8", device_address=device_address
        )

    mock_protocol = Mock()
    mock_protocol.read_block = Mock(side_effect=protocol_side_effect)

    policy = RetryPolicy(max_attempts=3, initial_delay=0.01, max_delay=0.05)
    client = Client(
        transport=_make_mock_transport(),
        profile=test_profile,
        parser=parser,
        protocol=mock_protocol,
        retry_policy=policy,
    )
    result = client.read_block(100)
    assert result is not None
    assert call_count == 3


def test_read_block_exhausts_retries_and_raises(test_profile):
    from power_sdk.utils.resilience import RetryPolicy

    parser = _mock_parser_with_schema(block_id=100)

    mock_protocol = Mock()
    mock_protocol.read_block = Mock(
        side_effect=TransportError("Persistent send error")
    )

    policy = RetryPolicy(max_attempts=2, initial_delay=0.01, max_delay=0.05)
    client = Client(
        transport=_make_mock_transport(),
        profile=test_profile,
        parser=parser,
        protocol=mock_protocol,
        retry_policy=policy,
    )
    with pytest.raises(TransportError, match="Persistent send error"):
        client.read_block(100)
    assert mock_protocol.read_block.call_count == 2


def test_read_block_no_retry_on_parser_error(test_profile):
    """ParserError must not trigger retry (fail fast)."""
    from power_sdk.utils.resilience import RetryPolicy

    parser = _mock_parser_with_schema(block_id=100)
    parser.parse_block = Mock(side_effect=ParserError("Invalid field value"))

    mock_protocol = _make_mock_protocol()

    policy = RetryPolicy(max_attempts=3, initial_delay=0.01, max_delay=0.05)
    client = Client(
        transport=_make_mock_transport(),
        profile=test_profile,
        parser=parser,
        protocol=mock_protocol,
        retry_policy=policy,
    )
    with pytest.raises(ParserError):
        client.read_block(100)
    assert mock_protocol.read_block.call_count == 1


def test_read_block_no_retry_on_protocol_error(test_profile):
    """ProtocolError must not trigger retry (fail fast)."""
    from power_sdk.utils.resilience import RetryPolicy

    parser = _mock_parser_with_schema(block_id=100)

    mock_protocol = Mock()
    mock_protocol.read_block = Mock(side_effect=ProtocolError("CRC mismatch"))

    policy = RetryPolicy(max_attempts=3, initial_delay=0.01, max_delay=0.05)
    client = Client(
        transport=_make_mock_transport(),
        profile=test_profile,
        parser=parser,
        protocol=mock_protocol,
        retry_policy=policy,
    )
    with pytest.raises(ProtocolError, match="CRC"):
        client.read_block(100)
    assert mock_protocol.read_block.call_count == 1
