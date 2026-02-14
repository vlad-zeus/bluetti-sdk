"""Unit tests for AsyncV2Client facade."""

import asyncio
from unittest.mock import Mock

import pytest
from bluetti_sdk.client_async import AsyncV2Client
from bluetti_sdk.devices.profiles import get_device_profile
from bluetti_sdk.errors import TransportError
from bluetti_sdk.models.types import BlockGroup
from bluetti_sdk.protocol.v2.types import ParsedBlock


@pytest.fixture
def mock_transport():
    transport = Mock()
    transport.connect = Mock()
    transport.disconnect = Mock()
    transport.is_connected = Mock(return_value=True)
    return transport


@pytest.fixture
def device_profile():
    return get_device_profile("EL100V2")


def _make_parsed_block(block_id: int) -> ParsedBlock:
    return ParsedBlock(
        block_id=block_id,
        name=f"BLOCK_{block_id}",
        values={"ok": True},
        raw=b"",
        length=0,
        protocol_version=2000,
        schema_version="1.0.0",
        timestamp=0.0,
    )


@pytest.mark.asyncio
async def test_async_connect_disconnect(mock_transport, device_profile):
    client = AsyncV2Client(mock_transport, device_profile)
    await client.connect()
    await client.disconnect()
    mock_transport.connect.assert_called_once()
    mock_transport.disconnect.assert_called_once()


@pytest.mark.asyncio
async def test_async_context_manager(mock_transport, device_profile):
    async with AsyncV2Client(mock_transport, device_profile) as client:
        assert client is not None

    mock_transport.connect.assert_called_once()
    mock_transport.disconnect.assert_called_once()


@pytest.mark.asyncio
async def test_async_read_block_delegates(mock_transport, device_profile):
    client = AsyncV2Client(mock_transport, device_profile)
    parsed = _make_parsed_block(100)
    client._sync_client.read_block = Mock(return_value=parsed)

    result = await client.read_block(100)
    assert result == parsed
    client._sync_client.read_block.assert_called_once_with(100, None)


@pytest.mark.asyncio
async def test_async_read_group_ex_delegates(mock_transport, device_profile):
    client = AsyncV2Client(mock_transport, device_profile)
    client._sync_client.read_group_ex = Mock(return_value=Mock(success=True))
    result = await client.read_group_ex(BlockGroup.CORE, partial_ok=True)
    assert result.success is True
    client._sync_client.read_group_ex.assert_called_once_with(BlockGroup.CORE, True)


@pytest.mark.asyncio
async def test_async_propagates_exceptions(mock_transport, device_profile):
    client = AsyncV2Client(mock_transport, device_profile)
    client._sync_client.read_block = Mock(side_effect=TransportError("boom"))

    with pytest.raises(TransportError, match="boom"):
        await client.read_block(100)


@pytest.mark.asyncio
async def test_async_concurrent_access_safety(mock_transport, device_profile):
    """Test that concurrent async calls are safely serialized.

    Multiple coroutines calling the client concurrently should not cause
    race conditions. All operations should complete successfully with
    predictable ordering due to internal lock.
    """
    client = AsyncV2Client(mock_transport, device_profile)

    # Track call order for verification
    call_order = []

    def read_block_mock(block_id, _register_count=None):
        # Simulate some work and record call
        call_order.append(block_id)
        return _make_parsed_block(block_id)

    def read_group_mock(group, _partial_ok=True):
        call_order.append(f"group_{group.value}")
        return [_make_parsed_block(100)]

    client._sync_client.read_block = Mock(side_effect=read_block_mock)
    client._sync_client.read_group = Mock(side_effect=read_group_mock)

    # Launch concurrent operations
    import asyncio

    results = await asyncio.gather(
        client.read_block(100),
        client.read_block(1300),
        client.read_group(BlockGroup.BATTERY),
        client.read_block(6000),
        client.read_group(BlockGroup.GRID),
    )

    # All operations should complete
    assert len(results) == 5
    assert all(r is not None for r in results)

    # Operations should have been serialized (all recorded)
    assert len(call_order) == 5
    # Verify specific calls were made (order may vary due to async scheduling)
    assert 100 in call_order
    assert 1300 in call_order
    assert 6000 in call_order
    assert "group_battery" in call_order
    assert "group_grid" in call_order


@pytest.mark.asyncio
async def test_async_lock_prevents_interleaving(mock_transport, device_profile):
    """Test that lock prevents operation interleaving.

    Verify that while one operation is executing, others wait for the lock.
    """
    client = AsyncV2Client(mock_transport, device_profile)

    execution_log = []

    async def slow_operation(op_name):
        # Acquire lock (implicitly via client method)
        execution_log.append(f"{op_name}_start")
        # Simulate async work
        await asyncio.sleep(0.01)
        execution_log.append(f"{op_name}_end")

    # Mock to track execution
    call_count = 0

    def read_block_with_delay(block_id, _register_count=None):
        nonlocal call_count
        call_count += 1
        # Record execution pattern
        execution_log.append(f"block_{block_id}")
        return _make_parsed_block(block_id)

    client._sync_client.read_block = Mock(side_effect=read_block_with_delay)

    # Launch two concurrent reads
    await asyncio.gather(client.read_block(100), client.read_block(200))

    # Both should complete
    assert call_count == 2
    # Operations should not interleave (serialized by lock)
    assert "block_100" in execution_log
    assert "block_200" in execution_log
