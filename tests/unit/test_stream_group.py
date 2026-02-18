"""Tests for stream_group() and astream_group() streaming APIs."""

from unittest.mock import Mock

import pytest
from power_sdk.client import Client
from power_sdk.client_async import AsyncClient
from power_sdk.contracts.types import ParsedRecord
from power_sdk.devices.types import BlockGroupDefinition, DeviceProfile
from power_sdk.models.types import BlockGroup
from power_sdk.transport.mqtt import MQTTTransport

# Test profile with inverter group for testing
TEST_PROFILE = DeviceProfile(
    model="Test Device",
    type_id="test",
    protocol="v2",
    description="Test device profile",
    groups={
        "inverter": BlockGroupDefinition(
            name="inverter",
            blocks=[1100, 1400, 1500],
            description="Test inverter group",
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


def test_stream_group_yields_blocks_in_order(sync_client, monkeypatch):
    """Verify stream_group yields blocks in group order."""
    # Mock read_block to return fake parsed blocks
    # INVERTER group = [1100, 1400, 1500]
    def mock_read_block(block_id):
        return ParsedRecord(
            block_id=block_id, name=f"BLOCK_{block_id}", values={}, raw=b""
        )

    sync_client._group_reader.read_block = mock_read_block

    # Stream INVERTER group (1100, 1400, 1500)
    streamed_blocks = list(sync_client.stream_group(BlockGroup.INVERTER))

    # Verify blocks yielded in correct order
    assert len(streamed_blocks) == 3
    assert streamed_blocks[0].block_id == 1100
    assert streamed_blocks[1].block_id == 1400
    assert streamed_blocks[2].block_id == 1500


def test_stream_group_partial_ok_true_skips_failures(sync_client, monkeypatch):
    """Verify partial_ok=True skips failed blocks and continues."""
    # INVERTER group = [1100, 1400, 1500]
    def mock_read_block(block_id):
        if block_id == 1400:
            raise Exception("Simulated failure")
        return ParsedRecord(
            block_id=block_id, name=f"BLOCK_{block_id}", values={}, raw=b""
        )

    sync_client._group_reader.read_block = mock_read_block

    # Stream with partial_ok=True (default)
    streamed_blocks = list(
        sync_client.stream_group(BlockGroup.INVERTER, partial_ok=True)
    )

    # Should get 2 blocks (1100 and 1500), skipping 1400
    assert len(streamed_blocks) == 2
    assert streamed_blocks[0].block_id == 1100
    assert streamed_blocks[1].block_id == 1500


def test_stream_group_partial_ok_false_fails_fast(sync_client, monkeypatch):
    """Verify partial_ok=False fails on first error."""
    # INVERTER group = [1100, 1400, 1500]
    def mock_read_block(block_id):
        if block_id == 1400:
            raise ValueError("Simulated failure")
        return ParsedRecord(
            block_id=block_id, name=f"BLOCK_{block_id}", values={}, raw=b""
        )

    sync_client._group_reader.read_block = mock_read_block

    # Stream with partial_ok=False should raise on first error
    with pytest.raises(ValueError, match="Simulated failure"):
        list(sync_client.stream_group(BlockGroup.INVERTER, partial_ok=False))


def test_stream_group_parity_with_read_group_on_success(sync_client, monkeypatch):
    """Verify stream_group has same results as read_group on success path."""
    # INVERTER group = [1100, 1400, 1500]
    def mock_read_block(block_id):
        return ParsedRecord(
            block_id=block_id,
            name=f"BLOCK_{block_id}",
            values={"value": block_id},
            raw=b"",
        )

    sync_client._group_reader.read_block = mock_read_block

    # Get results from both APIs
    streamed = list(sync_client.stream_group(BlockGroup.INVERTER))
    batched = sync_client.read_group(BlockGroup.INVERTER)

    # Verify same results
    assert len(streamed) == len(batched)
    for s, b in zip(streamed, batched):
        assert s.block_id == b.block_id
        assert s.name == b.name
        assert s.values == b.values


def test_stream_group_invalid_group_raises_valueerror(sync_client):
    """Verify streaming invalid group raises ValueError."""
    # Create fake group enum
    from enum import Enum

    class FakeGroup(Enum):
        NONEXISTENT = "nonexistent"

    with pytest.raises(ValueError, match="not supported"):
        list(sync_client.stream_group(FakeGroup.NONEXISTENT))


@pytest.mark.asyncio
async def test_astream_group_yields_blocks_in_order(async_client, monkeypatch):
    """Verify astream_group yields blocks in group order (async)."""
    # INVERTER group = [1100, 1400, 1500]
    def mock_read_block(block_id, register_count=None):
        return ParsedRecord(
            block_id=block_id, name=f"BLOCK_{block_id}", values={}, raw=b""
        )

    monkeypatch.setattr(async_client._sync_client, "read_block", mock_read_block)

    # Stream INVERTER group asynchronously
    streamed_blocks = []
    async for block in async_client.astream_group(BlockGroup.INVERTER):
        streamed_blocks.append(block)

    # Verify blocks yielded in correct order
    assert len(streamed_blocks) == 3
    assert streamed_blocks[0].block_id == 1100
    assert streamed_blocks[1].block_id == 1400
    assert streamed_blocks[2].block_id == 1500


@pytest.mark.asyncio
async def test_astream_group_partial_ok_true_skips_failures(async_client, monkeypatch):
    """Verify astream_group partial_ok=True skips failed blocks (async)."""
    # INVERTER group = [1100, 1400, 1500]
    def mock_read_block(block_id, register_count=None):
        if block_id == 1400:
            raise Exception("Simulated async failure")
        return ParsedRecord(
            block_id=block_id, name=f"BLOCK_{block_id}", values={}, raw=b""
        )

    monkeypatch.setattr(async_client._sync_client, "read_block", mock_read_block)

    # Stream with partial_ok=True
    streamed_blocks = []
    async for block in async_client.astream_group(BlockGroup.INVERTER, partial_ok=True):
        streamed_blocks.append(block)

    # Should get 2 blocks (1100 and 1500), skipping 1400
    assert len(streamed_blocks) == 2
    assert streamed_blocks[0].block_id == 1100
    assert streamed_blocks[1].block_id == 1500


@pytest.mark.asyncio
async def test_astream_group_partial_ok_false_fails_fast(async_client, monkeypatch):
    """Verify astream_group partial_ok=False fails on first error (async)."""
    # INVERTER group = [1100, 1400, 1500]
    def mock_read_block(block_id, register_count=None):
        if block_id == 1400:
            raise ValueError("Simulated async failure")
        return ParsedRecord(
            block_id=block_id, name=f"BLOCK_{block_id}", values={}, raw=b""
        )

    monkeypatch.setattr(async_client._sync_client, "read_block", mock_read_block)

    # Stream with partial_ok=False should raise on first error
    with pytest.raises(ValueError, match="Simulated async failure"):
        async for _ in async_client.astream_group(
            BlockGroup.INVERTER, partial_ok=False
        ):
            pass


@pytest.mark.asyncio
async def test_astream_group_parity_with_read_group_on_success(
    async_client, monkeypatch
):
    """Verify astream_group has same results as read_group on success (async)."""
    # INVERTER group = [1100, 1400, 1500]
    def mock_read_block(block_id, register_count=None):
        return ParsedRecord(
            block_id=block_id,
            name=f"BLOCK_{block_id}",
            values={"value": block_id},
            raw=b"",
        )

    # Mock for astream_group (calls read_block directly)
    monkeypatch.setattr(async_client._sync_client, "read_block", mock_read_block)
    # Mock for read_group (delegates to GroupReader)
    async_client._sync_client._group_reader.read_block = mock_read_block

    # Get results from streaming API
    streamed = []
    async for block in async_client.astream_group(BlockGroup.INVERTER):
        streamed.append(block)

    # Get batch results
    batched = await async_client.read_group(BlockGroup.INVERTER)

    # Verify same results
    assert len(streamed) == len(batched)
    for s, b in zip(streamed, batched):
        assert s.block_id == b.block_id
        assert s.name == b.name
        assert s.values == b.values


@pytest.mark.asyncio
async def test_astream_group_invalid_group_raises_valueerror(async_client):
    """Verify streaming invalid group raises ValueError (async)."""
    from enum import Enum

    class FakeGroup(Enum):
        NONEXISTENT = "nonexistent"

    with pytest.raises(ValueError, match="not supported"):
        async for _ in async_client.astream_group(FakeGroup.NONEXISTENT):
            pass


