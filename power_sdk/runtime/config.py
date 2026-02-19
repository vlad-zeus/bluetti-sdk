"""Runtime DSL config: SinkSpec definitions and runtime-specific validation.

Validates the runtime YAML config after bootstrap.load_config() has verified
the base structure. Adds:
  - Strict version constraint (only v1 supported)
  - 'sinks' section: type/field validation per sink type
  - Per-device 'sink' reference validation against defined sink names
  - Cycle detection in composite sink references
  - Poll interval > 0 with precise device path in error messages
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

_SINK_TYPES = frozenset({"composite", "jsonl", "memory"})


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
                    f"sinks.{name!r}.maxlen must be a positive integer, "
                    f"got {maxlen!r}"
                )
            spec.maxlen = maxlen
        elif sink_type == "jsonl":
            path = raw.get("path", "")
            if not isinstance(path, str) or not path.strip():
                raise ValueError(
                    f"sinks.{name!r}.path must be a non-empty string"
                )
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
    specs: dict[str, SinkSpec] = {}
    if sinks_raw:
        specs = parse_sink_specs(sinks_raw)
        # Validate composite references and check for cycles
        for name, spec in specs.items():
            if spec.type == "composite":
                for sub in spec.sub_sinks:
                    if sub not in specs:
                        raise ValueError(
                            f"sinks.{name!r} references unknown sink {sub!r}"
                        )
                _detect_cycle(name, specs)

    # Validate defaults.sink reference
    defaults = config.get("defaults", {})
    default_sink = defaults.get("sink")
    if default_sink is not None:
        if not specs:
            raise ValueError(
                f"defaults.sink={default_sink!r} but no 'sinks' section defined"
            )
        if default_sink not in specs:
            raise ValueError(
                f"defaults.sink={default_sink!r} is not defined in 'sinks' section"
            )

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
            raise ValueError(
                f"devices[{idx}].poll_interval must be > 0, got {val}"
            )

        # Per-device sink reference
        dev_sink = entry.get("sink", default_sink)
        if dev_sink is not None:
            if not specs:
                raise ValueError(
                    f"devices[{idx}].sink={dev_sink!r} "
                    "but no 'sinks' section defined"
                )
            if dev_sink not in specs:
                raise ValueError(
                    f"devices[{idx}].sink={dev_sink!r} "
                    "is not defined in 'sinks' section"
                )
