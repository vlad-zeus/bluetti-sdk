"""Tests for Executor reconnect policy and consecutive_errors metric."""

from __future__ import annotations

import asyncio

import pytest
from power_sdk.errors import TransportError
from power_sdk.runtime import Executor

from tests.helpers import make_device_runtime, make_registry

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_reconnect_triggered_after_threshold() -> None:
    """After N consecutive errors, Executor reconnects the device."""
    runtime = make_device_runtime(poll_interval=0.01)
    runtime.client.read_group.side_effect = TransportError("fail")

    executor = Executor(
        make_registry(runtime),
        connect=True,
        jitter_max=0.0,
        reconnect_after_errors=3,
        reconnect_cooldown_s=0.0,  # no cooldown — allow immediate reconnects
    )
    run_task = asyncio.create_task(executor.run())
    await asyncio.sleep(0.15)
    await executor.stop()
    await run_task

    m = executor.metrics("dev1")
    assert m is not None
    assert m.reconnect_attempts >= 1
    # disconnect+connect_once called at least once each for reconnect
    assert runtime.client.disconnect.call_count >= 1
    assert runtime.client.connect_once.call_count >= 1


@pytest.mark.asyncio
async def test_reconnect_cooldown_respected() -> None:
    """With a long cooldown, at most 1 reconnect fires in a short window."""
    runtime = make_device_runtime(poll_interval=0.01)
    runtime.client.read_group.side_effect = TransportError("fail")

    executor = Executor(
        make_registry(runtime),
        connect=True,
        jitter_max=0.0,
        reconnect_after_errors=2,
        reconnect_cooldown_s=10.0,  # longer than our test window
    )
    run_task = asyncio.create_task(executor.run())
    await asyncio.sleep(0.10)
    await executor.stop()
    await run_task

    m = executor.metrics("dev1")
    assert m is not None
    # Cooldown of 10s means at most 1 reconnect in 100ms
    assert m.reconnect_attempts <= 1


@pytest.mark.asyncio
async def test_consecutive_errors_reset_on_success() -> None:
    """consecutive_errors counter resets to 0 after a successful poll."""
    runtime = make_device_runtime(poll_interval=0.01)
    call_count = 0

    def side_effect(*args: object, **kwargs: object) -> list:
        nonlocal call_count
        call_count += 1
        if call_count <= 3:
            raise TransportError("fail")
        return []  # success

    runtime.client.read_group.side_effect = side_effect

    executor = Executor(
        make_registry(runtime),
        connect=False,
        jitter_max=0.0,
        reconnect_after_errors=0,  # disable reconnect — test metrics only
    )
    run_task = asyncio.create_task(executor.run())
    # Allow enough polls for 3 errors + at least 1 success
    await asyncio.sleep(0.12)
    await executor.stop()
    await run_task

    m = executor.metrics("dev1")
    assert m is not None
    assert m.poll_ok >= 1
    assert m.poll_error >= 3
    # After the first successful poll, consecutive_errors resets
    assert m.consecutive_errors == 0


@pytest.mark.asyncio
async def test_consecutive_errors_increments_per_error() -> None:
    """consecutive_errors increments with each error."""
    runtime = make_device_runtime(poll_interval=0.01)
    runtime.client.read_group.side_effect = TransportError("fail")

    executor = Executor(
        make_registry(runtime),
        connect=False,
        jitter_max=0.0,
        reconnect_after_errors=0,  # disable reconnect
    )
    run_task = asyncio.create_task(executor.run())
    await asyncio.sleep(0.05)
    await executor.stop()
    await run_task

    m = executor.metrics("dev1")
    assert m is not None
    assert m.consecutive_errors >= 1
    assert m.poll_error >= 1


@pytest.mark.asyncio
async def test_last_snapshot_at_set_on_poll() -> None:
    """last_snapshot_at is set after the first poll cycle."""
    runtime = make_device_runtime(poll_interval=0.01)
    executor = Executor(make_registry(runtime), connect=False, jitter_max=0.0)
    run_task = asyncio.create_task(executor.run())
    await asyncio.sleep(0.04)
    await executor.stop()
    await run_task

    m = executor.metrics("dev1")
    assert m is not None
    assert m.last_snapshot_at is not None
    assert m.last_snapshot_at > 0.0


@pytest.mark.asyncio
async def test_no_reconnect_when_connect_false() -> None:
    """Reconnect does not fire when connect=False even after many errors."""
    runtime = make_device_runtime(poll_interval=0.01)
    runtime.client.read_group.side_effect = TransportError("fail")

    executor = Executor(
        make_registry(runtime),
        connect=False,  # reconnect guard requires connect=True
        jitter_max=0.0,
        reconnect_after_errors=2,
        reconnect_cooldown_s=0.0,
    )
    run_task = asyncio.create_task(executor.run())
    await asyncio.sleep(0.08)
    await executor.stop()
    await run_task

    m = executor.metrics("dev1")
    assert m is not None
    assert m.reconnect_attempts == 0
