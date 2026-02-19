"""Build Sink instances from parsed runtime YAML config.

Resolves the 'sinks' config section into named Sink instances.
Composite sinks are built after their sub-sinks (topological order via
recursive memoisation). Cycle detection must have been run via
validate_runtime_config() before calling build_sinks_from_config().
"""

from __future__ import annotations

from typing import Any

from .config import SinkSpec, parse_sink_specs
from .sink import CompositeSink, JsonlSink, MemorySink, Sink


def build_sinks_from_config(sinks_config: dict[str, Any]) -> dict[str, Sink]:
    """Build all named Sink instances from the raw 'sinks' YAML section.

    Args:
        sinks_config: The raw dict from config["sinks"]. May be empty or None.

    Returns:
        Dict of ``{name: Sink}`` for all declared sinks. Empty dict if the
        config has no sinks section.

    Note:
        ``validate_runtime_config()`` must be called before this to ensure
        all references are valid and no cycles exist.
    """
    if not sinks_config:
        return {}

    specs = parse_sink_specs(sinks_config)
    built: dict[str, Sink] = {}

    def _build(name: str) -> Sink:
        if name in built:
            return built[name]
        spec: SinkSpec = specs[name]
        if spec.type == "memory":
            sink: Sink = MemorySink(maxlen=spec.maxlen)
        elif spec.type == "jsonl":
            sink = JsonlSink(path=spec.path)
        elif spec.type == "composite":
            sub_sinks = [_build(sub) for sub in spec.sub_sinks]
            sink = CompositeSink(*sub_sinks)
        else:
            raise ValueError(f"Unknown sink type: {spec.type!r}")
        built[name] = sink
        return sink

    for name in specs:
        _build(name)

    return built
