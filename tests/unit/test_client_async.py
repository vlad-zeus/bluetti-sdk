"""Unit tests for AsyncClient facade.

Vendor/plugin-neutral: no imports from power_sdk.plugins.bluetti.*.
test_profile and mock_parser fixtures come from tests/conftest.py.
"""

import asyncio
from typing import Any
from unittest.mock import Mock, patch

import pytest
from power_sdk.client_async import AsyncClient
from power_sdk.contracts.types import ParsedRecord
from power_sdk.errors import ParserError, ProtocolError, TransportError
from power_sdk.models.types import BlockGroup

# test_profile and mock_parser are provided by tests/conftest.py


@pytest.fixture
def mock_transport() -> Mock:
    transport = Mock()
    transport.connect = Mock()
    transport.disconnect = Mock()
    transport.is_connected = Mock(return_value=True)
    return transport


def _make_parsed_block(block_id: int) -> ParsedRecord:
    return ParsedRecord(
        block_id=block_id,
        name=f"BLOCK_{block_id}",
        values={"ok": True},
        raw=b"",
        length=0,
        protocol_version=None,
        schema_version="1.0.0",
        timestamp=0.0,
    )


def _make_client(mock_transport, test_profile, mock_parser, **kwargs):
    return AsyncClient(mock_transport, test_profile, parser=mock_parser, **kwargs)


@pytest.mark.asyncio
async def test_async_connect_disconnect(
    mock_transport: Any, test_profile: Any, mock_parser: Any
) -> None:
    client = _make_client(mock_transport, test_profile, mock_parser)
    await client.connect()
    await client.disconnect()
    mock_transport.connect.assert_called_once()
    mock_transport.disconnect.assert_called_once()


@pytest.mark.asyncio
async def test_async_context_manager(
    mock_transport: Any, test_profile: Any, mock_parser: Any
) -> None:
    async with _make_client(mock_transport, test_profile, mock_parser) as client:
        assert client is not None
    mock_transport.connect.assert_called_once()
    mock_transport.disconnect.assert_called_once()


@pytest.mark.asyncio
async def test_async_read_block_delegates(
    mock_transport: Any, test_profile: Any, mock_parser: Any
) -> None:
    client = _make_client(mock_transport, test_profile, mock_parser)
    parsed = _make_parsed_block(100)
    client._sync_client.read_block = Mock(return_value=parsed)

    result = await client.read_block(100)
    assert result == parsed
    client._sync_client.read_block.assert_called_once_with(100, None, True)


@pytest.mark.asyncio
async def test_async_read_group_ex_delegates(
    mock_transport: Any, test_profile: Any, mock_parser: Any
) -> None:
    client = _make_client(mock_transport, test_profile, mock_parser)
    client._sync_client.read_group_ex = Mock(return_value=Mock(success=True))
    result = await client.read_group_ex(BlockGroup.CORE, partial_ok=True)
    assert result.success is True
    client._sync_client.read_group_ex.assert_called_once_with(BlockGroup.CORE, True)


@pytest.mark.asyncio
async def test_async_propagates_exceptions(
    mock_transport: Any, test_profile: Any, mock_parser: Any
) -> None:
    client = _make_client(mock_transport, test_profile, mock_parser)
    client._sync_client.read_block = Mock(side_effect=TransportError("boom"))
    with pytest.raises(TransportError, match="boom"):
        await client.read_block(100)


@pytest.mark.asyncio
async def test_async_concurrent_access_safety(
    mock_transport: Any, test_profile: Any, mock_parser: Any
) -> None:
    """Concurrent async calls are safely serialized."""
    client = _make_client(mock_transport, test_profile, mock_parser)
    call_order: list[Any] = []

    def read_block_mock(
        block_id: int,
        _register_count: int | None = None,
        _update_state: bool = True,
    ) -> ParsedRecord:
        call_order.append(block_id)
        return _make_parsed_block(block_id)

    def read_group_mock(
        group: BlockGroup, _partial_ok: bool = True
    ) -> list[ParsedRecord]:
        call_order.append(f"group_{group.value}")
        return [_make_parsed_block(100)]

    client._sync_client.read_block = Mock(side_effect=read_block_mock)
    client._sync_client.read_group = Mock(side_effect=read_group_mock)

    results = await asyncio.gather(
        client.read_block(100),
        client.read_block(1300),
        client.read_group(BlockGroup.BATTERY),
        client.read_block(6000),
        client.read_group(BlockGroup.GRID),
    )

    assert len(results) == 5
    assert all(r is not None for r in results)
    assert len(call_order) == 5
    assert 100 in call_order
    assert 1300 in call_order
    assert 6000 in call_order
    assert "group_battery" in call_order
    assert "group_grid" in call_order


