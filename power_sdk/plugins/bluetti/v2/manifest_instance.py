"""Bluetti V2 plugin manifest instance.

Imported by the bootstrap loader to register this plugin.
"""

from __future__ import annotations

from .manifest import PluginManifest

BLUETTI_V2_MANIFEST = PluginManifest(
    vendor="bluetti",
    protocol="v2",
    version="1.0.0",
    description="Bluetti V2 block-addressed protocol over MQTT/Modbus",
    profile_ids=("EL100V2", "EL30V2", "ELITE200V2"),
    transport_keys=("mqtt",),
    schema_pack_version="1.0.0",
    capabilities=("read",),
    # parser_factory and protocol_layer_factory wired after code migration in Step 2c
    parser_factory=None,
    protocol_layer_factory=None,
)
