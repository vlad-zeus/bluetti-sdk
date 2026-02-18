"""Protocol layer factory."""

from __future__ import annotations

from typing import Callable, ClassVar

from ..contracts.protocol import ProtocolLayerInterface
from ..errors import ProtocolError

ProtocolBuilder = Callable[[], ProtocolLayerInterface]


class ProtocolFactory:
    """Create protocol layer instances by protocol key.
    """

    _builders: ClassVar[dict[str, ProtocolBuilder]] = {}

    @classmethod
    def register(cls, protocol: str, builder: ProtocolBuilder) -> None:
        """Register or override a protocol builder."""
        cls._builders[protocol] = builder

    @classmethod
    def create(cls, protocol: str) -> ProtocolLayerInterface:
        """Create a protocol layer instance for the given protocol key."""
        builder = cls._builders.get(protocol)
        if builder is None:
            available = ", ".join(sorted(cls._builders.keys()))
            raise ProtocolError(
                f"Unknown protocol {protocol!r}. Available: {available}"
            )
        return builder()

    @classmethod
    def list_protocols(cls) -> list[str]:
        """List all registered protocol keys."""
        return sorted(cls._builders.keys())

    @classmethod
    def _reset(cls) -> None:
        """Reset factory state (for testing only)."""
        cls._builders = {}
