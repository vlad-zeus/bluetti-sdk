"""Plugin registry — discovery via importlib.metadata entry_points.

Plugins register themselves by declaring an entry point in pyproject.toml:
    [project.entry-points."power_sdk.plugins"]
    "vendor/protocol" = "my_package.manifest:MY_MANIFEST"

load_plugins() returns an empty registry if no plugins are installed.
Static imports of specific vendor manifests are intentionally absent here.
"""

from __future__ import annotations

import logging
from typing import Iterator

from .manifest import PluginManifest

logger = logging.getLogger(__name__)


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
    """Discover plugins via importlib.metadata entry_points(group='power_sdk.plugins').

    Returns an empty PluginRegistry if no plugins are installed.
    A broken entry point is logged as a warning and skipped.

    Third-party plugins register by adding to pyproject.toml:
        [project.entry-points."power_sdk.plugins"]
        "acme/v1" = "acme_power.manifest:ACME_V1_MANIFEST"
    """
    registry = PluginRegistry()

    try:
        from importlib.metadata import entry_points

        # Compatible with Python 3.9-3.11 (dict-like) and 3.12+ (SelectableGroups)
        eps = entry_points()
        if hasattr(eps, "select"):
            plugins = eps.select(group="power_sdk.plugins")
        else:
            plugins = eps.get("power_sdk.plugins", [])  # type: ignore[arg-type]

        for ep in plugins:
            try:
                manifest = ep.load()
                registry.register(manifest)
                logger.debug("Plugin loaded via entry_point: %s", ep.name)
            except Exception as exc:
                logger.warning("Plugin %r failed to load: %s", ep.name, exc)
    except ImportError:
        logger.warning(
            "importlib.metadata unavailable; no plugins loaded via entry_points"
        )

    return registry
