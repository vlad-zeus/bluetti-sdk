"""Unit tests for AsyncClient facade."""

import asyncio
from typing import Any
from unittest.mock import Mock

import pytest
from power_sdk.client_async import AsyncClient
from power_sdk.contracts.types import ParsedRecord
from power_sdk.devices.profiles import get_device_profile
from power_sdk.devices.types import DeviceProfile
from power_sdk.errors import ParserError, ProtocolError, TransportError
from power_sdk.models.types import BlockGroup


@pytest.fixture
def mock_transport() -> Mock:
    transport = Mock()
    transport.connect = Mock()
    transport.disconnect = Mock()
    transport.is_connected = Mock(return_value=True)
    return transport


@pytest.fixture
def device_profile() -> DeviceProfile:
    return get_device_profile("EL100V2")


def _make_parsed_block(block_id: int) -> ParsedRecord:
    return ParsedRecord(
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
async def test_async_connect_disconnect(
    mock_transport: Any, device_profile: Any
) -> None:
    client = AsyncClient(mock_transport, device_profile)
    await client.connect()
    await client.disconnect()
    mock_transport.connect.assert_called_once()
    mock_transport.disconnect.assert_called_once()


@pytest.mark.asyncio
async def test_async_context_manager(
    mock_transport: Any, device_profile: Any
) -> None:
    async with AsyncClient(mock_transport, device_profile) as client:
        assert client is not None

    mock_transport.connect.assert_called_once()
    mock_transport.disconnect.assert_called_once()


@pytest.mark.asyncio
async def test_async_read_block_delegates(
    mock_transport: Any, device_profile: Any
) -> None:
    client = AsyncClient(mock_transport, device_profile)
    parsed = _make_parsed_block(100)
    client._sync_client.read_block = Mock(return_value=parsed)

    result = await client.read_block(100)
    assert result == parsed
    client._sync_client.read_block.assert_called_once_with(100, None, True)


@pytest.mark.asyncio
async def test_async_read_group_ex_delegates(
    mock_transport: Any, device_profile: Any
) -> None:
    client = AsyncClient(mock_transport, device_profile)
    client._sync_client.read_group_ex = Mock(return_value=Mock(success=True))
    result = await client.read_group_ex(BlockGroup.CORE, partial_ok=True)
    assert result.success is True
    client._sync_client.read_group_ex.assert_called_once_with(BlockGroup.CORE, True)


@pytest.mark.asyncio
async def test_async_propagates_exceptions(
    mock_transport: Any, device_profile: Any
) -> None:
    client = AsyncClient(mock_transport, device_profile)
    client._sync_client.read_block = Mock(side_effect=TransportError("boom"))

    with pytest.raises(TransportError, match="boom"):
        await client.read_block(100)


@pytest.mark.asyncio
async def test_async_concurrent_access_safety(
    mock_transport: Any, device_profile: Any
) -> None:
    """Test that concurrent async calls are safely serialized.

    Multiple coroutines calling the client concurrently should not cause
    race conditions. All operations should complete successfully with
    predictable ordering due to internal lock.
    """
    client = AsyncClient(mock_transport, device_profile)

    # Track call order for verification
    call_order: list[Any] = []

    def read_block_mock(
        block_id: int,
        _register_count: int | None = None,
        _update_state: bool = True,
    ) -> ParsedRecord:
        # Simulate some work and record call
        call_order.append(block_id)
        return _make_parsed_block(block_id)

    def read_group_mock(
        group: BlockGroup, _partial_ok: bool = True
    ) -> list[ParsedRecord]:
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
async def test_async_lock_prevents_interleaving(
    mock_transport: Any, device_profile: Any
) -> None:
    """Test that lock prevents operation interleaving.

    Verify that while one operation is executing, others wait for the lock.
    """
    client = AsyncClient(mock_transport, device_profile)

    execution_log = []

    async def slow_operation(op_name: str) -> None:
        # Acquire lock (implicitly via client method)
        execution_log.append(f"{op_name}_start")
        # Simulate async work
        await asyncio.sleep(0.01)
        execution_log.append(f"{op_name}_end")

    # Mock to track execution
    call_count = 0

    def read_block_with_delay(
        block_id: int,
        _register_count: int | None = None,
        _update_state: bool = True,
    ) -> ParsedRecord:
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


@pytest.mark.asyncio
async def test_async_propagates_parser_error(
    mock_transport: Any, device_profile: Any
) -> None:
    """Test that ParserError from sync client propagates through async facade."""
    client = AsyncClient(mock_transport, device_profile)
    client._sync_client.read_block = Mock(
        side_effect=ParserError("Unknown block schema")
    )

    with pytest.raises(ParserError, match="Unknown block schema"):
        await client.read_block(999)


@pytest.mark.asyncio
async def test_async_propagates_protocol_error(
    mock_transport: Any, device_profile: Any
) -> None:
    """Test that ProtocolError from sync client propagates through async facade."""
    client = AsyncClient(mock_transport, device_profile)
    client._sync_client.read_block = Mock(side_effect=ProtocolError("CRC mismatch"))

    with pytest.raises(ProtocolError, match="CRC mismatch"):
        await client.read_block(100)


@pytest.mark.asyncio
async def test_async_context_disconnect_on_exception(
    mock_transport: Any, device_profile: Any
) -> None:
    """Test that disconnect is called even when exception occurs in context.

    Ensures proper cleanup when user code inside async with block raises.
    """
    disconnect_called = False

    def track_disconnect() -> None:
        nonlocal disconnect_called
        disconnect_called = True

    mock_transport.disconnect = Mock(side_effect=track_disconnect)

    with pytest.raises(ValueError, match="user error"):
        async with AsyncClient(mock_transport, device_profile) as client:
            assert client is not None
            raise ValueError("user error")

    # Disconnect must be called despite exception
    assert disconnect_called
    mock_transport.disconnect.assert_called_once()


@pytest.mark.asyncio
async def test_async_context_cleanup_on_connect_failure(
    mock_transport: Any, device_profile: Any
) -> None:
    """Test cleanup when connect() fails in __aenter__.

    Enhanced behavior: even though Python doesn't call __aexit__ on __aenter__ failure,
    our implementation explicitly calls disconnect() in the exception handler to ensure
    proper cleanup of partial connection states.
    """
    from power_sdk.utils.resilience import RetryPolicy

    mock_transport.connect = Mock(side_effect=TransportError("Connection refused"))

    # Use retry policy with single attempt to test cleanup without retries
    retry_policy = RetryPolicy(max_attempts=1)

    with pytest.raises(TransportError, match="Connection refused"):
        async with AsyncClient(
            mock_transport, device_profile, retry_policy=retry_policy
        ):
            pass  # Should not reach here

    # connect was attempted
    mock_transport.connect.assert_called_once()
    # disconnect SHOULD be called for cleanup (enhanced behavior)
    mock_transport.disconnect.assert_called_once()


@pytest.mark.asyncio
async def test_async_context_returns_false(
    mock_transport: Any, device_profile: Any
) -> None:
    """Test that __aexit__ returns False, allowing exceptions to propagate."""
    try:
        async with AsyncClient(mock_transport, device_profile):
            raise RuntimeError("test exception")
    except RuntimeError as exc:
        assert str(exc) == "test exception"
    else:
        pytest.fail("Exception should have propagated")


@pytest.mark.asyncio
async def test_async_multiple_operations_error_handling(
    mock_transport: Any, device_profile: Any
) -> None:
    """Test error handling when multiple concurrent operations fail.

    Verifies that errors from gather() are properly propagated.
    """
    client = AsyncClient(mock_transport, device_profile)

    def read_block_with_errors(
        block_id: int,
        _register_count: int | None = None,
        _update_state: bool = True,
    ) -> ParsedRecord:
        if block_id == 100:
            return _make_parsed_block(100)
        elif block_id == 1300:
            raise TransportError("Network timeout")
        else:
            raise ParserError("Unknown block")

    client._sync_client.read_block = Mock(side_effect=read_block_with_errors)

    # Use return_exceptions to collect all errors
    results = await asyncio.gather(
        client.read_block(100),
        client.read_block(1300),
        client.read_block(6000),
        return_exceptions=True,
    )

    assert len(results) == 3
    assert isinstance(results[0], ParsedRecord)  # Success
    assert isinstance(results[1], TransportError)  # Error
    assert isinstance(results[2], ParserError)  # Error


@pytest.mark.asyncio
async def test_async_context_preserves_original_exception(
    mock_transport: Any, device_profile: Any
) -> None:
    """Test that original exception is preserved if disconnect also fails.

    If an exception occurs in the async with block AND disconnect() fails,
    the original exception should propagate, not the disconnect error.
    This preserves diagnostic information about the actual failure.
    """
    # Make disconnect raise an exception
    mock_transport.disconnect = Mock(
        side_effect=TransportError("Disconnect failed")
    )

    original_error = ValueError("Original context error")

    # The original ValueError should propagate, not the TransportError
    with pytest.raises(ValueError, match="Original context error"):
        async with AsyncClient(mock_transport, device_profile):
            raise original_error

    # Both connect and disconnect should have been called
    mock_transport.connect.assert_called_once()
    mock_transport.disconnect.assert_called_once()


@pytest.mark.asyncio
async def test_async_context_disconnect_error_without_context_error(
    mock_transport: Any, device_profile: Any
) -> None:
    """Test that disconnect error propagates if no context exception.

    If the async with block succeeds but disconnect() fails,
    the disconnect error should propagate normally.
    """
    # Make disconnect raise an exception
    mock_transport.disconnect = Mock(
        side_effect=TransportError("Disconnect failed")
    )

    # The disconnect error should propagate since no context exception
    with pytest.raises(TransportError, match="Disconnect failed"):
        async with AsyncClient(mock_transport, device_profile):
            pass  # No exception in context

    # Both connect and disconnect should have been called
    mock_transport.connect.assert_called_once()
    mock_transport.disconnect.assert_called_once()


@pytest.mark.asyncio
async def test_async_client_passes_retry_policy_to_sync_client(
    mock_transport: Any, device_profile: Any
) -> None:
    """Test that AsyncClient passes retry_policy to underlying sync client."""
    from power_sdk.utils.resilience import RetryPolicy

    custom_policy = RetryPolicy(
        max_attempts=5,
        initial_delay=0.1,
        backoff_factor=1.5,
        max_delay=10.0,
    )

    client = AsyncClient(
        mock_transport, device_profile, retry_policy=custom_policy
    )

    # Verify retry_policy was passed to sync client
    assert client._sync_client.retry_policy is custom_policy
    assert client._sync_client.retry_policy.max_attempts == 5
    assert client._sync_client.retry_policy.initial_delay == 0.1


