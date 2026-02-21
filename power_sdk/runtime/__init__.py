"""Runtime layer — N-device lifecycle and poll orchestration."""

from .bridge import BridgeMapper
from .config import SinkSpec
from .device import DeviceRuntime, DeviceSnapshot
from .factory import ResolvedPipeline, StageResolver
from .loop import DeviceMetrics, Executor
from .push import PushCallbackAdapter
from .registry import DeviceSummary, RuntimeRegistry
from .sink import CompositeSink, JsonlSink, MemorySink, Sink
from .sink_factory import build_sinks_from_config
from .spec import PipelineSpec, WritePolicySpec

__all__ = [
    "BridgeMapper",
    "CompositeSink",
    "DeviceMetrics",
    "DeviceRuntime",
    "DeviceSnapshot",
    "DeviceSummary",
    "Executor",
    "JsonlSink",
    "MemorySink",
    "PipelineSpec",
    "PushCallbackAdapter",
    "ResolvedPipeline",
    "RuntimeRegistry",
    "Sink",
    "SinkSpec",
    "StageResolver",
    # Preview API: WritePolicySpec fields are parsed from config but not yet
    # enforced by the runtime pipeline. Setting them has no effect until write
    # command support is implemented. See power_sdk/runtime/spec.py for details.
    "WritePolicySpec",
    "build_sinks_from_config",
]
