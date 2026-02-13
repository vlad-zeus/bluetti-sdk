"""Layer Contracts and Interfaces

Defines strict contracts between architectural layers:
    transport → protocol → v2_parser → device_model

Each layer has clear responsibilities and does NOT leak into others.
"""

from .transport import TransportProtocol
from .protocol import ProtocolLayerInterface, NormalizedPayload
from .parser import V2ParserInterface
from .device import DeviceModelInterface
from .client import BluettiClientInterface

__all__ = [
    # Transport layer
    "TransportProtocol",

    # Protocol layer
    "ProtocolLayerInterface",
    "NormalizedPayload",

    # Parser layer
    "V2ParserInterface",

    # Device layer
    "DeviceModelInterface",

    # Client layer
    "BluettiClientInterface",
]
