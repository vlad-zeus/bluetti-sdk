"""Unit tests for protocol layer implementations."""

from unittest.mock import Mock

import pytest
from power_sdk.errors import ProtocolError
from power_sdk.plugins.bluetti.v2.protocol.layer import ModbusProtocolLayer


def _build_test_response(data: bytes, function_code: int = 0x03) -> bytes:
    """Build a valid Modbus response frame with CRC."""
    frame = bytes([0x01, function_code, len(data)]) + data
    crc = 0xFFFF
    for byte in frame:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return frame + bytes([crc & 0xFF, (crc >> 8) & 0xFF])


def test_modbus_protocol_layer_returns_normalized_payload() -> None:
    transport = Mock()
    transport.send_frame = Mock(
        return_value=_build_test_response(bytes([0x00, 0x64, 0x00, 0xC8]))
    )
    layer = ModbusProtocolLayer()

    payload = layer.read_block(
        transport=transport,
        device_address=1,
        block_id=1300,
        register_count=2,
    )

    assert payload.block_id == 1300
    assert payload.data == bytes([0x00, 0x64, 0x00, 0xC8])
    assert payload.device_address == 1
    transport.send_frame.assert_called_once()


def test_modbus_protocol_layer_rejects_bad_crc() -> None:
    transport = Mock()
    # Intentionally bad CRC
    transport.send_frame = Mock(
        return_value=bytes([0x01, 0x03, 0x04, 0x00, 0x64, 0x00, 0xC8, 0xFF, 0xFF])
    )
    layer = ModbusProtocolLayer()

    with pytest.raises(ProtocolError, match="CRC"):
        layer.read_block(
            transport=transport,
            device_address=1,
            block_id=100,
            register_count=2,
        )


def test_modbus_protocol_layer_propagates_modbus_error_response() -> None:
    transport = Mock()
    # Error response: function code 0x83, error code 0x02 (illegal data address)
    transport.send_frame = Mock(
        return_value=_build_test_response(bytes([0x02]), function_code=0x83)
    )
    layer = ModbusProtocolLayer()

    with pytest.raises(ProtocolError):
        layer.read_block(
            transport=transport,
            device_address=1,
            block_id=9999,
            register_count=2,
        )

