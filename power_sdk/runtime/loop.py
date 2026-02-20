"""Async per-device run loop with graceful shutdown and per-device metrics."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import random
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from .device import DeviceRuntime, DeviceSnapshot
from .push import PushCallbackAdapter

if TYPE_CHECKING:
    from .registry import RuntimeRegistry

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# DeviceMetrics
# ---------------------------------------------------------------------------


@dataclass
class DeviceMetrics:
    """Accumulated counters for one device's poll history."""

    device_id: str
    poll_ok: int = 0
    poll_error: int = 0
    last_duration_ms: float = 0.0
    last_ok_at: float | None = None
    last_error_at: float | None = None
    # Phase 3 extensions
    dropped_snapshots: int = 0
    consecutive_errors: int = 0
    reconnect_attempts: int = 0
    last_snapshot_at: float | None = None

    def record(self, snapshot: DeviceSnapshot) -> None:
        """Update metrics from snapshot."""
        self.last_duration_ms = snapshot.duration_ms
        self.last_snapshot_at = snapshot.timestamp
        if snapshot.ok:
            self.poll_ok += 1
            self.last_ok_at = snapshot.timestamp
            self.consecutive_errors = 0
        else:
            self.poll_error += 1
            self.last_error_at = snapshot.timestamp
            self.consecutive_errors += 1


# ---------------------------------------------------------------------------
# Queue helpers
# ---------------------------------------------------------------------------


def _enqueue_snapshot(
    queue: asyncio.Queue,  # type: ignore[type-arg]
    snapshot: DeviceSnapshot,
    drop_policy: str,
    metrics: DeviceMetrics,
) -> None:
    """Enqueue snapshot into the per-device bounded queue.

    drop_oldest: discard the head of the queue to make room.
    drop_new: discard incoming snapshot when queue is full.
    """
    if drop_policy == "drop_oldest":
        if queue.full():
            try:
                queue.get_nowait()  # discard oldest — no task_done (not using join)
                metrics.dropped_snapshots += 1
            except asyncio.QueueEmpty:
                pass
        queue.put_nowait(snapshot)
    else:  # "drop_new"
        try:
            queue.put_nowait(snapshot)
        except asyncio.QueueFull:
            metrics.dropped_snapshots += 1


async def _sink_worker(
    device_id: str,
    queue: asyncio.Queue,  # type: ignore[type-arg]
    sink: Any,
    stop_event: asyncio.Event,
) -> None:
    """Drain the per-device queue and write to sink.

    Runs until stop_event is set AND queue is empty.
    Sink errors are logged as WARNING; draining continues.
    """
    while not (stop_event.is_set() and queue.empty()):
        try:
            snapshot = await asyncio.wait_for(queue.get(), timeout=0.05)
        except asyncio.TimeoutError:
            continue
        try:
            await sink.write(snapshot)
        except Exception as exc:
            logger.warning(
                "[%s] sink.write failed: %s: %s",
                device_id,
                type(exc).__name__,
                exc,
            )


# ---------------------------------------------------------------------------
# Internal loop
# ---------------------------------------------------------------------------


async def _device_loop(
    runtime: DeviceRuntime,
    metrics: DeviceMetrics,
    stop_event: asyncio.Event,
    queue: asyncio.Queue,  # type: ignore[type-arg]
    *,
    connect: bool,
    jitter_max: float,
    drop_policy: str,
    reconnect_after_errors: int,
    reconnect_cooldown_s: float,
) -> None:
    """Run poll_once() in a loop for one device until stop_event is set.

    Jitter: initial random delay capped at min(jitter_max, poll_interval * 0.1).
    Snapshots are enqueued (not written directly) — sink worker drains separately.
    Reconnect: triggered after N consecutive errors with a per-device cooldown.
    """
    logger.info(
        "Loop started: %s (interval=%.0fs)", runtime.device_id, runtime.poll_interval
    )

    # Initial jitter to stagger device start times
    jitter = random.uniform(0.0, min(jitter_max, runtime.poll_interval * 0.1))
    if jitter > 0.0:
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=jitter)
            logger.info("Loop cancelled during jitter: %s", runtime.device_id)
            return  # stop requested during jitter
        except asyncio.TimeoutError:
            pass  # normal: jitter elapsed

    first = True
    last_reconnect_at: float = 0.0

    try:
        while not stop_event.is_set():
            # Connect only on first iteration
            snapshot = await asyncio.to_thread(
                runtime.poll_once,
                connect and first,  # connect arg
                False,  # disconnect arg — handled in finally
            )
            first = False
            metrics.record(snapshot)

            # Logging
            if snapshot.ok:
                logger.debug(
                    "[%s] poll_ok blocks=%d duration=%.1fms",
                    runtime.device_id,
                    snapshot.blocks_read,
                    snapshot.duration_ms,
                )
            else:
                logger.warning(
                    "[%s] poll_error %s: %s (duration=%.1fms)",
                    runtime.device_id,
                    type(snapshot.error).__name__,
                    snapshot.error,
                    snapshot.duration_ms,
                )

            # Reconnect after N consecutive errors (only when connect=True)
            if (
                connect
                and reconnect_after_errors > 0
                and metrics.consecutive_errors >= reconnect_after_errors
            ):
                now = time.monotonic()
                if now - last_reconnect_at >= reconnect_cooldown_s:
                    logger.info(
                        "[%s] reconnecting after %d consecutive errors",
                        runtime.device_id,
                        metrics.consecutive_errors,
                    )
                    with contextlib.suppress(Exception):
                        await asyncio.to_thread(runtime.client.disconnect)
                    try:
                        # connect_once: single attempt, no internal sleep —
                        # keeps the thread-pool thread free immediately on
                        # failure; retry cadence is handled by reconnect_cooldown_s
                        await asyncio.to_thread(runtime.client.connect_once)
                    except Exception as _reconnect_exc:
                        logger.warning(
                            "[%s] reconnect attempt %d failed: %s",
                            runtime.device_id,
                            metrics.reconnect_attempts + 1,
                            _reconnect_exc,
                        )
                    metrics.reconnect_attempts += 1
                    # Reset consecutive_errors regardless of success so the next
                    # N errors must accumulate before triggering another reconnect.
                    # Without this reset the counter stays ≥ threshold and the next
                    # poll (if still failing) would immediately re-trigger when the
                    # cooldown elapses — causing rapid-fire reconnect storms.
                    metrics.consecutive_errors = 0
                    last_reconnect_at = now

            # Enqueue snapshot for sink worker — non-blocking
            _enqueue_snapshot(queue, snapshot, drop_policy, metrics)

            # Wait for poll_interval or stop_event
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=runtime.poll_interval)
                break  # stop_event was set
            except asyncio.TimeoutError:
                pass  # interval elapsed — continue loop

    finally:
        # Disconnect on loop exit (connect=True means we opened the connection)
        if connect:
            with contextlib.suppress(Exception):
                await asyncio.to_thread(runtime.client.disconnect)
        logger.info("Loop stopped: %s", runtime.device_id)


