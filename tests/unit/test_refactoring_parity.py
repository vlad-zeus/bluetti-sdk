"""Parity tests to verify refactoring didn't change orchestration behavior."""

from unittest.mock import Mock

import pytest
from power_sdk.client import Client
from power_sdk.contracts.types import ParsedRecord
from power_sdk.models.device import Device
from power_sdk.models.types import BlockGroup


@pytest.fixture
def mock_transport():
    transport = Mock()
    transport.connect = Mock()
    transport.disconnect = Mock()
    transport.is_connected = Mock(return_value=True)
    return transport


@pytest.fixture
def client(mock_transport, test_profile, mock_parser):
    return Client(
        transport=mock_transport,
        profile=test_profile,
        parser=mock_parser,
        device_address=1,
    )


def test_read_group_behavior_unchanged(client):
    def mock_read_block(block_id):
        return ParsedRecord(
            block_id=block_id,
            name=f"BLOCK_{block_id}",
            values={"test_field": block_id * 10},
            raw=b"\x00\x00",
            length=2,
        )

    client._group_reader.read_block = mock_read_block
    result = client.read_group(BlockGroup.CORE, partial_ok=True)

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].block_id == 100
    assert result[0].values["test_field"] == 1000


def test_stream_group_behavior_unchanged(client):
    def mock_read_block(block_id):
        return ParsedRecord(
            block_id=block_id,
            name=f"BLOCK_{block_id}",
            values={"order": block_id},
            raw=b"\x00\x00",
            length=2,
        )

    client._group_reader.read_block = mock_read_block
    streamed = list(client.stream_group(BlockGroup.CORE, partial_ok=True))

    assert len(streamed) == 1
    assert streamed[0].block_id == 100
    assert streamed[0].values["order"] == 100


def test_device_update_dispatch_unchanged():
    device = Device(device_id="test", model="GENERIC", protocol_version=1)
    device.register_handler(
        100,
        lambda p: device.merge_state(dict(p.values), group=BlockGroup.CORE),
    )
    device.register_handler(
        1300,
        lambda p: device.merge_state(dict(p.values), group=BlockGroup.GRID),
    )

    device.update_from_block(
        ParsedRecord(
            block_id=100,
            name="CORE",
            values={"soc": 85, "pack_voltage": 54.0},
            raw=b"\x00\x00",
            length=2,
        )
    )
    device.update_from_block(
        ParsedRecord(
            block_id=1300,
            name="GRID",
            values={"frequency": 50.0, "phase_0_voltage": 230.0},
            raw=b"\x00\x00",
            length=2,
        )
    )

    assert device.get_group_state(BlockGroup.CORE)["soc"] == 85
    assert device.get_group_state(BlockGroup.GRID)["frequency"] == 50.0


def test_group_state_dispatch_unchanged():
    device = Device(device_id="test", model="GENERIC", protocol_version=1)
    device.merge_state({"soc": 90, "pack_voltage": 55.0}, group=BlockGroup.CORE)
    device.merge_state({"frequency": 60.0}, group=BlockGroup.GRID)
    device.merge_state({"cycles": 150}, group=BlockGroup.BATTERY)

    core_state = device.get_group_state(BlockGroup.CORE)
    grid_state = device.get_group_state(BlockGroup.GRID)
    battery_state = device.get_group_state(BlockGroup.BATTERY)

    assert core_state["soc"] == 90
    assert core_state["pack_voltage"] == 55.0
    assert grid_state["frequency"] == 60.0
    assert battery_state["cycles"] == 150
