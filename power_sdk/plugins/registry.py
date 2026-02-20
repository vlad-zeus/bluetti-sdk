"""Plugin registry discovery for runtime plugin loading.

Plugins register themselves by declaring an entry point in pyproject.toml:
    [project.entry-points."power_sdk.plugins"]
    "vendor/protocol" = "my_package.manifest:MY_MANIFEST"

Discovery order:
1) Installed entry points (production path)
2) Local package scan for ``power_sdk.plugins.*.*.manifest_instance`` (dev path)

No vendor-specific fallback is used.
"""

from __future__ import annotations

import importlib
import inspect
import logging
import pkgutil
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


def _discover_from_entry_points() -> list[PluginManifest]:
    """Return manifests discovered from installed package entry points."""
    manifests: list[PluginManifest] = []
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
                if isinstance(manifest, PluginManifest):
                    manifests.append(manifest)
                else:
                    logger.warning(
                        "Plugin entry point %r did not return PluginManifest", ep.name
                    )
            except Exception as exc:
                logger.warning("Plugin %r failed to load: %s", ep.name, exc)
    except ImportError:
        logger.warning(
            "importlib.metadata unavailable; no plugins loaded via entry_points"
        )
    return manifests


def _discover_from_local_package() -> list[PluginManifest]:
    """Return manifests from local source tree plugin modules.

    This supports source-tree execution (e.g. ``python -m power_sdk``) where
    entry points may be unavailable until package installation.
    """
    manifests: list[PluginManifest] = []
    try:
        import power_sdk.plugins as plugins_pkg

        for module_info in pkgutil.walk_packages(
            plugins_pkg.__path__, prefix=f"{plugins_pkg.__name__}."
        ):
            modname = module_info.name
            if not modname.endswith(".manifest_instance"):
                continue
            try:
                module = importlib.import_module(modname)
            except Exception as exc:
                logger.warning("Failed to import plugin module %r: %s", modname, exc)
                continue

            for _, value in inspect.getmembers(module):
                if isinstance(value, PluginManifest):
                    manifests.append(value)
    except Exception as exc:
        logger.warning("Local plugin scan failed: %s", exc)
    return manifests


def load_plugins() -> PluginRegistry:
    """Discover plugins from entry points and local source modules."""
    registry = PluginRegistry()
    for manifest in [*_discover_from_entry_points(), *_discover_from_local_package()]:
        try:
            registry.register(manifest)
        except ValueError:
            # Duplicate key across discovery sources is expected in editable installs.
            logger.debug("Duplicate plugin key ignored: %s", manifest.key)
    return registry