# ---------------------------------------------------------------------------
# Push-mode lifecycle loop
# ---------------------------------------------------------------------------


async def _push_loop(
    runtime: DeviceRuntime,
    adapter: PushCallbackAdapter,
    stop_event: asyncio.Event,
    *,
    connect: bool,
) -> None:
    """Push-mode lifecycle manager for one device.

    Connects (if requested), then waits for *stop_event*.
    All data flows in via ``adapter.on_data()`` called by the transport plugin
    — this coroutine only manages the connection lifecycle.
    """
    logger.info("Push loop started: %s", runtime.device_id)
    if connect:
        try:
            await asyncio.to_thread(runtime.client.connect)
        except Exception as exc:
            logger.error(
                "Push loop connect failed for %s: %s: %s",
                runtime.device_id,
                type(exc).__name__,
                exc,
            )
            raise
    try:
        await stop_event.wait()
    finally:
        if connect:
            with contextlib.suppress(Exception):
                await asyncio.to_thread(runtime.client.disconnect)
        logger.info("Push loop stopped: %s", runtime.device_id)


# ---------------------------------------------------------------------------
# _NoOpSink — default when no sink provided
# ---------------------------------------------------------------------------


class _NoOpSink:
    async def write(self, snapshot: DeviceSnapshot) -> None:
        pass

    async def close(self) -> None:
        pass


# ---------------------------------------------------------------------------
# Executor
# ---------------------------------------------------------------------------


