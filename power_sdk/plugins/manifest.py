"""Vendor-neutral plugin manifest contract."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


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
    capabilities: tuple[str, ...] = field(default=("read",))
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

