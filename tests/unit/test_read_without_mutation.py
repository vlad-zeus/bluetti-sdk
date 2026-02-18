"""Tests for non-mutating read path (update_state parameter).

Verifies that read_block can be called without side effects when update_state=False.
This addresses CQRS violation and enables query-only mode.
"""

from unittest.mock import Mock

import pytest
from power_sdk.client import Client
from power_sdk.client_async import AsyncClient
from power_sdk.contracts.protocol import NormalizedPayload
from power_sdk.devices.types import BlockGroupDefinition, DeviceProfile
from power_sdk.protocol.v2.types import ParsedBlock
from power_sdk.transport.mqtt import MQTTTransport

# Test profile
TEST_PROFILE = DeviceProfile(
    model="Test Device",
    type_id="test",
    protocol="v2",
    description="Test device profile",
    groups={
        "core": BlockGroupDefinition(
            name="core",
            blocks=[100],
            description="Test core group",
            poll_interval=5,
        ),
    },
)


@pytest.fixture
def mock_transport():
    """Create mock transport."""
    transport = Mock(spec=MQTTTransport)
    transport.is_connected.return_value = True
    return transport


@pytest.fixture
def sync_client(mock_transport):
    """Create sync client with mock transport."""
    return Client(transport=mock_transport, profile=TEST_PROFILE)


@pytest.fixture
def async_client(mock_transport):
    """Create async client with mock transport."""
    return AsyncClient(transport=mock_transport, profile=TEST_PROFILE)


def test_read_block_with_update_state_true_default(sync_client, monkeypatch):
    """Verify read_block updates device state by default (update_state=True)."""
    # Mock protocol layer to return normalized payload
    monkeypatch.setattr(
        sync_client.protocol,
        "read_block",
        lambda **kwargs: NormalizedPayload(
            block_id=100, data=b"\x00\x00\x00\x55", device_address=1
        ),
    )

    # Mock parser to return predictable parsed block
    def mock_parse_block(block_id, data, validate, protocol_version):
        return ParsedBlock(
            block_id=block_id,
            name="TEST_BLOCK",
            values={"test_field": 42},
            raw=data,
        )

    monkeypatch.setattr(sync_client.parser, "parse_block", mock_parse_block)

    # Get initial device state
    initial_blocks = len(sync_client.device._blocks)

    # Read block (default: update_state=True)
    result = sync_client.read_block(100)

    # Verify block was parsed
    assert result.block_id == 100
    assert result.values["test_field"] == 42

    # Verify device state was updated
    assert len(sync_client.device._blocks) == initial_blocks + 1
    assert 100 in sync_client.device._blocks


def test_read_block_with_update_state_false_no_mutation(sync_client, monkeypatch):
    """Verify read_block with update_state=False does NOT update device state."""
    # Mock protocol layer to return normalized payload
    monkeypatch.setattr(
        sync_client.protocol,
        "read_block",
        lambda **kwargs: NormalizedPayload(
            block_id=100, data=b"\x00\x00\x00\x55", device_address=1
        ),
    )

    # Mock parser to return predictable parsed block
    def mock_parse_block(block_id, data, validate, protocol_version):
        return ParsedBlock(
            block_id=block_id,
            name="TEST_BLOCK",
            values={"test_field": 99},
            raw=data,
        )

    monkeypatch.setattr(sync_client.parser, "parse_block", mock_parse_block)

    # Get initial device state
    initial_blocks = len(sync_client.device._blocks)
    initial_last_update = sync_client.device.last_update

    # Read block with update_state=False (query-only mode)
    result = sync_client.read_block(100, update_state=False)

    # Verify block was parsed
    assert result.block_id == 100
    assert result.values["test_field"] == 99

    # Verify device state was NOT updated
    assert len(sync_client.device._blocks) == initial_blocks
    assert 100 not in sync_client.device._blocks
    assert sync_client.device.last_update == initial_last_update


@pytest.mark.asyncio
async def test_async_read_block_with_update_state_false(async_client, monkeypatch):
    """Verify AsyncClient.read_block respects update_state parameter."""
    # Mock protocol layer to return normalized payload
    monkeypatch.setattr(
        async_client._sync_client.protocol,
        "read_block",
        lambda **kwargs: NormalizedPayload(
            block_id=100, data=b"\x00\x00\x00\x55", device_address=1
        ),
    )

    # Mock parser to return predictable parsed block
    def mock_parse_block(block_id, data, validate, protocol_version):
        return ParsedBlock(
            block_id=block_id,
            name="TEST_BLOCK",
            values={"async_field": 123},
            raw=data,
        )

    monkeypatch.setattr(
        async_client._sync_client.parser, "parse_block", mock_parse_block
    )

    # Get initial device state
    initial_blocks = len(async_client._sync_client.device._blocks)

    # Read block with update_state=False (query-only mode)
    result = await async_client.read_block(100, update_state=False)

    # Verify block was parsed
    assert result.block_id == 100
    assert result.values["async_field"] == 123

    # Verify device state was NOT updated
    assert len(async_client._sync_client.device._blocks) == initial_blocks
    assert 100 not in async_client._sync_client.device._blocks


