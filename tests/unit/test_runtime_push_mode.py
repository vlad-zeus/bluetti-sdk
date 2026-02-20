"""Tests for push-mode: PushCallbackAdapter and Executor push dispatch."""

from __future__ import annotations

import asyncio
import time
from unittest.mock import MagicMock, patch

import pytest
from power_sdk.runtime.device import DeviceRuntime, DeviceSnapshot
from power_sdk.runtime.loop import DeviceMetrics, Executor
from power_sdk.runtime.push import PushCallbackAdapter, _default_decode
from power_sdk.runtime.registry import RuntimeRegistry

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_runtime(device_id: str = "dev1", mode: str = "push") -> DeviceRuntime:
    profile = MagicMock()
    profile.model = "MOCK_MODEL"
    client = MagicMock()
    client.profile = profile
    runtime = DeviceRuntime(
        device_id=device_id,
        client=client,
        vendor="test",
        protocol="v1",
        profile_id="MOCK",
        transport_key="mqtt",
        poll_interval=0.05,
        mode=mode,
    )
    return runtime


def _make_adapter(
    runtime: DeviceRuntime | None = None,
    *,
    loop: asyncio.AbstractEventLoop | None = None,
    maxsize: int = 10,
    drop_policy: str = "drop_oldest",
    decode_fn=None,
) -> tuple[PushCallbackAdapter, asyncio.Queue, DeviceMetrics]:
    r = runtime or _make_runtime()
    metrics = DeviceMetrics(device_id=r.device_id)
    queue: asyncio.Queue = asyncio.Queue(maxsize=maxsize)
    lp = loop or asyncio.get_event_loop()
    adapter = PushCallbackAdapter(
        r,
        metrics,
        queue,
        lp,
        decode_fn=decode_fn,
        drop_policy=drop_policy,
    )
    return adapter, queue, metrics


# ---------------------------------------------------------------------------
# _default_decode
# ---------------------------------------------------------------------------


class TestDefaultDecode:
    def test_dict_passed_through(self) -> None:
        data = {"soc": 80}
        assert _default_decode(data) is data

    def test_non_dict_wrapped(self) -> None:
        result = _default_decode(b"\x01\x02")
        assert result == {"data": b"\x01\x02"}

    def test_string_wrapped(self) -> None:
        result = _default_decode("hello")
        assert result == {"data": "hello"}

    def test_none_wrapped(self) -> None:
        result = _default_decode(None)
        assert result == {"data": None}


# ---------------------------------------------------------------------------
# PushCallbackAdapter — on_data
# ---------------------------------------------------------------------------


class TestPushCallbackAdapterOnData:
    @pytest.mark.asyncio
    async def test_on_data_enqueues_snapshot(self) -> None:
        adapter, queue, _ = _make_adapter()
        adapter.on_data({"soc": 75})
        await asyncio.sleep(0)  # allow call_soon_threadsafe to fire
        assert not queue.empty()
        snap = queue.get_nowait()
        assert isinstance(snap, DeviceSnapshot)
        assert snap.state == {"soc": 75}
        assert snap.ok

    @pytest.mark.asyncio
    async def test_on_data_uses_decode_fn(self) -> None:
        def my_decode(raw):
            return {"parsed": raw * 2}

        adapter, queue, _ = _make_adapter(decode_fn=my_decode)
        adapter.on_data(5)
        await asyncio.sleep(0)
        snap = queue.get_nowait()
        assert snap.state == {"parsed": 10}

    @pytest.mark.asyncio
    async def test_on_data_decode_error_creates_error_snapshot(self) -> None:
        def bad_decode(raw):
            raise ValueError("bad payload")

        adapter, queue, _ = _make_adapter(decode_fn=bad_decode)
        adapter.on_data(b"garbage")
        await asyncio.sleep(0)
        snap = queue.get_nowait()
        assert not snap.ok
        assert isinstance(snap.error, ValueError)
        assert snap.state == {}

    @pytest.mark.asyncio
    async def test_on_data_updates_metrics_ok(self) -> None:
        adapter, _, metrics = _make_adapter()
        adapter.on_data({"x": 1})
        await asyncio.sleep(0)
        assert metrics.poll_ok == 1
        assert metrics.poll_error == 0

    @pytest.mark.asyncio
    async def test_on_data_updates_metrics_error(self) -> None:
        def fail(_):
            raise RuntimeError("oops")

        adapter, _, metrics = _make_adapter(decode_fn=fail)
        adapter.on_data("anything")
        await asyncio.sleep(0)
        assert metrics.poll_error == 1
        assert metrics.poll_ok == 0

    @pytest.mark.asyncio
    async def test_on_data_drop_oldest_evicts_head(self) -> None:
        adapter, queue, metrics = _make_adapter(maxsize=2, drop_policy="drop_oldest")
        # Fill the queue first
        snap1 = DeviceSnapshot(
            device_id="dev1",
            model="X",
            timestamp=time.time(),
            state={"n": 1},
            blocks_read=1,
        )
        snap2 = DeviceSnapshot(
            device_id="dev1",
            model="X",
            timestamp=time.time(),
            state={"n": 2},
            blocks_read=1,
        )
        queue.put_nowait(snap1)
        queue.put_nowait(snap2)
        assert queue.full()

        adapter.on_data({"n": 3})
        await asyncio.sleep(0)

        assert metrics.dropped_snapshots == 1
        items = []
        while not queue.empty():
            items.append(queue.get_nowait().state["n"])
        # snap1 was dropped (oldest), snap2 + new are kept
        assert items == [2, 3]

    @pytest.mark.asyncio
    async def test_on_data_drop_new_discards_incoming(self) -> None:
        adapter, queue, metrics = _make_adapter(maxsize=2, drop_policy="drop_new")
        snap1 = DeviceSnapshot(
            device_id="dev1",
            model="X",
            timestamp=time.time(),
            state={"n": 1},
            blocks_read=1,
        )
        snap2 = DeviceSnapshot(
            device_id="dev1",
            model="X",
            timestamp=time.time(),
            state={"n": 2},
            blocks_read=1,
        )
        queue.put_nowait(snap1)
        queue.put_nowait(snap2)

        adapter.on_data({"n": 3})
        await asyncio.sleep(0)

        assert metrics.dropped_snapshots == 1
        items = []
        while not queue.empty():
            items.append(queue.get_nowait().state["n"])
        assert items == [1, 2]  # new item was dropped