@pytest.mark.asyncio
async def test_async_reads_execute_both_blocks(
    mock_transport: Any, test_profile: Any, mock_parser: Any
) -> None:
    """Both concurrent read_block calls complete successfully."""
    client = _make_client(mock_transport, test_profile, mock_parser)
    execution_log = []
    call_count = 0

    def read_block_impl(
        block_id: int,
        _register_count: int | None = None,
        _update_state: bool = True,
    ) -> ParsedRecord:
        nonlocal call_count
        call_count += 1
        execution_log.append(f"block_{block_id}")
        return _make_parsed_block(block_id)

    client._sync_client.read_block = Mock(side_effect=read_block_impl)
    await asyncio.gather(client.read_block(100), client.read_block(200))

    assert call_count == 2
    assert "block_100" in execution_log
    assert "block_200" in execution_log


@pytest.mark.asyncio
async def test_concurrent_reads_allowed(
    mock_transport: Any, test_profile: Any, mock_parser: Any
) -> None:
    """read_block calls no longer hold _op_lock; concurrent reads don't deadlock."""
    transport = mock_transport
    client = AsyncClient(
        transport=transport,
        profile=test_profile,
        parser=mock_parser,
    )
    # Both read_block calls should resolve without deadlock
    client._sync_client.read_block = Mock(return_value=_make_parsed_block(100))
    results = await asyncio.gather(
        client.read_block(100),
        client.read_block(1300),
    )
    assert len(results) == 2


@pytest.mark.asyncio
async def test_state_queries_use_to_thread(
    mock_transport: Any, test_profile: Any, mock_parser: Any
) -> None:
    """State queries delegate via to_thread to avoid event-loop blocking."""
    transport = mock_transport
    client = AsyncClient(
        transport=transport,
        profile=test_profile,
        parser=mock_parser,
    )
    calls: list[str] = []

    async def fake_to_thread(func, *args, **kwargs):
        calls.append(getattr(func, "__name__", str(func)))
        return func(*args, **kwargs)

    with patch("power_sdk.client_async.asyncio.to_thread", side_effect=fake_to_thread):
        state = await client.get_device_state()
        assert isinstance(state, dict)
        group_state = await client.get_group_state(BlockGroup.CORE)
        assert isinstance(group_state, dict)

    assert len(calls) == 2


@pytest.mark.asyncio
async def test_metadata_queries_are_local(
    mock_transport: Any, test_profile: Any, mock_parser: Any
) -> None:
    """Metadata queries stay local on sync client wrapper."""
    transport = mock_transport
    client = AsyncClient(
        transport=transport,
        profile=test_profile,
        parser=mock_parser,
    )
    groups = await client.get_available_groups()
    assert isinstance(groups, list)


@pytest.mark.asyncio
async def test_async_propagates_parser_error(
    mock_transport: Any, test_profile: Any, mock_parser: Any
) -> None:
    client = _make_client(mock_transport, test_profile, mock_parser)
    client._sync_client.read_block = Mock(
        side_effect=ParserError("Unknown block schema")
    )
    with pytest.raises(ParserError, match="Unknown block schema"):
        await client.read_block(999)


@pytest.mark.asyncio
async def test_async_propagates_protocol_error(
    mock_transport: Any, test_profile: Any, mock_parser: Any
) -> None:
    client = _make_client(mock_transport, test_profile, mock_parser)
    client._sync_client.read_block = Mock(side_effect=ProtocolError("CRC mismatch"))
    with pytest.raises(ProtocolError, match="CRC mismatch"):
        await client.read_block(100)


@pytest.mark.asyncio
async def test_astream_group_yields_incrementally(
    mock_transport: Any, test_profile: Any, mock_parser: Any
) -> None:
    client = _make_client(mock_transport, test_profile, mock_parser)
    events: list[str] = []

    def _gen():
        events.append("first_ready")
        yield _make_parsed_block(100)
        events.append("second_ready")
        yield _make_parsed_block(1300)

    client._sync_client.stream_group = Mock(side_effect=lambda *_a, **_k: _gen())
    stream = client.astream_group(BlockGroup.CORE)

    first = await stream.__anext__()
    assert first.block_id == 100
    assert events == ["first_ready"]

    second = await stream.__anext__()
    assert second.block_id == 1300
    assert events == ["first_ready", "second_ready"]


