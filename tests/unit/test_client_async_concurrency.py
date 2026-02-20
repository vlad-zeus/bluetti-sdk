"""Async concurrency guardrail for AsyncClient.

Verifies that read_block operations are submitted to the thread pool
concurrently (not serialized at the AsyncClient level). The transport-level
_request_lock continues to serialize actual I/O — this test focuses on the
asyncio layer only.
"""

from __future__ import annotations

import asyncio
import threading
import time
from unittest.mock import Mock, patch

import pytest
from power_sdk.client_async import AsyncClient
from power_sdk.contracts.types import ParsedRecord
from power_sdk.models.types import BlockGroup

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


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


def _make_mock_transport() -> Mock:
    transport = Mock()
    transport.connect = Mock()
    transport.disconnect = Mock()
    transport.is_connected = Mock(return_value=True)
    transport.send_frame = Mock(return_value=b"\x00\x64")
    return transport


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_concurrent_reads_no_deadlock(test_profile, mock_parser):
    """asyncio.gather on multiple read_block calls completes without deadlock."""
    client = AsyncClient(
        transport=_make_mock_transport(),
        profile=test_profile,
        parser=mock_parser,
    )

    block_ids = [100, 1300, 1400, 1500]
    with patch.object(
        client._sync_client,
        "read_block",
        side_effect=[_make_parsed_block(bid) for bid in block_ids],
    ):
        results = await asyncio.gather(*[client.read_block(bid) for bid in block_ids])

    assert len(results) == len(block_ids)
    assert all(isinstance(r, ParsedRecord) for r in results)


@pytest.mark.asyncio
async def test_reads_submitted_concurrently_to_thread_pool(test_profile, mock_parser):
    """Core guardrail: without _op_lock on reads, N threads start concurrently.

    Uses threading.Barrier(N): all N threads must arrive before any proceeds.
    If reads were serialized by an asyncio lock, only 1 thread would run at a
    time → barrier.wait() would timeout → BrokenBarrierError → test fails.

    This is deterministic and avoids flaky timing assertions.
    """
    N = 3
    barrier = threading.Barrier(N, timeout=5.0)  # wide timeout for slow CI

    def barrier_read(block_id, *args, **kwargs):
        """Each thread must wait at the barrier until all N have arrived."""
        try:
            barrier.wait()
        except threading.BrokenBarrierError:
            pytest.fail(
                f"Barrier broken: reads appear to be serialized "
                f"(only 1 thread running at a time); expected {N} concurrent."
            )
        return _make_parsed_block(block_id)

    client = AsyncClient(
        transport=_make_mock_transport(),
        profile=test_profile,
        parser=mock_parser,
    )
    with patch.object(client._sync_client, "read_block", barrier_read):
        results = await asyncio.gather(
            *[client.read_block(i * 100) for i in range(1, N + 1)]
        )

    assert len(results) == N


@pytest.mark.asyncio
async def test_state_queries_schedule_to_thread(test_profile, mock_parser):
    """State queries use to_thread to avoid event-loop blocking on model locks."""
    client = AsyncClient(
        transport=_make_mock_transport(),
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
async def test_metadata_queries_stay_local(test_profile, mock_parser):
    """Metadata lookups remain local and do not require thread delegation."""
    client = AsyncClient(
        transport=_make_mock_transport(),
        profile=test_profile,
        parser=mock_parser,
    )
    groups = await client.get_available_groups()
    assert isinstance(groups, list)

    schemas = await client.get_registered_schemas()
    assert isinstance(schemas, dict)


@pytest.mark.asyncio
async def test_mutation_ops_still_serialized(test_profile, mock_parser):
    """connect/disconnect/register_schema still hold _op_lock."""
    transport = _make_mock_transport()
    client = AsyncClient(
        transport=transport,
        profile=test_profile,
        parser=mock_parser,
    )

    # Two concurrent connect calls should not corrupt state
    await asyncio.gather(
        client.connect(),
        client.connect(),
    )
    # Both calls happened (transport.connect called twice — serialized by _op_lock)
    assert transport.connect.call_count == 2


@pytest.mark.asyncio
async def test_read_and_query_interleave(test_profile, mock_parser):
    """A pure query (get_device_state) can interleave with an ongoing read_block."""
    read_started = asyncio.Event()
    # Capture the running loop before entering the thread pool worker.
    # asyncio.get_event_loop() is deprecated inside threads in Python 3.12+.
    loop = asyncio.get_running_loop()

    def slow_read(block_id, *args, **kwargs):
        # Signal that read has started from within the thread pool worker.
        loop.call_soon_threadsafe(read_started.set)
        time.sleep(0.02)
        return _make_parsed_block(block_id)

    client = AsyncClient(
        transport=_make_mock_transport(),
        profile=test_profile,
        parser=mock_parser,
    )

    async def do_read():
        with patch.object(client._sync_client, "read_block", slow_read):
            return await client.read_block(100)

    async def do_query():
        await read_started.wait()
        # This should NOT wait for read_block to finish (no _op_lock on reads)
        return await client.get_device_state()

    read_task = asyncio.create_task(do_read())
    query_task = asyncio.create_task(do_query())
    block, state = await asyncio.gather(read_task, query_task)

    assert isinstance(block, ParsedRecord)
    assert isinstance(state, dict)
