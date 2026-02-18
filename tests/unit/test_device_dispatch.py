"""Tests for device dispatch registries."""

from unittest.mock import Mock

import pytest
from power_sdk.contracts.types import ParsedRecord
from power_sdk.models.device import (
    V2Device,
)
from power_sdk.models.types import BlockGroup


@pytest.fixture
def device():
    """Create V2Device instance."""
    return V2Device(device_id="test_device", model="EL100V2", protocol_version=2000)


def test_block_update_registry_dispatches_100(device):
    """Verify BlockUpdateRegistry dispatches block 100 to _update_home_data."""
    parsed = ParsedRecord(
        block_id=100,
        name="APP_HOME_DATA",
        values={"soc": 85},
        raw=b"\x00\x55",
        length=2,
    )

    device.update_from_block(parsed)

    # Verify home_data was updated
    assert device.home_data.soc == 85


def test_block_update_registry_dispatches_1300(device):
    """Verify BlockUpdateRegistry dispatches block 1300 to _update_grid_info."""
    parsed = ParsedRecord(
        block_id=1300,
        name="INV_GRID_INFO",
        values={"frequency": 50.0},
        raw=b"\x01\xF4",
        length=2,
    )

    device.update_from_block(parsed)

    # Verify grid_info was updated
    assert device.grid_info.frequency == 50.0


def test_block_update_registry_dispatches_6000(device):
    """Verify BlockUpdateRegistry dispatches block 6000 to _update_battery_pack."""
    parsed = ParsedRecord(
        block_id=6000,
        name="PACK_MAIN_INFO",
        values={"soc": 90},
        raw=b"\x00\x5A",
        length=2,
    )

    device.update_from_block(parsed)

    # Verify battery_pack was updated
    assert device.battery_pack.soc == 90


def test_block_update_registry_warns_on_unknown(device, caplog):
    """Verify BlockUpdateRegistry logs warning for unknown block."""
    parsed = ParsedRecord(
        block_id=9999,
        name="UNKNOWN_BLOCK",
        values={},
        raw=b"\x00\x00",
        length=2,
    )

    device.update_from_block(parsed)

    # Verify warning was logged
    assert any("Unknown block 9999" in record.message for record in caplog.records)


def test_group_state_registry_dispatches_grid(device):
    """Verify GroupStateRegistry dispatches GRID group to _get_grid_state."""
    # Set up grid data
    device.grid_info.frequency = 50.0
    device.grid_info.phase_0_voltage = 230.0

    state = device.get_group_state(BlockGroup.GRID)

    assert state["frequency"] == 50.0
    assert state["voltage"] == 230.0


def test_group_state_registry_dispatches_core(device):
    """Verify GroupStateRegistry dispatches CORE group to _get_core_state."""
    # Set up home data
    device.home_data.soc = 85
    device.home_data.pack_voltage = 54.0

    state = device.get_group_state(BlockGroup.CORE)

    assert state["soc"] == 85
    assert state["pack_voltage"] == 54.0


def test_group_state_registry_dispatches_battery(device):
    """Verify GroupStateRegistry dispatches BATTERY group to _get_battery_state."""
    # Set up battery pack data
    device.battery_pack.soc = 90
    device.battery_pack.cycles = 100

    state = device.get_group_state(BlockGroup.BATTERY)

    assert state["soc"] == 90
    assert state["cycles"] == 100


def test_custom_handler_registration(device):
    """Verify BlockUpdateRegistry supports custom handler registration."""
    # Register custom handler for new block
    custom_handler = Mock()
    device._block_registry.register_handler(7777, custom_handler)

    parsed = ParsedRecord(
        block_id=7777,
        name="CUSTOM_BLOCK",
        values={"custom": "data"},
        raw=b"\x00\x00",
        length=2,
    )

    device.update_from_block(parsed)

    # Verify custom handler was called
    custom_handler.assert_called_once_with(parsed)