@pytest.mark.asyncio
async def test_async_context_disconnect_on_exception(
    mock_transport: Any, test_profile: Any, mock_parser: Any
) -> None:
    """disconnect() is called even when exception occurs inside the context."""
    disconnect_called = False

    def track_disconnect() -> None:
        nonlocal disconnect_called
        disconnect_called = True

    mock_transport.disconnect = Mock(side_effect=track_disconnect)

    with pytest.raises(ValueError, match="user error"):
        async with _make_client(mock_transport, test_profile, mock_parser) as client:
            assert client is not None
            raise ValueError("user error")

    assert disconnect_called
    mock_transport.disconnect.assert_called_once()


@pytest.mark.asyncio
async def test_async_context_cleanup_on_connect_failure(
    mock_transport: Any, test_profile: Any, mock_parser: Any
) -> None:
    """Cleanup happens even when connect() fails in __aenter__."""
    from power_sdk.utils.resilience import RetryPolicy

    mock_transport.connect = Mock(side_effect=TransportError("Connection refused"))
    retry_policy = RetryPolicy(max_attempts=1)

    with pytest.raises(TransportError, match="Connection refused"):
        async with _make_client(
            mock_transport, test_profile, mock_parser, retry_policy=retry_policy
        ):
            pass

    mock_transport.connect.assert_called_once()
    mock_transport.disconnect.assert_called_once()


@pytest.mark.asyncio
async def test_async_context_returns_false(
    mock_transport: Any, test_profile: Any, mock_parser: Any
) -> None:
    """__aexit__ returns False, allowing exceptions to propagate."""
    try:
        async with _make_client(mock_transport, test_profile, mock_parser):
            raise RuntimeError("test exception")
    except RuntimeError as exc:
        assert str(exc) == "test exception"
    else:
        pytest.fail("Exception should have propagated")


@pytest.mark.asyncio
async def test_async_multiple_operations_error_handling(
    mock_transport: Any, test_profile: Any, mock_parser: Any
) -> None:
    """Error handling when multiple concurrent operations fail."""
    client = _make_client(mock_transport, test_profile, mock_parser)

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

    results = await asyncio.gather(
        client.read_block(100),
        client.read_block(1300),
        client.read_block(6000),
        return_exceptions=True,
    )

    assert len(results) == 3
    assert isinstance(results[0], ParsedRecord)
    assert isinstance(results[1], TransportError)
    assert isinstance(results[2], ParserError)


@pytest.mark.asyncio
async def test_async_context_preserves_original_exception(
    mock_transport: Any, test_profile: Any, mock_parser: Any
) -> None:
    """Original exception preserved if disconnect also fails."""
    mock_transport.disconnect = Mock(side_effect=TransportError("Disconnect failed"))
    original_error = ValueError("Original context error")

    with pytest.raises(ValueError, match="Original context error"):
        async with _make_client(mock_transport, test_profile, mock_parser):
            raise original_error

    mock_transport.connect.assert_called_once()
    mock_transport.disconnect.assert_called_once()


@pytest.mark.asyncio
async def test_async_context_disconnect_error_without_context_error(
    mock_transport: Any, test_profile: Any, mock_parser: Any
) -> None:
    """Disconnect error propagates if no context exception."""
    mock_transport.disconnect = Mock(side_effect=TransportError("Disconnect failed"))

    with pytest.raises(TransportError, match="Disconnect failed"):
        async with _make_client(mock_transport, test_profile, mock_parser):
            pass

    mock_transport.connect.assert_called_once()
    mock_transport.disconnect.assert_called_once()


@pytest.mark.asyncio
async def test_async_client_passes_retry_policy_to_sync_client(
    mock_transport: Any, test_profile: Any, mock_parser: Any
) -> None:
    """AsyncClient passes retry_policy to the underlying sync client."""
    from power_sdk.utils.resilience import RetryPolicy

    custom_policy = RetryPolicy(
        max_attempts=5,
        initial_delay=0.1,
        backoff_factor=1.5,
        max_delay=10.0,
    )
    client = _make_client(
        mock_transport, test_profile, mock_parser, retry_policy=custom_policy
    )

    assert client._sync_client.retry_policy is custom_policy
    assert client._sync_client.retry_policy.max_attempts == 5
    assert client._sync_client.retry_policy.initial_delay == 0.1
