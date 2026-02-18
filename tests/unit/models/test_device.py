"""Unit tests for device model."""

import time
from datetime import datetime

from power_sdk.contracts.types import ParsedRecord
from power_sdk.models.device import BatteryPackInfo, Device, GridInfo, HomeData
from power_sdk.models.types import BlockGroup


def test_grid_info_creation():
    """Test GridInfo dataclass creation."""
    grid = GridInfo(
        frequency=50.0, phase_0_voltage=230.4, phase_0_current=5.2, phase_0_power=1196
    )

    assert grid.frequency == 50.0
    assert grid.phase_0_voltage == 230.4
    assert grid.phase_0_current == 5.2
    assert grid.phase_0_power == 1196


def test_home_data_creation():
    """Test HomeData dataclass creation."""
    home = HomeData(soc=85, pack_voltage=51.2, pack_current=10.5, pack_power=537)

    assert home.soc == 85
    assert home.pack_voltage == 51.2
    assert home.pack_current == 10.5
    assert home.pack_power == 537


def test_battery_pack_info_creation():
    """Test BatteryPackInfo dataclass creation."""
    pack = BatteryPackInfo(
        soc=85,
        voltage=51.2,
        current=10.5,
        power=537,
        temp_max=35,
        temp_min=20,
        temp_avg=28,
        cycles=42,
        soh=98,
    )

    assert pack.soc == 85
    assert pack.voltage == 51.2
    assert pack.cycles == 42
    assert pack.soh == 98


def test_v2device_creation():
    """Test V2Device creation."""
    device = Device(model="EL100V2", device_id="test_device_001")

    assert device.model == "EL100V2"
    assert device.device_id == "test_device_001"
    # State containers are created but empty
    assert device.grid_info is not None
    assert device.home_data is not None
    assert device.battery_pack is not None
    assert device.grid_info.frequency is None  # Not yet updated


def test_v2device_update_grid_info():
    """Test updating grid info from parsed block."""
    device = Device(model="EL100V2", device_id="test_device_001")

    # Create parsed block (Block 1300)
    parsed = ParsedRecord(
        block_id=1300,
        name="INV_GRID_INFO",
        length=32,
        values={
            "frequency": 50.0,
            "phase_0_voltage": 230.4,
            "phase_0_current": 5.2,
            "phase_0_power": 1196,
        },
        raw=bytes(32),
        timestamp=time.time(),
    )

    device.update_from_block(parsed)

    # Grid info should be updated
    assert device.grid_info is not None
    assert device.grid_info.frequency == 50.0
    assert device.grid_info.phase_0_voltage == 230.4
    assert device.grid_info.phase_0_current == 5.2
    assert device.grid_info.phase_0_power == 1196


def test_v2device_update_home_data():
    """Test updating home data from parsed block."""
    device = Device(model="EL100V2", device_id="test_device_001")

    # Create parsed block (Block 100)
    parsed = ParsedRecord(
        block_id=100,
        name="APP_HOME_DATA",
        length=100,
        values={
            "soc": 85,
            "pack_voltage": 51.2,
            "pack_current": 10.5,
            "pack_power": 537,
            "ac_input_power": 0,
            "ac_output_power": 500,
            "dc_input_power": 100,
            "pv_power": 100,
        },
        raw=bytes(100),
        timestamp=time.time(),
    )

    device.update_from_block(parsed)

    # Home data should be updated
    assert device.home_data is not None
    assert device.home_data.soc == 85
    assert device.home_data.pack_voltage == 51.2
    assert device.home_data.ac_output_power == 500
    assert device.home_data.pv_power == 100


def test_v2device_update_battery_pack():
    """Test updating battery pack from parsed block."""
    device = Device(model="EL100V2", device_id="test_device_001")

    # Create parsed block (Block 6000)
    parsed = ParsedRecord(
        block_id=6000,
        name="PACK_MAIN_INFO",
        length=50,
        values={
            "soc": 85,
            "voltage": 51.2,
            "current": 10.5,
            "power": 537,
            "temp_max": 35,
            "temp_min": 20,
            "temp_avg": 28,
            "cycles": 42,
            "soh": 98,
        },
        raw=bytes(50),
        timestamp=time.time(),
    )

    device.update_from_block(parsed)

    # Battery pack should be updated
    assert device.battery_pack is not None
    assert device.battery_pack.soc == 85
    assert device.battery_pack.voltage == 51.2
    assert device.battery_pack.cycles == 42
    assert device.battery_pack.soh == 98


def test_v2device_update_unknown_block():
    """Test updating with unknown block ID."""
    device = Device(model="EL100V2", device_id="test_device_001")

    # Unknown block
    parsed = ParsedRecord(
        block_id=9999,
        name="UNKNOWN",
        length=10,
        values={"test": 123},
        raw=bytes(10),
        timestamp=time.time(),
    )

    # Should not raise, just log warning
    device.update_from_block(parsed)


def test_v2device_get_state_empty():
    """Test getting state when no data."""
    device = Device(model="EL100V2", device_id="test_device_001")

    state = device.get_state()

    assert state["model"] == "EL100V2"
    assert state["device_id"] == "test_device_001"
    assert state["last_update"] is None
    # Grid/home fields not included if not updated
    assert "grid_voltage" not in state
    assert "soc" not in state


