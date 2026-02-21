"""Tests for async Executor and per-device loop."""

from __future__ import annotations

import asyncio

import pytest
from power_sdk.runtime import Executor

from tests.helpers import make_device_runtime, make_registry

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_executor_polls_device_multiple_times():
    """With poll_interval=10ms, expect >= 2 polls in 80ms."""
    runtime = make_device_runtime("dev1", poll_interval=0.01)
    registry = make_registry(runtime)
    executor = Executor(registry, connect=False, jitter_max=0.0)

    run_task = asyncio.create_task(executor.run())
    await asyncio.sleep(0.08)
    await executor.stop()
    await run_task

    m = executor.metrics("dev1")
    assert m is not None
    assert m.poll_ok >= 2


@pytest.mark.asyncio
async def test_executor_stops_gracefully():
    """stop() sets stop_event; tasks complete without hanging."""
    runtime = make_device_runtime(poll_interval=0.01)
    executor = Executor(make_registry(runtime), connect=False, jitter_max=0.0)

    run_task = asyncio.create_task(executor.run())
    await asyncio.sleep(0.03)
    await executor.stop(timeout=2.0)
    await run_task  # should not hang


@pytest.mark.asyncio
async def test_executor_per_device_isolation():
    """Error in dev1 does not stop dev2."""
    from power_sdk.errors import TransportError

    r1 = make_device_runtime("dev1", poll_interval=0.01)
    r1.client.read_group.side_effect = TransportError("boom")
    r2 = make_device_runtime("dev2", poll_interval=0.01)

    executor = Executor(make_registry(r1, r2), connect=False, jitter_max=0.0)
    run_task = asyncio.create_task(executor.run())
    await asyncio.sleep(0.06)
    await executor.stop()
    await run_task

    assert executor.metrics("dev1").poll_error >= 1
    assert executor.metrics("dev2").poll_ok >= 1


@pytest.mark.asyncio
async def test_device_metrics_updated_on_ok():
    runtime = make_device_runtime(poll_interval=0.01)
    executor = Executor(make_registry(runtime), connect=False, jitter_max=0.0)
    run_task = asyncio.create_task(executor.run())
    await asyncio.sleep(0.04)
    await executor.stop()
    await run_task
    m = executor.metrics("dev1")
    assert m.poll_ok >= 1
    assert m.poll_error == 0
    assert m.last_ok_at is not None


@pytest.mark.asyncio
async def test_device_metrics_updated_on_error():
    from power_sdk.errors import TransportError

    runtime = make_device_runtime(poll_interval=0.01)
    runtime.client.read_group.side_effect = TransportError("fail")
    executor = Executor(make_registry(runtime), connect=False, jitter_max=0.0)
    run_task = asyncio.create_task(executor.run())
    await asyncio.sleep(0.04)
    await executor.stop()
    await run_task
    m = executor.metrics("dev1")
    assert m.poll_error >= 1
    assert m.poll_ok == 0
    assert m.last_error_at is not None


def test_snapshot_has_duration_ms():
    runtime = make_device_runtime(poll_interval=0.01)
    snapshot = runtime.poll_once()
    assert snapshot.duration_ms >= 0.0


@pytest.mark.asyncio
async def test_sink_failure_does_not_kill_loop():
    """If sink.write raises, loop continues polling."""

    class BrokenSink:
        async def write(self, snapshot):
            raise RuntimeError("sink broken")

        async def close(self):
            pass

    runtime = make_device_runtime(poll_interval=0.01)
    executor = Executor(
        make_registry(runtime), sink=BrokenSink(), connect=False, jitter_max=0.0
    )
    run_task = asyncio.create_task(executor.run())
    # Use a generous sleep (15x poll_interval) so the assertion holds even
    # under CPU contention when the full suite runs concurrently.
    await asyncio.sleep(0.15)
    await executor.stop()
    await run_task

    # Loop continued despite sink errors
    m = executor.metrics("dev1")
    assert m.poll_ok + m.poll_error >= 2


