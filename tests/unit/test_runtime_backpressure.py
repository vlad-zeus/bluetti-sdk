"""Tests for Executor backpressure queue — drop_oldest and drop_new policies."""
from __future__ import annotations

import asyncio
from unittest.mock import Mock

import pytest
from power_sdk.runtime import DeviceRuntime, Executor, RuntimeRegistry

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_runtime(
    device_id: str = "dev1", poll_interval: float = 0.005
) -> DeviceRuntime:
    client = Mock()
    client.profile.model = "M"
    client.connect = Mock()
    client.disconnect = Mock()
    client.read_group = Mock(return_value=[])
    client.get_device_state = Mock(return_value={})
    return DeviceRuntime(
        device_id=device_id,
        client=client,
        vendor="acme",
        protocol="v1",
        profile_id="DEV1",
        transport_key="stub",
        poll_interval=poll_interval,
    )


def _registry(*runtimes: DeviceRuntime) -> RuntimeRegistry:
    return RuntimeRegistry(list(runtimes))


class _SlowSink:
    """Sink that sleeps on every write, simulating a slow consumer."""

    def __init__(self, delay: float = 2.0) -> None:
        self._delay = delay

    async def write(self, snapshot: object) -> None:
        await asyncio.sleep(self._delay)

    async def close(self) -> None:
        pass


class _BrokenSink:
    """Sink that always raises."""

    async def write(self, snapshot: object) -> None:
        raise RuntimeError("broken")

    async def close(self) -> None:
        pass


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_queue_full_drop_oldest() -> None:
    """With queue_maxsize=2 and a very slow sink, oldest items are dropped."""
    runtime = _make_runtime(poll_interval=0.005)
    executor = Executor(
        _registry(runtime),
        sink=_SlowSink(delay=2.0),
        connect=False,
        jitter_max=0.0,
        queue_maxsize=2,
        drop_policy="drop_oldest",
    )
    run_task = asyncio.create_task(executor.run())
    await asyncio.sleep(0.08)  # ~16 polls at 5ms interval; queue fills immediately
    await executor.stop()
    await run_task

    m = executor.metrics("dev1")
    assert m is not None
    assert m.dropped_snapshots >= 1


@pytest.mark.asyncio
async def test_queue_full_drop_new() -> None:
    """With queue_maxsize=2 and a very slow sink, new items are dropped."""
    runtime = _make_runtime(poll_interval=0.005)
    executor = Executor(
        _registry(runtime),
        sink=_SlowSink(delay=2.0),
        connect=False,
        jitter_max=0.0,
        queue_maxsize=2,
        drop_policy="drop_new",
    )
    run_task = asyncio.create_task(executor.run())
    await asyncio.sleep(0.08)
    await executor.stop()
    await run_task

    m = executor.metrics("dev1")
    assert m is not None
    assert m.dropped_snapshots >= 1


@pytest.mark.asyncio
async def test_sink_slow_consumer_does_not_block_polling() -> None:
    """Polling continues at full speed even when sink is slower than poll_interval."""
    runtime = _make_runtime(poll_interval=0.01)
    executor = Executor(
        _registry(runtime),
        sink=_SlowSink(delay=0.5),  # much slower than 10ms poll_interval
        connect=False,
        jitter_max=0.0,
        queue_maxsize=100,
    )
    run_task = asyncio.create_task(executor.run())
    await asyncio.sleep(0.08)
    await executor.stop()
    await run_task

    m = executor.metrics("dev1")
    assert m is not None
    # At 10ms interval over 80ms, expect >= 4 polls regardless of sink speed
    assert m.poll_ok >= 4


@pytest.mark.asyncio
async def test_sink_failure_loop_continues_with_queue() -> None:
    """Sink errors in _sink_worker do not stop the poll loop."""
    runtime = _make_runtime(poll_interval=0.01)
    executor = Executor(
        _registry(runtime),
        sink=_BrokenSink(),
        connect=False,
        jitter_max=0.0,
        queue_maxsize=50,
    )
    run_task = asyncio.create_task(executor.run())
    await asyncio.sleep(0.06)
    await executor.stop()
    await run_task

    m = executor.metrics("dev1")
    assert m is not None
    assert m.poll_ok >= 2


@pytest.mark.asyncio
async def test_dropped_snapshots_counter_increments() -> None:
    """dropped_snapshots metric reflects actual drops."""
    runtime = _make_runtime(poll_interval=0.001)  # 1ms — very aggressive
    executor = Executor(
        _registry(runtime),
        sink=_SlowSink(delay=5.0),
        connect=False,
        jitter_max=0.0,
        queue_maxsize=1,
        drop_policy="drop_oldest",
    )
    run_task = asyncio.create_task(executor.run())
    await asyncio.sleep(0.05)
    await executor.stop()
    await run_task

    m = executor.metrics("dev1")
    assert m is not None
    # With queue_maxsize=1 and many fast polls, many drops expected
    assert m.dropped_snapshots >= 1
