"""Protocol layer factory — discovers from PluginRegistry."""

from __future__ import annotations

from typing import Callable, ClassVar

from ..contracts.protocol import ProtocolLayerInterface
from ..errors import ProtocolError

ProtocolBuilder = Callable[[], ProtocolLayerInterface]


class ProtocolFactory:
    """Create protocol layer instances by protocol key.

    On first use, bootstraps its registry from load_plugins().
    Additional builders can be registered via register() for tests or extensions.
    """

    _builders: ClassVar[dict[str, ProtocolBuilder]] = {}
    _bootstrapped: ClassVar[bool] = False

    @classmethod
    def _bootstrap(cls) -> None:
        if cls._bootstrapped:
            return
        from power_sdk.plugins.registry import load_plugins

        registry = load_plugins()
        for key in registry:
            vendor, protocol = key.split("/", 1)
            manifest = registry.get(vendor, protocol)
            if manifest and manifest.protocol_layer_factory:
                # setdefault: explicit register() calls take priority over bootstrap
                cls._builders.setdefault(protocol, manifest.protocol_layer_factory)
        cls._bootstrapped = True

    @classmethod
    def register(cls, protocol: str, builder: ProtocolBuilder) -> None:
        """Register or override a protocol builder."""
        cls._builders[protocol] = builder

    @classmethod
    def create(cls, protocol: str) -> ProtocolLayerInterface:
        """Create a protocol layer instance for the given protocol key."""
        cls._bootstrap()
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
        cls._bootstrap()
        return sorted(cls._builders.keys())

    @classmethod
    def _reset(cls) -> None:
        """Reset factory state (for testing only)."""
        cls._builders = {}
        cls._bootstrapped = False