# ---------------------------------------------------------------------------
# Executor — push mode dispatch
# ---------------------------------------------------------------------------


def _make_registry(*runtimes: DeviceRuntime) -> RuntimeRegistry:
    return RuntimeRegistry(list(runtimes))


class TestExecutorPushDispatch:
    @pytest.mark.asyncio
    async def test_push_adapter_available_after_run_started(self) -> None:
        """push_adapter() returns adapter for push-mode device after run()."""
        runtime = _make_runtime("dev1", mode="push")
        reg = _make_registry(runtime)

        executor = Executor(reg, connect=False)
        task = asyncio.create_task(executor.run())
        await asyncio.sleep(0.01)

        adapter = executor.push_adapter("dev1")
        assert adapter is not None
        assert adapter.device_id == "dev1"

        await executor.stop()
        await task

    @pytest.mark.asyncio
    async def test_pull_device_has_no_push_adapter(self) -> None:
        """push_adapter() returns None for pull-mode devices."""
        runtime = _make_runtime("dev1", mode="pull")

        with patch.object(runtime.client, "read_group", side_effect=RuntimeError):
            executor = Executor(_make_registry(runtime), connect=False, jitter_max=0.0)
            assert executor.push_adapter("dev1") is None  # before run
            task = asyncio.create_task(executor.run())
            await asyncio.sleep(0.01)
            assert executor.push_adapter("dev1") is None  # during run
            await executor.stop()
            await task

    @pytest.mark.asyncio
    async def test_push_on_data_reaches_sink(self) -> None:
        """Data fed to push adapter ends up in the sink via sink worker."""
        from power_sdk.runtime.sink import MemorySink

        runtime = _make_runtime("dev1", mode="push")
        sink = MemorySink()
        executor = Executor(_make_registry(runtime), sink=sink, connect=False)
        run_task = asyncio.create_task(executor.run())
        await asyncio.sleep(0.01)

        adapter = executor.push_adapter("dev1")
        assert adapter is not None
        adapter.on_data({"power": 100})
        await asyncio.sleep(0.05)

        snap = sink.last("dev1")
        assert snap is not None
        assert snap.state == {"power": 100}

        await executor.stop()
        await run_task

    @pytest.mark.asyncio
    async def test_mixed_pull_push_both_run(self) -> None:
        """Registry with pull + push devices: both tasks are created."""
        pull_rt = _make_runtime("pull_dev", mode="pull")
        push_rt = _make_runtime("push_dev", mode="push")

        with patch.object(pull_rt.client, "read_group", side_effect=RuntimeError):
            executor = Executor(
                _make_registry(pull_rt, push_rt), connect=False, jitter_max=0.0
            )
            task = asyncio.create_task(executor.run())
            await asyncio.sleep(0.02)

            # push adapter only for push device
            assert executor.push_adapter("push_dev") is not None
            assert executor.push_adapter("pull_dev") is None

            # both devices have metrics
            assert executor.metrics("pull_dev") is not None
            assert executor.metrics("push_dev") is not None

            await executor.stop()
            await task
