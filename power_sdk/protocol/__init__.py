"""Protocol layer - Modbus and V2 protocol implementations.

This module contains:
- Protocol factory and registry
- Modbus RTU normalization and framing
- Protocol layer implementations
- V2 protocol parser with schema-based field extraction
"""

from .factory import ProtocolFactory
from .layer import ModbusProtocolLayer
from .modbus import (
    ModbusResponse,
    build_modbus_request,
    normalize_modbus_response,
    parse_modbus_frame,
    validate_crc,
)

__all__ = [
    "ModbusProtocolLayer",
    "ModbusResponse",
    "ProtocolFactory",
    "build_modbus_request",
    "normalize_modbus_response",
    "parse_modbus_frame",
    "validate_crc",
]
