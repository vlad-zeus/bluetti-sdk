"""Runtime DSL config: SinkSpec/PipelineSpec definitions and validation.

Validates the runtime YAML config after bootstrap.load_config() has verified
the base structure. Adds:
  - Strict version constraint (only v1 supported)
  - 'sinks' section: type/field validation per sink type
  - 'pipelines' section: mode, transport, vendor, protocol validation
  - Per-device 'sink' and 'pipeline' reference validation
  - Cycle detection in composite sink references
  - Poll interval > 0 with precise device path in error messages
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .spec import VALID_MODES, PipelineSpec

_SINK_TYPES = frozenset({"composite", "jsonl", "memory"})


# ---------------------------------------------------------------------------
# SinkSpec
# ---------------------------------------------------------------------------


@dataclass
class SinkSpec:
    """Parsed and validated sink specification from YAML."""

    name: str
    type: str  # "memory" | "jsonl" | "composite"
    maxlen: int = 100  # memory: ring-buffer size
    path: str = ""  # jsonl: output file path
    sub_sinks: list[str] = field(default_factory=list)  # composite: child names


def parse_sink_specs(sinks_config: dict[str, Any]) -> dict[str, SinkSpec]:
    """Parse raw 'sinks' YAML section into {name: SinkSpec}.

    Raises ValueError with the full sink path on any invalid spec.
    """
    if not isinstance(sinks_config, dict):
        raise ValueError("'sinks' must be a mapping")
    specs: dict[str, SinkSpec] = {}
    for name, raw in sinks_config.items():
        if not isinstance(raw, dict):
            raise ValueError(
                f"sinks.{name!r} must be a mapping, got {type(raw).__name__}"
            )
        sink_type = raw.get("type")
        if sink_type not in _SINK_TYPES:
            raise ValueError(
                f"sinks.{name!r}.type={sink_type!r} is invalid; "
                f"expected one of {sorted(_SINK_TYPES)}"
            )
        spec = SinkSpec(name=name, type=sink_type)
        if sink_type == "memory":
            maxlen = raw.get("maxlen", 100)
            if not isinstance(maxlen, int) or maxlen <= 0:
                raise ValueError(
                    f"sinks.{name!r}.maxlen must be a positive integer, got {maxlen!r}"
                )
            spec.maxlen = maxlen
        elif sink_type == "jsonl":
            path = raw.get("path", "")
            if not isinstance(path, str) or not path.strip():
                raise ValueError(f"sinks.{name!r}.path must be a non-empty string")
            spec.path = path.strip()
        elif sink_type == "composite":
            sub = raw.get("sinks", [])
            if not isinstance(sub, list) or not sub:
                raise ValueError(
                    f"sinks.{name!r}.sinks must be a non-empty list of sink names"
                )
            spec.sub_sinks = [str(n) for n in sub]
        specs[name] = spec
    return specs


def _detect_cycle(
    name: str,
    specs: dict[str, SinkSpec],
    path: tuple[str, ...] = (),
) -> None:
    """Raise ValueError if composite sink references form a cycle."""
    if name in path:
        cycle = " -> ".join((*path, name))
        raise ValueError(f"Cycle detected in composite sinks: {cycle}")
    if name not in specs or specs[name].type != "composite":
        return
    for sub in specs[name].sub_sinks:
        _detect_cycle(sub, specs, (*path, name))


# ---------------------------------------------------------------------------
# PipelineSpec parsing
# ---------------------------------------------------------------------------


def parse_pipeline_specs(
    pipelines_raw: dict[str, Any],
) -> dict[str, PipelineSpec]:
    """Parse raw 'pipelines:' YAML section into {name: PipelineSpec}.

    Raises ValueError with field-level path info on any invalid spec.
    """
    if not isinstance(pipelines_raw, dict):
        raise ValueError("'pipelines' must be a mapping")
    specs: dict[str, PipelineSpec] = {}
    for name, raw in pipelines_raw.items():
        if not isinstance(raw, dict):
            raise ValueError(
                f"pipelines.{name!r} must be a mapping, got {type(raw).__name__}"
            )
        mode = raw.get("mode", "pull")
        if mode not in VALID_MODES:
            raise ValueError(
                f"pipelines.{name!r}.mode={mode!r} is invalid; "
                f"expected one of {sorted(VALID_MODES)}"
            )
        transport = raw.get("transport", "")
        if not isinstance(transport, str):
            raise ValueError(f"pipelines.{name!r}.transport must be a string")
        vendor = raw.get("vendor", "")
        if not isinstance(vendor, str):
            raise ValueError(f"pipelines.{name!r}.vendor must be a string")
        protocol = raw.get("protocol", "")
        if not isinstance(protocol, str):
            raise ValueError(f"pipelines.{name!r}.protocol must be a string")
        specs[name] = PipelineSpec(
            name=name,
            mode=mode,
            transport=transport,
            vendor=vendor,
            protocol=protocol,
        )
    return specs


# ---------------------------------------------------------------------------
# Full config validation
# ---------------------------------------------------------------------------


def validate_runtime_config(config: dict[str, Any]) -> None:
    """Runtime-specific validation of an already-loaded config dict.

    Call this after bootstrap.load_config() for runtime-specific checks.
    Raises ValueError with field-level path information on any invalid value.
    """
    # Version: only v1 supported
    version = config.get("version", 1)
    if version != 1:
        raise ValueError(
            f"Unsupported runtime config version: {version!r}. "
            "Only version 1 is supported."
        )

    # Parse sinks section (optional)
    sinks_raw = config.get("sinks", {})
    sink_specs: dict[str, SinkSpec] = {}
    if sinks_raw:
        sink_specs = parse_sink_specs(sinks_raw)
        # Validate composite references and check for cycles
        for name, spec in sink_specs.items():
            if spec.type == "composite":
                for sub in spec.sub_sinks:
                    if sub not in sink_specs:
                        raise ValueError(
                            f"sinks.{name!r} references unknown sink {sub!r}"
                        )
                _detect_cycle(name, sink_specs)

    # Validate defaults.sink reference
    defaults = config.get("defaults", {})
    default_sink = defaults.get("sink")
    if default_sink is not None:
        if not sink_specs:
            raise ValueError(
                f"defaults.sink={default_sink!r} but no 'sinks' section defined"
            )
        if default_sink not in sink_specs:
            raise ValueError(
                f"defaults.sink={default_sink!r} is not defined in 'sinks' section"
            )

    # Parse pipelines section (required)
    pipelines_raw = config.get("pipelines")
    if not isinstance(pipelines_raw, dict) or not pipelines_raw:
        raise ValueError("'pipelines' section is required")
    pipeline_specs = parse_pipeline_specs(pipelines_raw)

    # Per-device validation
    devices = config.get("devices", [])
    for idx, entry in enumerate(devices):
        # poll_interval must be a positive number
        raw = entry.get("poll_interval", defaults.get("poll_interval", 30))
        try:
            val = float(raw)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"devices[{idx}].poll_interval must be a number, got {raw!r}"
            ) from exc
        if val <= 0:
            raise ValueError(f"devices[{idx}].poll_interval must be > 0, got {val}")

        # pipeline is required per device
        dev_pipeline = entry.get("pipeline")
        if not dev_pipeline:
            raise ValueError(f"devices[{idx}]: 'pipeline' is required")
        if dev_pipeline not in pipeline_specs:
            raise ValueError(
                f"devices[{idx}].pipeline={dev_pipeline!r} "
                "is not defined in 'pipelines' section"
            )

        # Per-device sink reference
        dev_sink = entry.get("sink", default_sink)
        if dev_sink is not None:
            if not sink_specs:
                raise ValueError(
                    f"devices[{idx}].sink={dev_sink!r} but no 'sinks' section defined"
                )
            if dev_sink not in sink_specs:
                raise ValueError(
                    f"devices[{idx}].sink={dev_sink!r} "
                    "is not defined in 'sinks' section"
                )
