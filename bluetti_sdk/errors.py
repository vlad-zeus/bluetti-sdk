"""Bluetti SDK Error Hierarchy

All errors inherit from BluettiError for easy catching.
Each layer has its own error type for precise handling.
"""


class BluettiError(Exception):
    """Base error for all Bluetti SDK errors."""
    pass


class TransportError(BluettiError):
    """Transport layer error (connection, timeout, network issues)."""
    pass


class ProtocolError(BluettiError):
    """Protocol layer error (CRC, framing, invalid Modbus response)."""
    pass


class ParserError(BluettiError):
    """Parser layer error (unknown block, validation failure, schema issues)."""
    pass


class DeviceError(BluettiError):
    """Device layer error (invalid state, unsupported operation)."""
    pass
