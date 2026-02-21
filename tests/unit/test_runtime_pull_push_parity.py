"""Parity tests: pull and push modes share the same executor/sink/metrics path."""

from __future__ import annotations

import asyncio

import pytest
from power_sdk.runtime.loop import Executor
from power_sdk.runtime.sink import MemorySink

from tests.helpers import make_device_runtime, make_registry

# ---------------------------------------------------------------------------
# Parity: both modes produce DeviceSnapshots in MemorySink
# ---------------------------------------------------------------------------


class TestPullPushParity:
    @pytest.mark.asyncio
    async def test_pull_device_produces_snapshots_in_sink(self) -> None:
        """Pull device: poll_once returns snapshot → ends up in MemorySink."""
        pull = make_device_runtime("pull_dev", mode="pull")
        pull.client.read_group.return_value = ["block1"]
        pull.client.get_device_state.return_value = {"soc": 90}

        reg = make_registry(pull)
        sink = MemorySink()
        executor = Executor(reg, sink=sink, connect=False, jitter_max=0.0)
        task = asyncio.create_task(executor.run())
        await asyncio.sleep(0.08)
        await executor.stop()
        await task

        snap = sink.last("pull_dev")
        assert snap is not None
        assert snap.ok

    @pytest.mark.asyncio
    async def test_push_device_produces_snapshots_in_sink(self) -> None:
        """Push device: on_data → snapshot → ends up in MemorySink."""
        push = make_device_runtime("push_dev", mode="push")

        reg = make_registry(push)
        sink = MemorySink()
        executor = Executor(reg, sink=sink, connect=False)
        task = asyncio.create_task(executor.run())
        await asyncio.sleep(0.01)

        adapter = executor.push_adapter("push_dev")
        assert adapter is not None
        adapter.on_data({"soc": 55})
        await asyncio.sleep(0.05)

        await executor.stop()
        await task

        snap = sink.last("push_dev")
        assert snap is not None
        assert snap.ok
        assert snap.state == {"soc": 55}

    @pytest.mark.asyncio
    async def test_both_modes_side_by_side(self) -> None:
        """pull + push devices in same registry, both produce snapshots."""
        pull = make_device_runtime("pull_dev", mode="pull")
        pull.client.read_group.return_value = ["b1"]
        pull.client.get_device_state.return_value = {"pull_key": 1}

        push = make_device_runtime("push_dev", mode="push")

        reg = make_registry(pull, push)
        sink = MemorySink()
        executor = Executor(reg, sink=sink, connect=False, jitter_max=0.0)
        task = asyncio.create_task(executor.run())
        await asyncio.sleep(0.05)

        adapter = executor.push_adapter("push_dev")
        assert adapter is not None
        adapter.on_data({"push_key": 99})
        await asyncio.sleep(0.05)

        await executor.stop()
        await task

        pull_snap = sink.last("pull_dev")
        push_snap = sink.last("push_dev")
        assert pull_snap is not None
        assert push_snap is not None
        assert push_snap.state == {"push_key": 99}

    @pytest.mark.asyncio
    async def test_push_metrics_updated(self) -> None:
        """Push adapter updates DeviceMetrics on each on_data call."""
        push = make_device_runtime("push_dev", mode="push")

        reg = make_registry(push)
        executor = Executor(reg, connect=False)
        task = asyncio.create_task(executor.run())
        await asyncio.sleep(0.01)

        adapter = executor.push_adapter("push_dev")
        assert adapter is not None
        adapter.on_data({"x": 1})
        adapter.on_data({"x": 2})
        await asyncio.sleep(0.05)

        await executor.stop()
        await task

        m = executor.metrics("push_dev")
        assert m is not None
        assert m.poll_ok == 2

    @pytest.mark.asyncio
    async def test_stop_works_with_only_push_devices(self) -> None:
        """Executor.stop() completes cleanly when all devices are push-mode."""
        push1 = make_device_runtime("p1", mode="push")
        push2 = make_device_runtime("p2", mode="push")

        reg = make_registry(push1, push2)
        executor = Executor(reg, connect=False)
        task = asyncio.create_task(executor.run())
        await asyncio.sleep(0.01)
        await executor.stop()
        await asyncio.wait_for(task, timeout=2.0)
        # No exception = pass
