"""Async per-device run loop with graceful shutdown and per-device metrics."""
from __future__ import annotations

import asyncio
import contextlib
import logging
import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from .device import DeviceRuntime, DeviceSnapshot

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

    def record(self, snapshot: DeviceSnapshot) -> None:
        """Update metrics from snapshot."""
        self.last_duration_ms = snapshot.duration_ms
        if snapshot.ok:
            self.poll_ok += 1
            self.last_ok_at = snapshot.timestamp
        else:
            self.poll_error += 1
            self.last_error_at = snapshot.timestamp


# ---------------------------------------------------------------------------
# Internal loop
# ---------------------------------------------------------------------------


async def _device_loop(
    runtime: DeviceRuntime,
    metrics: DeviceMetrics,
    stop_event: asyncio.Event,
    sink: Any,   # Sink protocol — imported at call site to avoid circular import
    *,
    connect: bool,
    jitter_max: float,
) -> None:
    """Run poll_once() in a loop for one device until stop_event is set.

    Jitter: initial random delay capped at min(jitter_max, poll_interval * 0.1).
    Sink failures: logged as WARNING, loop continues.
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
    try:
        while not stop_event.is_set():
            # Connect only on first iteration
            snapshot = await asyncio.to_thread(
                runtime.poll_once,
                connect and first,  # connect arg
                False,              # disconnect arg — we handle disconnect in finally
            )
            first = False
            metrics.record(snapshot)

            # Logging
            if snapshot.ok:
                logger.debug(
                    "[%s] poll_ok blocks=%d duration=%.1fms",
                    runtime.device_id, snapshot.blocks_read, snapshot.duration_ms,
                )
            else:
                logger.warning(
                    "[%s] poll_error %s: %s (duration=%.1fms)",
                    runtime.device_id,
                    type(snapshot.error).__name__,
                    snapshot.error,
                    snapshot.duration_ms,
                )

            # Sink — failures must NOT kill the polling loop
            try:
                await sink.write(snapshot)
            except Exception as exc:
                logger.warning(
                    "[%s] sink.write failed: %s: %s",
                    runtime.device_id,
                    type(exc).__name__,
                    exc,
                )

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

    Per-device poll intervals are taken from each DeviceRuntime.

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
    ) -> None:
        self._registry = registry
        self._sink = sink if sink is not None else _NoOpSink()
        self._connect = connect
        self._jitter_max = jitter_max
        self._metrics: dict[str, DeviceMetrics] = {
            r.device_id: DeviceMetrics(r.device_id) for r in registry
        }
        self._stop_event: asyncio.Event | None = None
        self._tasks: list[asyncio.Task[None]] = []

    def metrics(self, device_id: str) -> DeviceMetrics | None:
        """Return accumulated metrics for a device, or None if unknown."""
        return self._metrics.get(device_id)

    def all_metrics(self) -> list[DeviceMetrics]:
        """Return metrics for all devices."""
        return list(self._metrics.values())

    async def run(self) -> None:
        """Start all device loop tasks and wait for them to complete.

        Returns when stop() is called (all tasks finish gracefully).
        Unexpected task exceptions are logged as ERROR — not raised silently.
        """
        self._stop_event = asyncio.Event()
        self._tasks = [
            asyncio.create_task(
                _device_loop(
                    runtime,
                    self._metrics[runtime.device_id],
                    self._stop_event,
                    self._sink,
                    connect=self._connect,
                    jitter_max=self._jitter_max,
                ),
                name=f"device-loop-{runtime.device_id}",
            )
            for runtime in self._registry
        ]

        results = await asyncio.gather(*self._tasks, return_exceptions=True)

        # Log unexpected exceptions — do not lose them silently
        for runtime, result in zip(self._registry, results):
            if isinstance(result, Exception) and not isinstance(
                result, asyncio.CancelledError
            ):
                logger.error(
                    "Device loop for %r raised unexpected exception: %s: %s",
                    runtime.device_id,
                    type(result).__name__,
                    result,
                )

    async def stop(self, timeout: float = 30.0) -> None:
        """Signal shutdown and wait up to timeout for tasks to complete."""
        if self._stop_event:
            self._stop_event.set()
        if self._tasks:
            _done, pending = await asyncio.wait(self._tasks, timeout=timeout)
            for task in pending:
                logger.warning(
                    "Device loop task did not stop in time; cancelling: %s",
                    task.get_name(),
                )
                task.cancel()

    async def __aenter__(self) -> Executor:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.stop()