@pytest.mark.asyncio
async def test_executor_stop_closes_sink_once():
    class TrackingSink:
        def __init__(self) -> None:
            self.closed = 0

        async def write(self, snapshot):
            return None

        async def close(self):
            self.closed += 1

    sink = TrackingSink()
    runtime = make_device_runtime(poll_interval=0.01)
    executor = Executor(
        make_registry(runtime), sink=sink, connect=False, jitter_max=0.0
    )

    run_task = asyncio.create_task(executor.run())
    await asyncio.sleep(0.03)
    await executor.stop()
    await run_task
    await executor.stop()

    assert sink.closed == 1


@pytest.mark.asyncio
async def test_sink_worker_drains_queue_before_exit():
    """All enqueued snapshots are written before sink_worker exits after stop."""

    class CollectingSink:
        def __init__(self) -> None:
            self.received: list = []

        async def write(self, snapshot) -> None:
            self.received.append(snapshot)

        async def close(self) -> None:
            pass

    sink = CollectingSink()
    runtime = make_device_runtime(poll_interval=0.005)
    executor = Executor(
        make_registry(runtime), sink=sink, connect=False, jitter_max=0.0
    )

    run_task = asyncio.create_task(executor.run())
    # Let it poll a few times so the queue has pending snapshots
    await asyncio.sleep(0.04)
    await executor.stop(timeout=2.0)
    await run_task

    # All polls generated snapshots and all were written to the sink
    m = executor.metrics("dev1")
    assert m is not None
    assert (m.poll_ok + m.poll_error) >= 2
    assert len(sink.received) >= 2


@pytest.mark.asyncio
async def test_reconnect_failure_does_not_crash_loop():
    """If disconnect/connect raises during reconnect, the loop continues."""
    from power_sdk.errors import TransportError

    runtime = make_device_runtime(poll_interval=0.01)
    # All polls fail → consecutive_errors increments quickly
    runtime.client.read_group.side_effect = TransportError("io error")
    # Reconnect also fails; contextlib.suppress must absorb this
    runtime.client.disconnect.side_effect = RuntimeError("already closed")
    runtime.client.connect.side_effect = RuntimeError("cannot connect")

    executor = Executor(
        make_registry(runtime),
        connect=True,
        jitter_max=0.0,
        reconnect_after_errors=2,
        reconnect_cooldown_s=0.0,
    )

    run_task = asyncio.create_task(executor.run())
    await asyncio.sleep(0.06)
    await executor.stop(timeout=2.0)
    await run_task

    m = executor.metrics("dev1")
    assert m is not None
    assert m.poll_error >= 1
    assert m.reconnect_attempts >= 1


@pytest.mark.asyncio
async def test_stop_before_run_is_safe():
    runtime = make_device_runtime(poll_interval=0.01)
    executor = Executor(make_registry(runtime), connect=False, jitter_max=0.0)
    await executor.stop()


@pytest.mark.asyncio
async def test_executor_double_run_raises():
    """Calling run() while already running must raise RuntimeError."""
    runtime = make_device_runtime(poll_interval=0.5)
    executor = Executor(make_registry(runtime), connect=False, jitter_max=0.0)

    run_task = asyncio.create_task(executor.run())
    await asyncio.sleep(0.01)  # let run() get underway

    with pytest.raises(RuntimeError, match="already running"):
        await executor.run()

    await executor.stop(timeout=2.0)
    await run_task


@pytest.mark.asyncio
async def test_executor_run_after_stop_is_allowed():
    """run() after a completed stop() must NOT raise (stop resets running state)."""
    runtime = make_device_runtime(poll_interval=0.5)
    executor = Executor(make_registry(runtime), connect=False, jitter_max=0.0)

    run_task = asyncio.create_task(executor.run())
    await asyncio.sleep(0.01)
    await executor.stop(timeout=2.0)
    await run_task

    # Second run must succeed (running flag was reset in finally)
    run_task2 = asyncio.create_task(executor.run())
    await asyncio.sleep(0.01)
    await executor.stop(timeout=2.0)
    await run_task2


