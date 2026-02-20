"""BridgeMapper contract — typed Protocol stub for snapshot-to-entity mapping.

Real implementations live in integration layers (e.g. home_assistant/) not
in the SDK core.  The SDK ships only the contract; integrations implement it.

Example::

    class MyBridge:
        def map_snapshot(self, snapshot: DeviceSnapshot) -> dict[str, Any]:
            return {
                "battery_soc": snapshot.state.get("total_battery_percent"),
                "ac_output_watts": snapshot.state.get("dc_output_power"),
            }
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from .device import DeviceSnapshot


@runtime_checkable
class BridgeMapper(Protocol):
    """Map a DeviceSnapshot to a flat key → value entity state dict.

    Implementations must be stateless — same snapshot always produces the
    same output dict.  No I/O; no side effects.
    """

    def map_snapshot(self, snapshot: DeviceSnapshot) -> dict[str, Any]:
        """Convert *snapshot* to an integration-specific entity state dict.

        Returns:
            A flat ``{entity_key: value}`` mapping for the integration layer.
        """
        ...
