"""Layer Contracts and Interfaces

Defines strict contracts between architectural layers:
    transport → protocol → v2_parser → device_model

Each layer has clear responsibilities and does NOT leak into others.
"""

from .client import BluettiClientInterface
from .device import DeviceModelInterface
from .parser import V2ParserInterface
from .protocol import NormalizedPayload, ProtocolLayerInterface
from .transport import TransportProtocol

__all__ = [
    "BluettiClientInterface",
    "DeviceModelInterface",
    "NormalizedPayload",
    "ProtocolLayerInterface",
    "TransportProtocol",
    "V2ParserInterface",
]
