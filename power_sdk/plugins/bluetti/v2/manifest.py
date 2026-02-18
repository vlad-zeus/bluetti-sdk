"""PluginManifest — declarative descriptor for a vendor+protocol plugin.

Every plugin exposes exactly one PluginManifest instance.
The bootstrap loader reads manifests to build the PluginRegistry.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(frozen=True)
class PluginManifest:
    """Immutable descriptor for a power_sdk plugin.

    Fields
    ------
    vendor : str
        Vendor identifier, e.g. "bluetti". Used as lookup key.
    protocol : str
        Protocol identifier, e.g. "v2". Combined with vendor to form plugin key.
    version : str
        Plugin semantic version, e.g. "1.0.0".
    description : str
        Human-readable description.
    profile_ids : tuple[str, ...]
        Device profile IDs this plugin supports, e.g. ("EL100V2", "EL30V2").
    transport_keys : tuple[str, ...]
        Transport keys this plugin registers, e.g. ("mqtt",).
    schema_pack_version : str
        Version of the schema pack shipped with this plugin.
    capabilities : tuple[str, ...]
        Feature flags, e.g. ("read", "write", "stream").
    parser_factory : Callable[[], Any] | None
        Zero-arg callable that returns a ParserInterface instance.
        Set by the plugin's __init__ at import time.
    protocol_layer_factory : Callable[[], Any] | None
        Zero-arg callable that returns a ProtocolLayerInterface instance.
    profile_loader : Callable[[str], Any] | None
        Zero-arg-with-profile_id callable: profile_loader(profile_id) → DeviceProfile.
    """

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
    """Zero-arg-with-profile_id callable: profile_loader(profile_id) → DeviceProfile."""

    @property
    def key(self) -> str:
        """Canonical plugin key: '<vendor>/<protocol>'."""
        return f"{self.vendor}/{self.protocol}"
