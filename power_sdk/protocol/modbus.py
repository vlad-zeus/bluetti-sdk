"""Compatibility shim — power_sdk.protocol.modbus has moved.

ModbusProtocolLayer and modbus utilities now live in:
    power_sdk.plugins.bluetti.v2.protocol.modbus
"""

from power_sdk.plugins.bluetti.v2.protocol.modbus import (  # noqa: F401
    ModbusResponse,
    build_modbus_request,
    normalize_modbus_response,
    parse_modbus_frame,
    validate_crc,
)
