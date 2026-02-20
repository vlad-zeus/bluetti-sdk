"""Bluetti V2 plugin manifest instance.

Imported by the bootstrap loader to register this plugin.
"""

from __future__ import annotations

from typing import Any

from power_sdk.models.types import BlockGroup
from power_sdk.plugins.manifest import PluginCapabilities, PluginManifest

from .profiles.registry import get_device_profile
from .protocol.layer import ModbusProtocolLayer
from .protocol.parser import V2Parser


def _register_block_handlers(device: Any, profile: Any) -> None:
    """Register Bluetti V2 block→state handlers on *device*.

    Maps block IDs to the corresponding Device update methods:
    - 100  → CORE  (dashboard)
    - 1300 → GRID  (grid monitoring)
    - 6000 → BATTERY (battery pack summary)
    - 1100, 1400, 1500 → INVERTER (inverter base/output/AC info)
    - 6100 → CELLS  (battery pack cell details)

    Called by ``build_client_from_entry`` after Client construction so that
    ``Device`` itself stays vendor-neutral (no hardcoded block IDs in core).
    """

    def _on_home(parsed: Any) -> None:
        values = dict(parsed.values)
        device.merge_state(values, group=BlockGroup.CORE)

    def _on_grid(parsed: Any) -> None:
        values = dict(parsed.values)
        # Keep legacy-friendly field aliases in flat state without polluting
        # group schema.
        if "phase_0_voltage" in values:
            values["grid_voltage"] = values.get("phase_0_voltage")
        if "phase_0_current" in values:
            values["grid_current"] = values.get("phase_0_current")
        if "phase_0_power" in values:
            values["grid_phase_0_power"] = values.get("phase_0_power")
        if "frequency" in values:
            values["grid_frequency"] = values.get("frequency")
        device.merge_state(values, group=BlockGroup.GRID)

    def _on_battery(parsed: Any) -> None:
        values = dict(parsed.values)
        device.merge_state(values, group=BlockGroup.BATTERY)

    def _on_inverter(parsed: Any) -> None:
        values = dict(parsed.values)
        device.merge_state(values, group=BlockGroup.INVERTER)

    def _on_cells(parsed: Any) -> None:
        values = dict(parsed.values)
        device.merge_state(values, group=BlockGroup.CELLS)

    device.register_handler(100, _on_home)
    device.register_handler(1300, _on_grid)
    device.register_handler(6000, _on_battery)
    device.register_handler(1100, _on_inverter)
    device.register_handler(1400, _on_inverter)
    device.register_handler(1500, _on_inverter)
    device.register_handler(6100, _on_cells)


def _load_schemas_for_profile(profile: Any, parser: Any) -> None:
    """Register all block schemas needed for *profile* into *parser*."""
    from .schemas import new_registry_with_builtins

    block_ids: set[int] = set()
    for group in profile.groups.values():
        block_ids.update(group.blocks)

    registry = new_registry_with_builtins()
    resolved = registry.resolve_blocks(list(block_ids), strict=True)
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
    handler_loader=_register_block_handlers,
)