def test_v2device_get_state_with_data():
    """Test getting state with data."""
    device = Device(model="EL100V2", device_id="test_device_001")

    # Add grid info
    device.grid_info = GridInfo(
        frequency=50.0,
        phase_0_voltage=230.4,
        phase_0_current=5.2,
        phase_0_power=1196,
        last_update=datetime.now(),  # Mark as updated
    )

    # Add home data
    device.home_data = HomeData(
        soc=85,
        pack_voltage=51.2,
        pack_current=10.5,
        pack_power=537,
        last_update=datetime.now(),  # Mark as updated
    )

    state = device.get_state()

    assert state["model"] == "EL100V2"
    assert state["grid_voltage"] == 230.4
    assert state["grid_frequency"] == 50.0
    # Note: grid_power from grid_info is overwritten by home_data.grid_power
    # so it will be None unless home_data.grid_power is set
    assert state["soc"] == 85
    assert state["pack_voltage"] == 51.2


def test_v2device_get_group_state_grid():
    """Test getting grid group state."""
    device = Device(model="EL100V2", device_id="test_device_001")

    device.grid_info = GridInfo(
        frequency=50.0, phase_0_voltage=230.4, phase_0_current=5.2, phase_0_power=1196
    )

    grid_state = device.get_group_state(BlockGroup.GRID)

    # Keys are simplified (no phase_0_ prefix)
    assert grid_state["frequency"] == 50.0
    assert grid_state["voltage"] == 230.4
    assert grid_state["current"] == 5.2
    assert grid_state["power"] == 1196


def test_v2device_get_group_state_core():
    """Test getting core group state."""
    device = Device(model="EL100V2", device_id="test_device_001")

    device.home_data = HomeData(
        soc=85, pack_voltage=51.2, pack_current=10.5, pack_power=537
    )

    core_state = device.get_group_state(BlockGroup.CORE)

    assert core_state["soc"] == 85
    assert core_state["pack_voltage"] == 51.2
    assert core_state["pack_power"] == 537


def test_v2device_get_group_state_battery():
    """Test getting battery group state."""
    device = Device(model="EL100V2", device_id="test_device_001")

    device.battery_pack = BatteryPackInfo(
        soc=85, voltage=51.2, current=10.5, power=537, cycles=42, soh=98
    )

    battery_state = device.get_group_state(BlockGroup.BATTERY)

    assert battery_state["soc"] == 85
    assert battery_state["voltage"] == 51.2
    assert battery_state["cycles"] == 42
    assert battery_state["soh"] == 98


def test_v2device_get_group_state_empty():
    """Test getting group state when no data."""
    device = Device(model="EL100V2", device_id="test_device_001")

    grid_state = device.get_group_state(BlockGroup.GRID)

    # Returns dict with None values
    assert "frequency" in grid_state
    assert "voltage" in grid_state
    assert grid_state["frequency"] is None
    assert grid_state["last_update"] is None


def test_v2device_last_update_tracking():
    """Test last update timestamp tracking."""
    device = Device(model="EL100V2", device_id="test_device_001")

    assert device.last_update is None

    # Update with block
    parsed = ParsedRecord(
        block_id=1300,
        name="INV_GRID_INFO",
        length=32,
        values={"frequency": 50.0},
        raw=bytes(32),
        timestamp=time.time(),
    )

    device.update_from_block(parsed)

    # Last update should be set (datetime object)
    assert device.last_update is not None
    assert isinstance(device.last_update, datetime)


def test_v2device_multiple_updates():
    """Test multiple sequential updates."""
    device = Device(model="EL100V2", device_id="test_device_001")

    # Update grid
    grid_block = ParsedRecord(
        block_id=1300,
        name="INV_GRID_INFO",
        length=32,
        values={"frequency": 50.0, "phase_0_voltage": 230.4},
        raw=bytes(32),
        timestamp=time.time(),
    )
    device.update_from_block(grid_block)

    # Update home
    home_block = ParsedRecord(
        block_id=100,
        name="APP_HOME_DATA",
        length=100,
        values={"soc": 85, "pack_voltage": 51.2},
        raw=bytes(100),
        timestamp=time.time(),
    )
    device.update_from_block(home_block)

    # Both should be updated
    assert device.grid_info is not None
    assert device.home_data is not None
    assert device.grid_info.frequency == 50.0
    assert device.home_data.soc == 85


def test_v2device_partial_data():
    """Test updating with partial data (optional fields)."""
    device = Device(model="EL100V2", device_id="test_device_001")

    # Minimal data
    parsed = ParsedRecord(
        block_id=1300,
        name="INV_GRID_INFO",
        length=32,
        values={
            "frequency": 50.0,
            # Missing other fields
        },
        raw=bytes(32),
        timestamp=time.time(),
    )

    device.update_from_block(parsed)

    # Should update with available data
    assert device.grid_info is not None
    assert device.grid_info.frequency == 50.0
    assert device.grid_info.phase_0_voltage is None

