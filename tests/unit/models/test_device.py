"""Unit tests for vendor-neutral Device model."""

import time
from datetime import datetime

from power_sdk.contracts.types import ParsedRecord
from power_sdk.models.device import Device
from power_sdk.models.types import BlockGroup


def _record(block_id: int, values: dict) -> ParsedRecord:
    return ParsedRecord(
        block_id=block_id,
        name=f"BLOCK_{block_id}",
        length=16,
        values=values,
        raw=bytes(16),
        timestamp=time.time(),
    )


def test_device_creation():
    device = Device(model="GENERIC", device_id="d1")
    assert device.model == "GENERIC"
    assert device.device_id == "d1"
    assert device.last_update is None


def test_update_from_block_with_registered_handler_merges_state():
    device = Device(model="GENERIC", device_id="d1")

    def on_core(parsed: ParsedRecord) -> None:
        device.merge_state(dict(parsed.values), group=BlockGroup.CORE)

    device.register_handler(100, on_core)
    device.update_from_block(_record(100, {"soc": 85, "pack_voltage": 51.2}))

    state = device.get_state()
    assert state["soc"] == 85
    assert state["pack_voltage"] == 51.2
    core = device.get_group_state(BlockGroup.CORE)
    assert core["soc"] == 85


def test_update_unknown_block_does_not_crash():
    device = Device(model="GENERIC", device_id="d1")
    device.update_from_block(_record(9999, {"x": 1}))
    assert device.get_state()["model"] == "GENERIC"


def test_last_update_tracking():
    device = Device(model="GENERIC", device_id="d1")

    def on_grid(parsed: ParsedRecord) -> None:
        device.merge_state(dict(parsed.values), group=BlockGroup.GRID)

    device.register_handler(1300, on_grid)
    device.update_from_block(_record(1300, {"frequency": 50.0}))
    assert isinstance(device.last_update, datetime)


def test_multiple_group_updates_keep_separate_group_state():
    device = Device(model="GENERIC", device_id="d1")
    device.register_handler(
        100,
        lambda p: device.merge_state(dict(p.values), group=BlockGroup.CORE),
    )
    device.register_handler(
        1300,
        lambda p: device.merge_state(dict(p.values), group=BlockGroup.GRID),
    )

    device.update_from_block(_record(100, {"soc": 90}))
    device.update_from_block(_record(1300, {"frequency": 60.0}))

    assert device.get_group_state(BlockGroup.CORE)["soc"] == 90
    assert device.get_group_state(BlockGroup.GRID)["frequency"] == 60.0


def test_get_group_state_empty_returns_empty_dict():
    device = Device(model="GENERIC", device_id="d1")
    assert device.get_group_state(BlockGroup.BATTERY) == {}


def test_raw_block_storage():
    device = Device(model="GENERIC", device_id="d1")

    def on_core(parsed: ParsedRecord) -> None:
        device.merge_state(dict(parsed.values), group=BlockGroup.CORE)

    rec = _record(100, {"soc": 77})
    device.register_handler(100, on_core)
    device.update_from_block(rec)

    assert device.get_raw_block(100) is rec


def test_no_handler_leaves_projected_state_unchanged():
    device = Device(model="GENERIC", device_id="d1")
    device.update_from_block(_record(100, {"soc": 77}))
    assert "soc" not in device.get_state()
