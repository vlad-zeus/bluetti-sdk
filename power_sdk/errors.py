"""Power SDK Error Hierarchy

All errors inherit from SDKError for easy catching.
Each layer has its own error type for precise handling.
"""


class SDKError(Exception):
    """Base error for all Power SDK errors."""


class TransportError(SDKError):
    """Transport layer error (connection, timeout, network issues)."""


class ProtocolError(SDKError):
    """Protocol layer error (CRC, framing, invalid Modbus response)."""


class ParserError(SDKError):
    """Parser layer error (unknown block, validation failure, schema issues)."""


class DeviceError(SDKError):
    """Device layer error (invalid state, unsupported operation)."""
