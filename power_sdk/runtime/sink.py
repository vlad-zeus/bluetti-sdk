"""Sink implementations for DeviceSnapshot post-poll delivery.

All sinks are async-safe. JsonlSink uses threading.Lock for file append.
CompositeSink fans out to multiple sinks. Errors in sinks are NOT
suppressed here — callers (Executor._device_loop) handle logging.
"""

from __future__ import annotations

import asyncio
import threading
from collections import deque
from pathlib import Path
from typing import Protocol, runtime_checkable

from .device import DeviceSnapshot

# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class Sink(Protocol):
    """Post-poll sink contract."""

    async def write(self, snapshot: DeviceSnapshot) -> None:
        """Receive one snapshot after a poll cycle."""
        ...

    async def close(self) -> None:
        """Flush and release resources."""
        ...


# ---------------------------------------------------------------------------
# MemorySink
# ---------------------------------------------------------------------------


class MemorySink:
    """In-memory ring buffer: last N snapshots per device.

    Also provides state persistence queries (last snapshot, ok/error counts).
    Thread-safe: uses asyncio — write() must be awaited from event loop.
    """

    def __init__(self, maxlen: int = 100) -> None:
        self._store: dict[str, deque[DeviceSnapshot]] = {}
        self._maxlen = maxlen

    async def write(self, snapshot: DeviceSnapshot) -> None:
        if snapshot.device_id not in self._store:
            self._store[snapshot.device_id] = deque(maxlen=self._maxlen)
        self._store[snapshot.device_id].append(snapshot)

    async def close(self) -> None:
        pass  # nothing to flush

    def last(self, device_id: str) -> DeviceSnapshot | None:
        """Last snapshot for device, or None if no polls yet."""
        q = self._store.get(device_id)
        return q[-1] if q else None

    def history(self, device_id: str) -> list[DeviceSnapshot]:
        """All retained snapshots for device (oldest first)."""
        return list(self._store.get(device_id, []))

    def all_last(self) -> dict[str, DeviceSnapshot]:
        """Mapping of device_id -> last snapshot for all devices."""
        return {did: q[-1] for did, q in self._store.items() if q}

    def ok_count(self, device_id: str) -> int:
        return sum(1 for s in self._store.get(device_id, []) if s.ok)

    def error_count(self, device_id: str) -> int:
        return sum(1 for s in self._store.get(device_id, []) if not s.ok)


# ---------------------------------------------------------------------------
# JsonlSink
# ---------------------------------------------------------------------------


class JsonlSink:
    """Appends one JSON line per snapshot to a file.

    Thread-safe: threading.Lock prevents line interleaving when multiple
    device loops call _append() concurrently via asyncio.to_thread().
    """

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._lock = threading.Lock()

    async def write(self, snapshot: DeviceSnapshot) -> None:
        import json

        record = {
            "device_id": snapshot.device_id,
            "model": snapshot.model,
            "timestamp": snapshot.timestamp,
            "ok": snapshot.ok,
            "blocks_read": snapshot.blocks_read,
            "duration_ms": snapshot.duration_ms,
            "state": snapshot.state,
            "error": str(snapshot.error) if snapshot.error else None,
        }
        line = json.dumps(record, ensure_ascii=False)
        await asyncio.to_thread(self._append, line)

    def _append(self, line: str) -> None:
        with self._lock, open(self._path, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    async def close(self) -> None:
        pass


# ---------------------------------------------------------------------------
# CompositeSink
# ---------------------------------------------------------------------------


class CompositeSink:
    """Fans out to multiple sinks sequentially.

    If one sink raises, subsequent sinks still receive the snapshot
    (errors are NOT suppressed — caller handles logging).
    """

    def __init__(self, *sinks: Sink) -> None:
        self._sinks = sinks

    async def write(self, snapshot: DeviceSnapshot) -> None:
        errors: list[Exception] = []
        for sink in self._sinks:
            try:
                await sink.write(snapshot)
            except Exception as _sink_exc:
                errors.append(_sink_exc)
        if errors:
            details = "; ".join(f"{type(e).__name__}: {e}" for e in errors)
            agg = RuntimeError(
                f"CompositeSink.write failed in {len(errors)} sink(s): {details}"
            )
            agg.__cause__ = errors[0]
            if len(errors) > 1:
                # __notes__ (PEP 678, Python 3.11+) surfaces additional errors in
                # tracebacks without losing them.
                agg.__notes__ = [
                    f"Additional: {type(e).__name__}: {e}" for e in errors[1:]
                ]
            raise agg

    async def close(self) -> None:
        errors: list[Exception] = []
        for sink in self._sinks:
            try:
                await sink.close()
            except Exception as exc:
                errors.append(exc)
        if errors:
            details = ", ".join(f"{type(err).__name__}: {err}" for err in errors)
            raise RuntimeError(
                f"CompositeSink.close failed in {len(errors)} sink(s): {details}"
            ) from errors[0]
