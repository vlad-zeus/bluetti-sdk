"""Runtime layer — N-device lifecycle and poll orchestration."""
from .config import SinkSpec
from .device import DeviceRuntime, DeviceSnapshot
from .loop import DeviceMetrics, Executor
from .registry import DeviceSummary, RuntimeRegistry
from .sink import CompositeSink, JsonlSink, MemorySink, Sink
from .sink_factory import build_sinks_from_config

__all__ = [
    "CompositeSink",
    "DeviceMetrics",
    "DeviceRuntime",
    "DeviceSnapshot",
    "DeviceSummary",
    "Executor",
    "JsonlSink",
    "MemorySink",
    "RuntimeRegistry",
    "Sink",
    "SinkSpec",
    "build_sinks_from_config",
]
