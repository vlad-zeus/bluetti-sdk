"""Protocol layer factory."""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import ClassVar

from ..contracts.protocol import ProtocolLayerInterface
from ..errors import ProtocolError

ProtocolBuilder = Callable[[], ProtocolLayerInterface]


class ProtocolFactory:
    """Create protocol layer instances by protocol key."""

    _builders: ClassVar[dict[str, ProtocolBuilder]] = {}
    _lock: ClassVar[threading.Lock] = threading.Lock()

    @classmethod
    def register(cls, protocol: str, builder: ProtocolBuilder) -> None:
        """Register or override a protocol builder."""
        with cls._lock:
            cls._builders[protocol] = builder

    @classmethod
    def create(cls, protocol: str) -> ProtocolLayerInterface:
        """Create a protocol layer instance for the given protocol key."""
        with cls._lock:
            builder = cls._builders.get(protocol)
            available = ", ".join(sorted(cls._builders.keys()))
        if builder is None:
            raise ProtocolError(
                f"Unknown protocol {protocol!r}. Available: {available}"
            )
        return builder()

    @classmethod
    def list_protocols(cls) -> list[str]:
        """List all registered protocol keys."""
        with cls._lock:
            return sorted(cls._builders.keys())

    @classmethod
    def _reset(cls) -> None:
        """Reset factory state (for testing only)."""
        with cls._lock:
            cls._builders = {}
