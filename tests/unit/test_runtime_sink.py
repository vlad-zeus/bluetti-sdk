"""Tests for Sink implementations."""
from __future__ import annotations

import asyncio
import json

import pytest
from power_sdk.runtime import CompositeSink, DeviceSnapshot, JsonlSink, MemorySink


def _make_snapshot(device_id: str = "dev1", ok: bool = True) -> DeviceSnapshot:
    from power_sdk.errors import TransportError
    return DeviceSnapshot(
        device_id=device_id,
        model="M",
        timestamp=1000.0,
        state={"v": 42},
        blocks_read=1,
        duration_ms=10.0,
        error=None if ok else TransportError("fail"),
    )


@pytest.mark.asyncio
async def test_memory_sink_stores_snapshot():
    sink = MemorySink()
    s = _make_snapshot()
    await sink.write(s)
    assert sink.last("dev1") is s


@pytest.mark.asyncio
async def test_memory_sink_respects_maxlen():
    sink = MemorySink(maxlen=5)
    for _i in range(10):
        await sink.write(_make_snapshot())
    assert len(sink.history("dev1")) == 5


@pytest.mark.asyncio
async def test_memory_sink_per_device_isolation():
    sink = MemorySink()
    await sink.write(_make_snapshot("dev1"))
    await sink.write(_make_snapshot("dev2"))
    assert sink.last("dev1") is not None
    assert sink.last("dev2") is not None
    assert sink.last("dev1").device_id == "dev1"
    assert sink.last("dev2").device_id == "dev2"


@pytest.mark.asyncio
async def test_memory_sink_ok_error_counts():
    sink = MemorySink()
    await sink.write(_make_snapshot(ok=True))
    await sink.write(_make_snapshot(ok=True))
    await sink.write(_make_snapshot(ok=False))
    assert sink.ok_count("dev1") == 2
    assert sink.error_count("dev1") == 1


@pytest.mark.asyncio
async def test_memory_sink_all_last():
    sink = MemorySink()
    await sink.write(_make_snapshot("d1"))
    await sink.write(_make_snapshot("d2"))
    all_last = sink.all_last()
    assert set(all_last.keys()) == {"d1", "d2"}


@pytest.mark.asyncio
async def test_jsonl_sink_writes_valid_json(tmp_path):
    path = tmp_path / "out.jsonl"
    sink = JsonlSink(path)
    await sink.write(_make_snapshot())
    await sink.write(_make_snapshot(ok=False))
    lines = path.read_text().strip().splitlines()
    assert len(lines) == 2
    for line in lines:
        obj = json.loads(line)
        assert "device_id" in obj
        assert "timestamp" in obj
        assert "ok" in obj


@pytest.mark.asyncio
async def test_jsonl_sink_error_snapshot(tmp_path):
    path = tmp_path / "errors.jsonl"
    sink = JsonlSink(path)
    await sink.write(_make_snapshot(ok=False))
    obj = json.loads(path.read_text().strip())
    assert obj["ok"] is False
    assert obj["error"] is not None
    assert isinstance(obj["error"], str)


@pytest.mark.asyncio
async def test_composite_sink_fans_out():
    received: list[str] = []

    class TrackingSink:
        def __init__(self, name: str):
            self.name = name
        async def write(self, snapshot: DeviceSnapshot) -> None:
            received.append(self.name)
        async def close(self) -> None:
            pass

    sink = CompositeSink(TrackingSink("A"), TrackingSink("B"))
    await sink.write(_make_snapshot())
    assert received == ["A", "B"]


@pytest.mark.asyncio
async def test_jsonl_sink_thread_safety(tmp_path):
    """Concurrent writes from multiple async tasks must not interleave lines."""
    path = tmp_path / "concurrent.jsonl"
    sink = JsonlSink(path)

    async def write_many() -> None:
        for _ in range(20):
            await sink.write(_make_snapshot())

    await asyncio.gather(write_many(), write_many(), write_many())
    lines = path.read_text().strip().splitlines()
    assert len(lines) == 60
    for line in lines:
        json.loads(line)  # each line must be valid JSON