# ---------------------------------------------------------------------------
# Bug-fix regression tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stop_closes_sink_only_after_sink_worker_exits():
    """sink.close() must not be called while the sink worker is still active.

    If the sink worker is cancelled mid-drain and sink.close() races against
    an in-progress write, data corruption or assertion errors can occur.
    This test verifies that close() is called only after the sink worker task
    has fully exited (observed via ordering of close_called vs write_called).
    """
    close_order: list[str] = []

    class OrderTrackingSink:
        def __init__(self) -> None:
            self.active_write = False

        async def write(self, snapshot) -> None:
            self.active_write = True
            await asyncio.sleep(0)  # yield to allow other tasks to run
            close_order.append("write")
            self.active_write = False

        async def close(self) -> None:
            # If active_write is True here, sink.close() raced a write.
            assert not self.active_write, "close() called while write() was active"
            close_order.append("close")

    sink = OrderTrackingSink()
    runtime = make_device_runtime(poll_interval=0.005)
    executor = Executor(
        make_registry(runtime), sink=sink, connect=False, jitter_max=0.0
    )

    run_task = asyncio.create_task(executor.run())
    await asyncio.sleep(0.04)
    await executor.stop(timeout=2.0)
    await run_task

    # close must appear after at least one write, and active_write must never
    # have been True when close() ran (asserted inside close()).
    assert "close" in close_order
    last_close = max(i for i, v in enumerate(close_order) if v == "close")
    last_write = max((i for i, v in enumerate(close_order) if v == "write"), default=-1)
    assert last_close > last_write, (
        f"close() at position {last_close} must come after last write at {last_write}"
    )


@pytest.mark.asyncio
async def test_sink_drain_cancelled_error_is_reraised():
    """CancelledError in the drain phase must propagate (not be swallowed).

    The drain loop uses `except asyncio.CancelledError` explicitly because
    CancelledError inherits from BaseException (Python 3.8+), not Exception.
    A plain `except Exception` would silently swallow it, leaving the task in
    a wrong state.  This test verifies the task is correctly marked cancelled.

    We simulate the scenario by cancelling the sink worker while it is inside
    a slow `sink.write()` call — CancelledError must propagate out unchanged.
    """
    from power_sdk.runtime.device import DeviceSnapshot
    from power_sdk.runtime.loop import _sink_worker

    class SlowSink:
        """Sink whose write() blocks long enough to receive a cancellation."""

        async def write(self, snapshot) -> None:
            await asyncio.sleep(0.2)  # outlasts the 0.05s cancellation delay

        async def close(self) -> None:
            pass

    q: asyncio.Queue = asyncio.Queue()
    stop_event = asyncio.Event()

    snapshot = DeviceSnapshot(
        device_id="dev1", model="M", timestamp=0.0, state={}, blocks_read=0
    )
    q.put_nowait(snapshot)
    # stop_event NOT set yet — outer while runs and calls sink.write(snapshot)

    sink = SlowSink()
    task = asyncio.create_task(_sink_worker("dev1", q, sink, stop_event))

    # Let the task enter sink.write() (which sleeps 0.2s), then cancel it.
    await asyncio.sleep(0.05)
    task.cancel()

    # The task must propagate CancelledError — it must NOT be swallowed.
    with pytest.raises(asyncio.CancelledError):
        await task

    assert task.cancelled(), "Task must be in cancelled state after CancelledError"


@pytest.mark.asyncio
async def test_poll_once_timeout_produces_error_snapshot():
    """When poll_once hangs beyond poll_timeout, an error snapshot is produced.

    asyncio.to_thread() cannot be cancelled mid-execution; wait_for() is used
    to impose a deadline.  The resulting snapshot must have ok=False and an
    error message describing the timeout.

    We test this by patching asyncio.wait_for (as seen by the loop module) so
    that it raises TimeoutError immediately for the poll_once call, then verify
    that the device loop converts that into an error snapshot.
    """
    from unittest.mock import patch

    from power_sdk.runtime.loop import DeviceMetrics, _device_loop

    runtime = make_device_runtime(poll_interval=0.01)

    q: asyncio.Queue = asyncio.Queue(maxsize=10)
    stop_event = asyncio.Event()
    metrics = DeviceMetrics(device_id="dev1")

    original_wait_for = asyncio.wait_for
    call_count = 0

    async def _patched_wait_for(coro, timeout):
        nonlocal call_count
        call_count += 1
        # First call is the poll_once to_thread — make it time out.
        # Subsequent calls (interval wait, stop_event.wait) use real wait_for.
        if call_count == 1 and timeout > 1.0:
            coro.close()  # cleanly close the coroutine/thread-wrapper
            raise asyncio.TimeoutError()
        return await original_wait_for(coro, timeout)

    target = "power_sdk.runtime.loop.asyncio.wait_for"
    with patch(target, side_effect=_patched_wait_for):
        loop_task = asyncio.create_task(
            _device_loop(
                runtime,
                metrics,
                stop_event,
                q,
                connect=False,
                jitter_max=0.0,
                drop_policy="drop_oldest",
                reconnect_after_errors=0,
                reconnect_cooldown_s=0.0,
            )
        )
        await asyncio.sleep(0.05)
        stop_event.set()
        await loop_task

    # The queue must contain at least one timeout error snapshot.
    assert not q.empty(), "Expected at least one timeout error snapshot in queue"
    snap = q.get_nowait()
    assert not snap.ok, "Timeout snapshot must have ok=False"
    assert snap.error is not None
    assert "timed out" in str(snap.error).lower()


