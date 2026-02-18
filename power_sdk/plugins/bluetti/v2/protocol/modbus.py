"""Protocol Layer - Modbus RTU Normalization

Responsibilities:
- Convert Modbus responses to normalized byte buffers
- Handle Modbus framing (function code, byte count)
- CRC validation (if needed)
- Endianness conversion

Does NOT know about:
- Block schemas
- Field parsing
- Transform pipelines
- Device models
"""

import logging
import struct
from dataclasses import dataclass
from typing import Optional, cast

from power_sdk.errors import ProtocolError

logger = logging.getLogger(__name__)


@dataclass
class ModbusResponse:
    """Raw Modbus response before normalization."""

    device_address: int
    function_code: int
    byte_count: int
    data: bytes
    crc: Optional[int] = None


def normalize_modbus_response(response: ModbusResponse) -> bytes:
    """Convert Modbus response to normalized byte buffer.

    Input: Raw Modbus response with framing
    Output: Clean big-endian byte buffer ready for parser

    Responsibilities:
    - Remove function code byte
    - Remove byte count
    - Keep only register data
    - Ensure big-endian byte order

    Args:
        response: ModbusResponse with framing

    Returns:
        Normalized byte buffer (big-endian, no framing)

    Raises:
        ProtocolError: If response is invalid

    Example:
        Raw Modbus response: 01 03 06 00 55 02 08 0C AD CRC
                             ^  ^  ^  [---- data ----]
                             |  |  |
                             |  |  byte_count
                             |  function_code
                             device_address

        Normalized: 00 55 02 08 0C AD (6 bytes, big-endian)
    """
    # Check for error response (function code has high bit set)
    if response.function_code & 0x80:
        if len(response.data) == 0:
            raise ProtocolError("Malformed Modbus error response: missing error code")

        error_code = response.data[0]
        error_names = {
            0x01: "Illegal function",
            0x02: "Illegal data address",
            0x03: "Illegal data value",
            0x04: "Slave device failure",
        }
        error_name = error_names.get(error_code, f"Unknown error {error_code}")
        raise ProtocolError(f"Modbus error response: {error_name} (code {error_code})")

    # Validate function code (0x03 = Read Holding Registers)
    if response.function_code != 0x03:
        raise ProtocolError(
            f"Unsupported function code: 0x{response.function_code:02X} "
            f"(expected 0x03 for Read Holding Registers)"
        )

    # Validate byte count
    if response.byte_count != len(response.data):
        raise ProtocolError(
            f"Byte count mismatch: header says {response.byte_count}, "
            f"but got {len(response.data)} bytes"
        )

    # Data is already big-endian from Modbus
    # Just return clean payload
    return response.data


def parse_modbus_frame(frame: bytes) -> ModbusResponse:
    """Parse raw Modbus frame into ModbusResponse.

    Args:
        frame: Raw Modbus RTU frame with framing

    Returns:
        ModbusResponse object

    Raises:
        ProtocolError: If frame is invalid

    Frame format:
        [device_addr][func_code][byte_count][data...][crc_low][crc_high]
         1 byte       1 byte     1 byte      N bytes  2 bytes
    """
    if len(frame) < 5:
        raise ProtocolError(f"Frame too short: {len(frame)} bytes")

    device_address = frame[0]
    function_code = frame[1]
    byte_count = frame[2]

    # Extract data (between byte_count and CRC)
    data_start = 3
    data_end = 3 + byte_count

    if len(frame) < data_end + 2:
        raise ProtocolError(
            f"Frame truncated: expected {data_end + 2} bytes, got {len(frame)}"
        )

    data = frame[data_start:data_end]

    # Extract CRC (optional - for validation)
    crc_bytes = frame[data_end : data_end + 2]
    crc = struct.unpack("<H", crc_bytes)[0] if len(crc_bytes) == 2 else None

    return ModbusResponse(
        device_address=device_address,
        function_code=function_code,
        byte_count=byte_count,
        data=data,
        crc=crc,
    )


def build_modbus_request(
    device_address: int, block_address: int, register_count: int
) -> bytes:
    """Build Modbus Read Holding Registers request.

    Args:
        device_address: Modbus device address (usually 1)
        block_address: Starting register address
        register_count: Number of registers to read

    Returns:
        Complete Modbus RTU frame with CRC

    Format:
        [device_addr][func_code=0x03][start_addr_hi][start_addr_lo][count_hi][count_lo][crc_lo][crc_hi]
    """
    # Build frame without CRC
    frame = bytearray()
    frame.append(device_address)
    frame.append(0x03)  # Read Holding Registers
    frame.extend(struct.pack(">H", block_address))  # Big-endian address
    frame.extend(struct.pack(">H", register_count))  # Big-endian count

    # Calculate CRC16-Modbus
    crc = _calculate_crc16_modbus(frame)
    frame.extend(struct.pack("<H", crc))  # Little-endian CRC

    return bytes(frame)


def _calculate_crc16_modbus(data: bytes) -> int:
    """Calculate CRC16-Modbus (little-endian polynomial).

    Args:
        data: Data to calculate CRC for

    Returns:
        CRC16 value
    """
    crc = 0xFFFF

    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1

    return crc


def validate_crc(frame: bytes) -> bool:
    """Validate Modbus CRC.

    Args:
        frame: Complete Modbus frame with CRC

    Returns:
        True if CRC is valid
    """
    if len(frame) < 4:
        return False

    # Extract CRC from frame
    received_crc = cast(int, struct.unpack("<H", frame[-2:])[0])

    # Calculate CRC of frame without CRC bytes
    calculated_crc = _calculate_crc16_modbus(frame[:-2])

    return received_crc == calculated_crc
