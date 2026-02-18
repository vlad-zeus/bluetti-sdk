"""Parity tests to verify refactoring didn't change behavior.

These tests ensure that the extraction of GroupReader and dispatch registries
preserves the exact same behavior as before.
"""

from unittest.mock import Mock

import pytest
from power_sdk.client import Client
from power_sdk.contracts.types import ParsedRecord
from power_sdk.models.device import V2Device
from power_sdk.models.types import BlockGroup
from power_sdk.plugins.bluetti.v2.profiles import get_device_profile


@pytest.fixture
def test_profile():
    """Get test device profile."""
    return get_device_profile("EL100V2")


@pytest.fixture
def mock_transport():
    """Create mock transport."""
    transport = Mock()
    transport.connect = Mock()
    transport.disconnect = Mock()
    transport.is_connected = Mock(return_value=True)
    return transport


@pytest.fixture
def client(mock_transport, test_profile):
    """Create Client instance."""
    return Client(transport=mock_transport, profile=test_profile, device_address=1)


def test_read_group_behavior_unchanged(client, monkeypatch):
    """Verify read_group returns same results before/after refactoring."""
    # Mock read_block at the _group_reader level (after delegation)
    def mock_read_block(block_id):
        return ParsedRecord(
            block_id=block_id,
            name=f"BLOCK_{block_id}",
            values={"test_field": block_id * 10},
            raw=b"\x00\x00",
            length=2,
        )

    # Replace the injected read_block function in GroupReader
    client._group_reader.read_block = mock_read_block

    # Read CORE group (contains block 100)
    result = client.read_group(BlockGroup.CORE, partial_ok=True)

    # Verify result structure and content
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].block_id == 100
    assert result[0].values["test_field"] == 1000


def test_stream_group_behavior_unchanged(client, monkeypatch):
    """Verify stream_group yields same blocks before/after refactoring."""
    # Mock read_block at the _group_reader level (after delegation)
    def mock_read_block(block_id):
        return ParsedRecord(
            block_id=block_id,
            name=f"BLOCK_{block_id}",
            values={"order": block_id},
            raw=b"\x00\x00",
            length=2,
        )

    # Replace the injected read_block function in GroupReader
    client._group_reader.read_block = mock_read_block

    # Stream CORE group
    streamed = list(client.stream_group(BlockGroup.CORE, partial_ok=True))

    # Verify generator behavior
    assert len(streamed) == 1
    assert streamed[0].block_id == 100
    assert streamed[0].values["order"] == 100


def test_device_update_dispatch_unchanged():
    """Verify block updates produce same device state before/after registry."""
    device = V2Device(device_id="test", model="EL100V2", protocol_version=2000)

    # Update with block 100 (home data)
    parsed_100 = ParsedRecord(
        block_id=100,
        name="APP_HOME_DATA",
        values={"soc": 85, "pack_voltage": 54.0},
        raw=b"\x00\x00",
        length=2,
    )
    device.update_from_block(parsed_100)

    # Verify device state updated correctly
    assert device.home_data.soc == 85
    assert device.home_data.pack_voltage == 54.0

    # Update with block 1300 (grid info)
    parsed_1300 = ParsedRecord(
        block_id=1300,
        name="INV_GRID_INFO",
        values={"frequency": 50.0, "phase_0_voltage": 230.0},
        raw=b"\x00\x00",
        length=2,
    )
    device.update_from_block(parsed_1300)

    # Verify grid state updated correctly
    assert device.grid_info.frequency == 50.0
    assert device.grid_info.phase_0_voltage == 230.0


def test_group_state_dispatch_unchanged():
    """Verify group state retrieval returns same values before/after registry."""
    device = V2Device(device_id="test", model="EL100V2", protocol_version=2000)

    # Set up device state
    device.home_data.soc = 90
    device.home_data.pack_voltage = 55.0
    device.grid_info.frequency = 60.0
    device.battery_pack.cycles = 150

    # Retrieve group states
    core_state = device.get_group_state(BlockGroup.CORE)
    grid_state = device.get_group_state(BlockGroup.GRID)
    battery_state = device.get_group_state(BlockGroup.BATTERY)

    # Verify correct values returned
    assert core_state["soc"] == 90
    assert core_state["pack_voltage"] == 55.0
    assert grid_state["frequency"] == 60.0
    assert battery_state["cycles"] == 150


