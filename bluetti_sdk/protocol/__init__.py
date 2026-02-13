"""Protocol layer - Modbus and V2 protocol implementations.

This module contains:
- Modbus RTU normalization and framing
- V2 protocol parser with schema-based field extraction
"""

from .modbus import (
    ModbusResponse,
    normalize_modbus_response,
    parse_modbus_frame,
    build_modbus_request,
    validate_crc,
)

__all__ = [
    "ModbusResponse",
    "normalize_modbus_response",
    "parse_modbus_frame",
    "build_modbus_request",
    "validate_crc",
]
