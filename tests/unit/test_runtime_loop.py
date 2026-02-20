"""Tests for async Executor and per-device loop."""

from __future__ import annotations

import asyncio
from unittest.mock import Mock

import pytest
from power_sdk.runtime import DeviceRuntime, Executor, RuntimeRegistry

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_device_runtime(
    device_id: str = "dev1", poll_interval: float = 0.01
) -> DeviceRuntime:
    client = Mock()
    client.profile.model = "M"
    client.connect = Mock()
    client.disconnect = Mock()
    client.read_group = Mock(return_value=[])
    client.get_device_state = Mock(return_value={"ok": True})
    return DeviceRuntime(
        device_id=device_id,
        client=client,
        vendor="acme",
        protocol="v1",
        profile_id="DEV1",
        transport_key="stub",
        poll_interval=poll_interval,
    )


def _make_registry(*runtimes: DeviceRuntime) -> RuntimeRegistry:
    return RuntimeRegistry(list(runtimes))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_executor_polls_device_multiple_times():
    """With poll_interval=10ms, expect >= 2 polls in 80ms."""
    runtime = _make_device_runtime("dev1", poll_interval=0.01)
    registry = _make_registry(runtime)
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
    runtime = _make_device_runtime(poll_interval=0.01)
    executor = Executor(_make_registry(runtime), connect=False, jitter_max=0.0)

    run_task = asyncio.create_task(executor.run())
    await asyncio.sleep(0.03)
    await executor.stop(timeout=2.0)
    await run_task  # should not hang


@pytest.mark.asyncio
async def test_executor_per_device_isolation():
    """Error in dev1 does not stop dev2."""
    from power_sdk.errors import TransportError

    r1 = _make_device_runtime("dev1", poll_interval=0.01)
    r1.client.read_group.side_effect = TransportError("boom")
    r2 = _make_device_runtime("dev2", poll_interval=0.01)

    executor = Executor(_make_registry(r1, r2), connect=False, jitter_max=0.0)
    run_task = asyncio.create_task(executor.run())
    await asyncio.sleep(0.06)
    await executor.stop()
    await run_task

    assert executor.metrics("dev1").poll_error >= 1
    assert executor.metrics("dev2").poll_ok >= 1


@pytest.mark.asyncio
async def test_device_metrics_updated_on_ok():
    runtime = _make_device_runtime(poll_interval=0.01)
    executor = Executor(_make_registry(runtime), connect=False, jitter_max=0.0)
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

    runtime = _make_device_runtime(poll_interval=0.01)
    runtime.client.read_group.side_effect = TransportError("fail")
    executor = Executor(_make_registry(runtime), connect=False, jitter_max=0.0)
    run_task = asyncio.create_task(executor.run())
    await asyncio.sleep(0.04)
    await executor.stop()
    await run_task
    m = executor.metrics("dev1")
    assert m.poll_error >= 1
    assert m.poll_ok == 0
    assert m.last_error_at is not None


@pytest.mark.asyncio
async def test_snapshot_has_duration_ms():
    runtime = _make_device_runtime(poll_interval=0.01)
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

    runtime = _make_device_runtime(poll_interval=0.01)
    executor = Executor(
        _make_registry(runtime), sink=BrokenSink(), connect=False, jitter_max=0.0
    )
    run_task = asyncio.create_task(executor.run())
    await asyncio.sleep(0.06)
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
    runtime = _make_device_runtime(poll_interval=0.01)
    executor = Executor(
        _make_registry(runtime), sink=sink, connect=False, jitter_max=0.0
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
    runtime = _make_device_runtime(poll_interval=0.005)
    executor = Executor(
        _make_registry(runtime), sink=sink, connect=False, jitter_max=0.0
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

    runtime = _make_device_runtime(poll_interval=0.01)
    # All polls fail → consecutive_errors increments quickly
    runtime.client.read_group.side_effect = TransportError("io error")
    # Reconnect also fails; contextlib.suppress must absorb this
    runtime.client.disconnect.side_effect = RuntimeError("already closed")
    runtime.client.connect.side_effect = RuntimeError("cannot connect")

    executor = Executor(
        _make_registry(runtime),
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
