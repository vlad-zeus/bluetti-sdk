"""Vendor-neutral plugin manifest contract."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(frozen=True)
class PluginCapabilities:
    """Declared capabilities of a vendor/protocol plugin.

    Defaults are intentionally conservative (write=False).
    Used by the bootstrap layer to gate write operations before a write
    API is added to Client.
    """

    supports_write: bool = False
    """True if this plugin can send commands to the device."""

    supports_streaming: bool = True
    """True if this plugin can stream blocks via stream_group / astream_group."""

    requires_device_validation_for_write: bool = True
    """True if write operations must be preceded by a device identity read."""

    def can_write(self, force: bool = False) -> bool:
        """Return True if write is permitted under current capability settings.

        Args:
            force: If True, skip the device-validation requirement check.
                   Does NOT bypass supports_write=False.
        """
        if not self.supports_write:
            return False
        if force:
            return True
        return not self.requires_device_validation_for_write


@dataclass(frozen=True)
class PluginManifest:
    """Immutable descriptor for a vendor/protocol plugin."""

    vendor: str
    protocol: str
    version: str
    description: str
    profile_ids: tuple[str, ...] = field(default_factory=tuple)
    transport_keys: tuple[str, ...] = field(default_factory=tuple)
    schema_pack_version: str = "0.0.0"
    capabilities: PluginCapabilities = field(default_factory=PluginCapabilities)
    parser_factory: Callable[[], Any] | None = field(
        default=None, compare=False, hash=False
    )
    protocol_layer_factory: Callable[[], Any] | None = field(
        default=None, compare=False, hash=False
    )
    profile_loader: Callable[[str], Any] | None = field(
        default=None, compare=False, hash=False
    )
    schema_loader: Callable[[Any, Any], None] | None = field(
        default=None, compare=False, hash=False
    )

    @property
    def key(self) -> str:
        """Canonical plugin key: '<vendor>/<protocol>'."""
        return f"{self.vendor}/{self.protocol}"

    def can_write(self, force: bool = False) -> bool:
        """Convenience proxy for capabilities.can_write()."""
        return self.capabilities.can_write(force)
