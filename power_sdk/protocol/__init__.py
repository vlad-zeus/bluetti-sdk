"""Protocol layer - core factory.

After Step 2c migration, Bluetti-specific protocol implementations
(ModbusProtocolLayer, V2Parser, etc.) live in:
    power_sdk.plugins.bluetti.v2.protocol

This package now only contains the plugin-agnostic factory.
"""

from .factory import ProtocolFactory

__all__ = [
    "ProtocolFactory",
]