class Executor:
    """Manages async per-device poll loops with graceful shutdown.

    Per-device snapshots are enqueued into bounded asyncio.Queues and drained
    by per-device sink worker coroutines. This decouples polling speed from
    sink throughput and provides backpressure control.

    Usage:
        async with Executor(registry, sink=MemorySink()) as executor:
            await executor.run()   # blocks until stop() or Ctrl-C

    Or:
        executor = Executor(registry)
        task = asyncio.create_task(executor.run())
        await asyncio.sleep(5)
        await executor.stop()
        await task
    """

    def __init__(
        self,
        registry: RuntimeRegistry,
        sink: Any | None = None,
        *,
        connect: bool = True,
        jitter_max: float = 5.0,
        queue_maxsize: int = 100,
        drop_policy: str = "drop_oldest",
        reconnect_after_errors: int = 3,
        reconnect_cooldown_s: float = 5.0,
    ) -> None:
        self._registry = registry
        self._fallback_sink = sink if sink is not None else _NoOpSink()
        self._connect = connect
        self._jitter_max = jitter_max
        self._queue_maxsize = queue_maxsize
        self._drop_policy = drop_policy
        self._reconnect_after_errors = reconnect_after_errors
        self._reconnect_cooldown_s = reconnect_cooldown_s
        self._metrics: dict[str, DeviceMetrics] = {
            r.device_id: DeviceMetrics(r.device_id) for r in registry
        }
        self._stop_event: asyncio.Event | None = None
        self._tasks: list[asyncio.Task[None]] = []
        self._sink_tasks: list[asyncio.Task[None]] = []
        self._queues: dict[str, asyncio.Queue] = {}  # type: ignore[type-arg]
        self._push_adapters: dict[str, PushCallbackAdapter] = {}
        self._sink_closed = False
        self._active_sinks: list[Any] = []
        self._running = False

    def metrics(self, device_id: str) -> DeviceMetrics | None:
        """Return accumulated metrics for a device, or None if unknown."""
        return self._metrics.get(device_id)

    def all_metrics(self) -> list[DeviceMetrics]:
        """Return metrics for all devices."""
        return list(self._metrics.values())

    def push_adapter(self, device_id: str) -> PushCallbackAdapter | None:
        """Return the PushCallbackAdapter for a push-mode device, or None.

        Only populated after ``run()`` has been called.  Pull-mode devices
        return None (they do not have a push adapter).
        """
        return self._push_adapters.get(device_id)

    async def run(self) -> None:
        """Start all device loop + sink worker tasks; wait for them to complete.

        Returns when stop() is called (all tasks finish gracefully).
        Unexpected task exceptions are logged as ERROR — not raised silently.

        Raises:
            RuntimeError: If called while already running (double-run guard).
                Create a new Executor or await stop() before calling run() again.
        """
        if self._running:
            raise RuntimeError(
                "Executor.run() is already running; "
                "await stop() before calling run() again"
            )
        self._running = True
        self._sink_closed = False
        self._stop_event = asyncio.Event()
        self._push_adapters = {}

        # Per-device bounded queues — created fresh per run() call
        self._queues = {
            r.device_id: asyncio.Queue(maxsize=self._queue_maxsize)
            for r in self._registry
        }

        # Device tasks — pull uses _device_loop; push uses _push_loop
        loop = asyncio.get_running_loop()
        self._tasks = []
        for runtime in self._registry:
            if runtime.mode == "push":
                adapter = PushCallbackAdapter(
                    runtime,
                    self._metrics[runtime.device_id],
                    self._queues[runtime.device_id],
                    loop,
                    drop_policy=self._drop_policy,
                )
                self._push_adapters[runtime.device_id] = adapter
                task = asyncio.create_task(
                    _push_loop(
                        runtime,
                        adapter,
                        self._stop_event,
                        connect=self._connect,
                    ),
                    name=f"push-loop-{runtime.device_id}",
                )
            else:  # mode == "pull" (default)
                task = asyncio.create_task(
                    _device_loop(
                        runtime,
                        self._metrics[runtime.device_id],
                        self._stop_event,
                        self._queues[runtime.device_id],
                        connect=self._connect,
                        jitter_max=self._jitter_max,
                        drop_policy=self._drop_policy,
                        reconnect_after_errors=self._reconnect_after_errors,
                        reconnect_cooldown_s=self._reconnect_cooldown_s,
                    ),
                    name=f"device-loop-{runtime.device_id}",
                )
            self._tasks.append(task)

        # Sink worker tasks — one per device, drains the queue
        self._active_sinks = []
        self._sink_tasks = []
        for runtime in self._registry:
            sink = self._fallback_sink
            get_sink = getattr(self._registry, "get_sink", None)
            if callable(get_sink):
                configured = get_sink(runtime.device_id)
                if configured is not None:
                    sink = configured
            self._active_sinks.append(sink)
            self._sink_tasks.append(
                asyncio.create_task(
                    _sink_worker(
                        runtime.device_id,
                        self._queues[runtime.device_id],
                        sink,
                        self._stop_event,
                    ),
                    name=f"sink-worker-{runtime.device_id}",
                )
            )

        # Wait for all poll loops to finish
        try:
            poll_results = await asyncio.gather(*self._tasks, return_exceptions=True)

            # Log unexpected exceptions — do not lose them silently
            for runtime, result in zip(self._registry, poll_results):
                if isinstance(result, Exception) and not isinstance(
                    result, asyncio.CancelledError
                ):
                    logger.error(
                        "Device loop for %r raised unexpected exception: %s: %s",
                        runtime.device_id,
                        type(result).__name__,
                        result,
                    )

            # Wait for sink workers to drain remaining queue items
            await asyncio.gather(*self._sink_tasks, return_exceptions=True)
        finally:
            self._running = False

    async def stop(self, timeout: float = 30.0) -> None:
        """Signal shutdown and wait up to timeout for tasks to complete."""
        if self._stop_event:
            self._stop_event.set()
        all_tasks = self._tasks + self._sink_tasks
        if all_tasks:
            _done, pending = await asyncio.wait(all_tasks, timeout=timeout)
            for task in pending:
                logger.warning(
                    "Task did not stop in time; cancelling: %s",
                    task.get_name(),
                )
                task.cancel()
        if not self._sink_closed and self._stop_event is not None:
            closed: set[int] = set()
            for sink in self._active_sinks or [self._fallback_sink]:
                sink_id = id(sink)
                if sink_id in closed:
                    continue
                closed.add(sink_id)
                try:
                    await sink.close()
                except Exception as exc:
                    logger.warning(
                        "Sink close failed: %s: %s",
                        type(exc).__name__,
                        exc,
                    )
            self._sink_closed = True

    async def __aenter__(self) -> Executor:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.stop()
