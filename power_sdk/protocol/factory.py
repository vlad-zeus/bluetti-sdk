"""Protocol layer factory and registry.

Provides a central mapping from profile.protocol identifiers to protocol
layer implementations.
"""

from __future__ import annotations

from typing import Callable, ClassVar

from power_sdk.plugins.bluetti.v2.protocol.layer import ModbusProtocolLayer

from ..contracts.protocol import ProtocolLayerInterface
from ..errors import ProtocolError

ProtocolBuilder = Callable[[], ProtocolLayerInterface]


class ProtocolFactory:
    """Create protocol layer instances by protocol key."""

    _builders: ClassVar[dict[str, ProtocolBuilder]] = {
        "v2": ModbusProtocolLayer,
        "modbus_v2": ModbusProtocolLayer,
    }

    @classmethod
    def register(cls, protocol: str, builder: ProtocolBuilder) -> None:
        """Register or override a protocol builder."""
        cls._builders[protocol] = builder

    @classmethod
    def create(cls, protocol: str) -> ProtocolLayerInterface:
        """Create protocol layer for a profile protocol key."""
        builder = cls._builders.get(protocol)
        if builder is None:
            available = ", ".join(sorted(cls._builders.keys()))
            raise ProtocolError(
                f"Unknown protocol '{protocol}'. Available protocols: {available}"
            )
        return builder()

    @classmethod
    def list_protocols(cls) -> list[str]:
        """List registered protocol keys."""
        return sorted(cls._builders.keys())
