"""Push-mode callback adapter — bridges transport events to DeviceSnapshots.

Transport plugins call PushCallbackAdapter.on_data(raw) from any thread when
the device publishes data.  The adapter decodes the payload, wraps it in a
DeviceSnapshot, and schedules enqueueing on the asyncio event loop via
call_soon_threadsafe — keeping all queue access on the event loop thread.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Callable

from .device import DeviceRuntime, DeviceSnapshot

logger = logging.getLogger(__name__)


class PushCallbackAdapter:
    """Thread-safe bridge: transport push callback → DeviceSnapshot → async queue.

    Usage::

        # Created by Executor for each push-mode device.
        adapter = PushCallbackAdapter(runtime, metrics, queue, loop)

        # Transport plugin wires the callback (transport-specific):
        transport.set_on_data(adapter.on_data)

        # When the device publishes, the adapter automatically:
        #   1. Decodes raw payload via decode_fn
        #   2. Creates DeviceSnapshot
        #   3. Schedules enqueue on the event loop thread
        #   4. Updates DeviceMetrics

    Args:
        runtime: DeviceRuntime owning this adapter.
        metrics: DeviceMetrics to update on each push event.
        queue: Per-device bounded asyncio.Queue shared with sink worker.
        loop: The running event loop to schedule on.
        decode_fn: Optional callable(raw) → state dict. Defaults to passthrough.
        drop_policy: ``"drop_oldest"`` (default) or ``"drop_new"``.
    """

    def __init__(
        self,
        runtime: DeviceRuntime,
        metrics: Any,  # DeviceMetrics — runtime type; TYPE_CHECKING import above
        queue: asyncio.Queue,  # type: ignore[type-arg]
        loop: asyncio.AbstractEventLoop,
        *,
        decode_fn: Callable[[Any], dict[str, Any]] | None = None,
        drop_policy: str = "drop_oldest",
    ) -> None:
        self._runtime = runtime
        self._metrics = metrics
        self._queue = queue
        self._loop = loop
        self._decode_fn: Callable[[Any], dict[str, Any]] = (
            decode_fn if decode_fn is not None else _default_decode
        )
        self._drop_policy = drop_policy

    @property
    def device_id(self) -> str:
        """Device ID this adapter is bound to."""
        return self._runtime.device_id

    def on_data(self, raw: Any) -> None:
        """Feed raw push data. Thread-safe; may be called from any thread.

        Converts *raw* to a DeviceSnapshot via decode_fn and schedules it
        to be enqueued into the device's queue on the event loop thread.
        Errors in decode_fn are captured into an error snapshot (not raised).
        """
        t = time.time()
        t0 = time.monotonic()
        try:
            state = self._decode_fn(raw)
            snapshot = DeviceSnapshot(
                device_id=self._runtime.device_id,
                model=self._runtime.client.profile.model,
                timestamp=t,
                state=state,
                blocks_read=1,
                duration_ms=(time.monotonic() - t0) * 1000.0,
            )
        except Exception as exc:
            logger.warning(
                "[%s] push decode failed: %s: %s",
                self._runtime.device_id,
                type(exc).__name__,
                exc,
            )
            snapshot = DeviceSnapshot(
                device_id=self._runtime.device_id,
                model=self._runtime.client.profile.model,
                timestamp=t,
                state={},
                blocks_read=0,
                duration_ms=(time.monotonic() - t0) * 1000.0,
                error=exc,
            )
        try:
            self._loop.call_soon_threadsafe(self._enqueue, snapshot)
        except RuntimeError:
            logger.warning(
                "[%s] push: event loop closed/stopped, dropping snapshot",
                self._runtime.device_id,
            )

    # ------------------------------------------------------------------
    # Private — runs in event loop thread via call_soon_threadsafe
    # ------------------------------------------------------------------

    def _enqueue(self, snapshot: DeviceSnapshot) -> None:
        """Enqueue snapshot and update metrics. Runs in the event loop thread."""
        self._metrics.record(snapshot)
        if self._drop_policy == "drop_oldest":
            if self._queue.full():
                try:
                    self._queue.get_nowait()
                    self._metrics.dropped_snapshots += 1
                except asyncio.QueueEmpty:
                    pass
            self._queue.put_nowait(snapshot)
        else:  # drop_new
            try:
                self._queue.put_nowait(snapshot)
            except asyncio.QueueFull:
                self._metrics.dropped_snapshots += 1


def _default_decode(raw: Any) -> dict[str, Any]:
    """Default push decoder: pass through dict; wrap other types."""
    if isinstance(raw, dict):
        return raw
    return {"data": raw}