@pytest.mark.asyncio
async def test_timeout_snapshot_uses_wall_clock_timestamp():
    """Regression: timeout snapshot must carry a Unix wall-clock timestamp.

    time.monotonic() returns seconds since OS boot (~tens of thousands),
    whereas time.time() returns Unix epoch seconds (~1.7 billion).
    Consumers such as JsonlSink and MetricsSink rely on Unix timestamps.
    """
    from unittest.mock import patch as _patch

    from power_sdk.runtime.loop import DeviceMetrics, _device_loop

    runtime = make_device_runtime(poll_interval=0.01)
    q: asyncio.Queue = asyncio.Queue(maxsize=10)
    stop_event = asyncio.Event()
    metrics = DeviceMetrics(device_id="dev1")

    original_wait_for = asyncio.wait_for
    call_count = 0

    async def _patched_wait_for(coro, timeout):
        nonlocal call_count
        call_count += 1
        if call_count == 1 and timeout > 1.0:
            coro.close()
            raise asyncio.TimeoutError()
        return await original_wait_for(coro, timeout)

    target = "power_sdk.runtime.loop.asyncio.wait_for"
    with _patch(target, side_effect=_patched_wait_for):
        loop_task = asyncio.create_task(
            _device_loop(
                runtime,
                metrics,
                stop_event,
                q,
                connect=False,
                jitter_max=0.0,
                drop_policy="drop_oldest",
                reconnect_after_errors=0,
                reconnect_cooldown_s=0.0,
            )
        )
        await asyncio.sleep(0.05)
        stop_event.set()
        await loop_task

    assert not q.empty(), "Expected timeout error snapshot in queue"
    snap = q.get_nowait()
    # Unix timestamp is always > 1 billion; monotonic (seconds since boot) is not.
    assert snap.timestamp > 1_000_000_000, (
        f"Expected Unix wall-clock timestamp (>1e9), got {snap.timestamp!r}; "
        "likely time.monotonic() was used instead of time.time()"
    )


@pytest.mark.asyncio
async def test_sink_worker_exception_is_logged_as_error(caplog):
    """Regression: unexpected exception in _sink_worker must be logged as ERROR.

    Previously asyncio.gather(*sink_tasks, return_exceptions=True) discarded
    results without inspection.  Now exceptions are logged so they are not lost.
    """
    import logging

    class ExplodingSink:
        """Sink that raises an unexpected exception on first write."""

        _count = 0

        async def write(self, snapshot) -> None:
            self._count += 1
            if self._count == 1:
                raise RuntimeError("unexpected sink failure")

        async def close(self) -> None:
            pass

    runtime = make_device_runtime(poll_interval=0.01)
    sink = ExplodingSink()

    with caplog.at_level(logging.WARNING, logger="power_sdk.runtime.loop"):
        executor = Executor(
            make_registry(runtime), sink=sink, connect=False, jitter_max=0.0
        )
        run_task = asyncio.create_task(executor.run())
        await asyncio.sleep(0.06)
        await executor.stop()
        await run_task

    # The loop must have continued despite the sink error (warning from _sink_worker)
    m = executor.metrics("dev1")
    assert m is not None
    assert m.poll_ok + m.poll_error >= 2

    assert any(
        record.levelno == logging.ERROR and "sink" in record.message.lower()
        for record in caplog.records
    ), "Expected ERROR-level log for sink exception"
