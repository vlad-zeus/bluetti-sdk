"""Tests for device dispatch behavior."""

import logging
from unittest.mock import Mock

import pytest
from power_sdk.contracts.types import ParsedRecord
from power_sdk.models.device import Device
from power_sdk.models.types import BlockGroup


@pytest.fixture
def device():
    d = Device(device_id="test_device", model="TEST", protocol_version=1)

    def on_core(parsed: ParsedRecord) -> None:
        d.merge_state(dict(parsed.values), group=BlockGroup.CORE)

    def on_grid(parsed: ParsedRecord) -> None:
        d.merge_state(dict(parsed.values), group=BlockGroup.GRID)

    def on_battery(parsed: ParsedRecord) -> None:
        d.merge_state(dict(parsed.values), group=BlockGroup.BATTERY)

    d.register_handler(100, on_core)
    d.register_handler(1300, on_grid)
    d.register_handler(6000, on_battery)
    return d


def test_dispatch_core_handler(device):
    parsed = ParsedRecord(
        block_id=100,
        name="CORE",
        values={"soc": 85},
        raw=b"\x00\x55",
        length=2,
    )
    device.update_from_block(parsed)
    assert device.get_group_state(BlockGroup.CORE)["soc"] == 85


def test_dispatch_grid_handler(device):
    parsed = ParsedRecord(
        block_id=1300,
        name="GRID",
        values={"frequency": 50.0},
        raw=b"\x01\xf4",
        length=2,
    )
    device.update_from_block(parsed)
    assert device.get_group_state(BlockGroup.GRID)["frequency"] == 50.0


def test_dispatch_battery_handler(device):
    parsed = ParsedRecord(
        block_id=6000,
        name="BATTERY",
        values={"cycles": 100},
        raw=b"\x00\x64",
        length=2,
    )
    device.update_from_block(parsed)
    assert device.get_group_state(BlockGroup.BATTERY)["cycles"] == 100


def test_unknown_block_warns(device, caplog):
    parsed = ParsedRecord(
        block_id=9999,
        name="UNKNOWN",
        values={},
        raw=b"\x00\x00",
        length=2,
    )
    with caplog.at_level(logging.WARNING, logger="power_sdk.models.device"):
        device.update_from_block(parsed)
    assert any("Unknown block 9999" in record.message for record in caplog.records)


def test_custom_handler_registration(device):
    custom = Mock()
    device.register_handler(7777, custom)
    parsed = ParsedRecord(
        block_id=7777,
        name="CUSTOM",
        values={"custom": True},
        raw=b"\x00\x01",
        length=2,
    )
    device.update_from_block(parsed)
    custom.assert_called_once_with(parsed)


def test_handler_exception_propagates(device):
    """Handler exceptions propagate from update_from_block (fail-fast policy).

    Variant A: raw block IS stored before handler is called, so callers that
    catch the exception can still retrieve the block via get_raw_block().
    The exception is NOT suppressed.
    """

    def broken_handler(parsed: ParsedRecord) -> None:
        raise ValueError("handler error")

    device.register_handler(5555, broken_handler)
    parsed = ParsedRecord(
        block_id=5555,
        name="BROKEN",
        values={"x": 1},
        raw=b"\x00\x01",
        length=2,
    )

    # Exception propagates — not swallowed
    with pytest.raises(ValueError, match="handler error"):
        device.update_from_block(parsed)

    # Raw block was stored BEFORE the handler was called
    assert device.get_raw_block(5555) is parsed
