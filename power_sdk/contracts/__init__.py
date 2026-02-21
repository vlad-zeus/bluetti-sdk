"""Layer Contracts and Interfaces

Defines strict contracts between architectural layers:
    transport → protocol → parser → device_model

Each layer has clear responsibilities and does NOT leak into others.
"""

from .client import ClientInterface
from .device import DeviceModelInterface
from .parser import ParserInterface
from .protocol import NormalizedPayload, ProtocolLayerInterface
from .schema import SchemaProtocol
from .transport import TransportProtocol
from .types import ParsedRecord

__all__ = [
    "ClientInterface",
    "DeviceModelInterface",
    "NormalizedPayload",
    "ParsedRecord",
    "ParserInterface",
    "ProtocolLayerInterface",
    "SchemaProtocol",
    "TransportProtocol",
]
