"""Unit tests for Modbus protocol layer."""

import pytest
from power_sdk.errors import ProtocolError
from power_sdk.protocol.modbus import (
    ModbusResponse,
    build_modbus_request,
    normalize_modbus_response,
    parse_modbus_frame,
    validate_crc,
)


def test_build_modbus_request():
    """Test building Modbus request."""
    # Read 10 registers starting from address 1300
    request = build_modbus_request(
        device_address=1, block_address=1300, register_count=10
    )

    # Check frame structure
    assert len(request) == 8  # 1 addr + 1 func + 2 start + 2 count + 2 crc
    assert request[0] == 0x01  # Device address
    assert request[1] == 0x03  # Function code (Read Holding Registers)

    # Check address (big-endian)
    assert (request[2] << 8 | request[3]) == 1300

    # Check count (big-endian)
    assert (request[4] << 8 | request[5]) == 10

    # CRC should be valid
    assert validate_crc(request)


def test_validate_crc():
    """Test CRC validation."""
    # Valid frame
    frame = build_modbus_request(1, 100, 5)
    assert validate_crc(frame) is True

    # Corrupt frame (flip one bit)
    corrupt = bytearray(frame)
    corrupt[0] ^= 0x01
    assert validate_crc(bytes(corrupt)) is False

    # Too short
    assert validate_crc(b"\x01\x03") is False


def test_parse_modbus_frame():
    """Test parsing Modbus frame."""
    # Build a valid response frame
    # [addr=01][func=03][count=06][data: 00 55 02 08 0C AD][crc]
    frame = bytes(
        [
            0x01,  # Device address
            0x03,  # Function code
            0x06,  # Byte count
            0x00,
            0x55,
            0x02,
            0x08,
            0x0C,
            0xAD,  # 6 bytes data
            0x00,
            0x00,  # Placeholder CRC (will be invalid but structure is correct)
        ]
    )

    response = parse_modbus_frame(frame)

    assert response.device_address == 0x01
    assert response.function_code == 0x03
    assert response.byte_count == 0x06
    assert response.data == bytes([0x00, 0x55, 0x02, 0x08, 0x0C, 0xAD])
    assert response.crc is not None


def test_parse_modbus_frame_too_short():
    """Test parsing frame that's too short."""
    with pytest.raises(ProtocolError, match="Frame too short"):
        parse_modbus_frame(b"\x01\x03")


def test_parse_modbus_frame_truncated():
    """Test parsing truncated frame."""
    # Frame says byte_count=10 but only has 2 bytes of data
    frame = bytes([0x01, 0x03, 0x0A, 0x00, 0x01])

    with pytest.raises(ProtocolError, match="Frame truncated"):
        parse_modbus_frame(frame)


def test_normalize_modbus_response():
    """Test normalizing Modbus response."""
    response = ModbusResponse(
        device_address=0x01,
        function_code=0x03,
        byte_count=6,
        data=bytes([0x00, 0x55, 0x02, 0x08, 0x0C, 0xAD]),
        crc=0xABCD,
    )

    normalized = normalize_modbus_response(response)

    # Should return clean data (no framing)
    assert normalized == bytes([0x00, 0x55, 0x02, 0x08, 0x0C, 0xAD])


def test_normalize_modbus_response_wrong_function_code():
    """Test normalizing with wrong function code."""
    response = ModbusResponse(
        device_address=0x01,
        function_code=0x04,  # Wrong (should be 0x03)
        byte_count=6,
        data=bytes([0x00, 0x55, 0x02, 0x08, 0x0C, 0xAD]),
    )

    with pytest.raises(ProtocolError, match="Unsupported function code"):
        normalize_modbus_response(response)


def test_normalize_modbus_response_byte_count_mismatch():
    """Test normalizing with byte count mismatch."""
    response = ModbusResponse(
        device_address=0x01,
        function_code=0x03,
        byte_count=10,  # Says 10 bytes
        data=bytes([0x00, 0x55, 0x02]),  # But only 3 bytes
    )

    with pytest.raises(ProtocolError, match="Byte count mismatch"):
        normalize_modbus_response(response)


def test_modbus_error_response():
    """Test handling Modbus error response (0x83)."""
    response = ModbusResponse(
        device_address=0x01,
        function_code=0x83,  # Error bit set (0x03 | 0x80)
        byte_count=1,
        data=bytes([0x02]),  # Error code: Illegal data address
    )

    with pytest.raises(ProtocolError, match="Illegal data address"):
        normalize_modbus_response(response)


def test_modbus_error_response_no_error_code():
    """Test error response with missing error code."""
    response = ModbusResponse(
        device_address=0x01,
        function_code=0x83,
        byte_count=0,
        data=bytes([]),  # No error code!
    )

    with pytest.raises(ProtocolError, match="missing error code"):
        normalize_modbus_response(response)


def test_modbus_error_codes():
    """Test all standard Modbus error codes."""
    error_codes = {
        0x01: "Illegal function",
        0x02: "Illegal data address",
        0x03: "Illegal data value",
        0x04: "Slave device failure",
    }

    for code, expected_msg in error_codes.items():
        response = ModbusResponse(
            device_address=0x01, function_code=0x83, byte_count=1, data=bytes([code])
        )

        with pytest.raises(ProtocolError, match=expected_msg):
            normalize_modbus_response(response)


def test_modbus_unknown_error_code():
    """Test unknown error code."""
    response = ModbusResponse(
        device_address=0x01,
        function_code=0x83,
        byte_count=1,
        data=bytes([0xFF]),  # Unknown error code
    )

    with pytest.raises(ProtocolError, match="Unknown error 255"):
        normalize_modbus_response(response)


def test_crc_calculation():
    """Test CRC calculation is consistent."""
    # Build two identical requests
    req1 = build_modbus_request(1, 1300, 16)
    req2 = build_modbus_request(1, 1300, 16)

    # Should be identical (including CRC)
    assert req1 == req2

    # CRC should be valid
    assert validate_crc(req1)
    assert validate_crc(req2)


def test_different_addresses_different_crc():
    """Test different data produces different CRC."""
    req1 = build_modbus_request(1, 1300, 16)
    req2 = build_modbus_request(1, 1301, 16)  # Different address

    # Should be different
    assert req1 != req2

    # Both should have valid CRC
    assert validate_crc(req1)
    assert validate_crc(req2)

