"""Bluetti V2 plugin manifest instance.

Imported by the bootstrap loader to register this plugin.
"""

from __future__ import annotations

from typing import Any

from power_sdk.plugins.manifest import PluginCapabilities, PluginManifest

from .profiles.registry import get_device_profile
from .protocol.layer import ModbusProtocolLayer
from .protocol.parser import V2Parser


def _load_schemas_for_profile(profile: Any, parser: Any) -> None:
    """Register all block schemas needed for *profile* into *parser*."""
    from .schemas import new_registry_with_builtins

    block_ids: set[int] = set()
    for group in profile.groups.values():
        block_ids.update(group.blocks)

    registry = new_registry_with_builtins()
    resolved = registry.resolve_blocks(list(block_ids), strict=False)
    for schema in resolved.values():
        parser.register_schema(schema)


BLUETTI_V2_MANIFEST = PluginManifest(
    vendor="bluetti",
    protocol="v2",
    version="1.0.0",
    description="Bluetti V2 block-addressed protocol over MQTT/Modbus",
    profile_ids=("EL100V2", "EL30V2", "ELITE200V2"),
    transport_keys=("mqtt",),
    schema_pack_version="1.0.0",
    capabilities=PluginCapabilities(
        supports_write=False,  # Write API not yet implemented
        supports_streaming=True,  # stream_group / astream_group supported
        requires_device_validation_for_write=True,
    ),
    parser_factory=V2Parser,
    protocol_layer_factory=ModbusProtocolLayer,
    profile_loader=get_device_profile,
    schema_loader=_load_schemas_for_profile,
)
