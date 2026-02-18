"""Protocol layer — vendor-neutral factory.

The factory resolves protocol keys (e.g. "v2") to ProtocolLayerInterface
implementations registered by plugins.  Plugin-specific implementations
(e.g. ModbusProtocolLayer) live in their respective plugin packages.
"""

from .factory import ProtocolFactory

__all__ = [
    "ProtocolFactory",
]
