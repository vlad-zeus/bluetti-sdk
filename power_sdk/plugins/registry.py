"""Plugin registry — static phase (Phase 1).

Phase 1: Known manifests registered at module import time.
Phase 2 (future): Discovery via importlib.metadata entry_points.
"""

from __future__ import annotations

from typing import Iterator

from .bluetti.v2.manifest import PluginManifest


class PluginRegistry:
    """Registry of PluginManifest instances keyed by '<vendor>/<protocol>'."""

    def __init__(self) -> None:
        self._manifests: dict[str, PluginManifest] = {}

    def register(self, manifest: PluginManifest) -> None:
        """Register a manifest. Raises ValueError if key already registered."""
        if manifest.key in self._manifests:
            raise ValueError(f"Plugin already registered: {manifest.key!r}")
        self._manifests[manifest.key] = manifest

    def get(self, vendor: str, protocol: str) -> PluginManifest | None:
        """Return manifest for vendor+protocol, or None."""
        return self._manifests.get(f"{vendor}/{protocol}")

    def keys(self) -> list[str]:
        """Return all registered plugin keys."""
        return list(self._manifests.keys())

    def __iter__(self) -> Iterator[str]:
        """Iterate over registered plugin keys."""
        return iter(self._manifests)

    def __len__(self) -> int:
        return len(self._manifests)


def load_plugins() -> PluginRegistry:
    """Build and return the static plugin registry.

    Static Phase 1: manifests are explicitly listed here.
    To add a new plugin, import its manifest and call registry.register().
    """
    from .bluetti.v2.manifest_instance import BLUETTI_V2_MANIFEST

    registry = PluginRegistry()
    registry.register(BLUETTI_V2_MANIFEST)
    return registry
