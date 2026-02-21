"""RuntimeRegistry — manages N DeviceRuntime instances from YAML config."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..bootstrap import build_client_from_entry, load_config, resolve_transport
from ..models.types import BlockGroup
from ..plugins.registry import PluginRegistry, load_plugins
from .config import parse_pipeline_specs, validate_runtime_config
from .device import DeviceRuntime, DeviceSnapshot
from .factory import StageResolver
from .sink import Sink
from .sink_factory import build_sinks_from_config

logger = logging.getLogger(__name__)


@dataclass
class DeviceSummary:
    """Resolved pipeline info per device — used by --dry-run (no I/O)."""

    device_id: str
    vendor: str
    protocol: str
    profile_id: str
    transport_key: str
    poll_interval: float
    can_write: bool
    supports_streaming: bool
    sink_name: str = "memory"
    # Phase 4 pipeline fields
    pipeline_name: str = "direct"
    mode: str = "pull"
    parser: str = "?"
    model: str = "?"


def _resolve(
    entry: dict[str, Any], defaults: dict[str, Any], key: str, default: Any = None
) -> Any:
    """Return entry[key] if present and non-None, else defaults[key], else default."""
    v = entry.get(key)
    if v is not None:
        return v
    return defaults.get(key, default)


def _build_effective_defaults(
    defaults: dict[str, Any],
    pspec: Any,
) -> dict[str, Any]:
    effective_defaults: dict[str, Any] = {**defaults}
    raw_dt = effective_defaults.get("transport")
    if raw_dt is not None and not isinstance(raw_dt, dict):
        raise ValueError("'defaults.transport' must be a mapping")
    if pspec.vendor:
        effective_defaults["vendor"] = pspec.vendor
    if pspec.protocol:
        effective_defaults["protocol"] = pspec.protocol
    if pspec.transport:
        eff_tr = dict(raw_dt or {})
        eff_tr["key"] = pspec.transport
        effective_defaults["transport"] = eff_tr
    return effective_defaults


def _resolve_sink_for_device(
    entry: dict[str, Any],
    default_sink_name: str | None,
    sinks: dict[str, Sink],
    device_id: str,
) -> tuple[str, Sink | None]:
    entry_sink = entry.get("sink", default_sink_name)
    if entry_sink:
        if entry_sink not in sinks:
            raise ValueError(
                f"Device {device_id!r}: sink {entry_sink!r} is not defined "
                "in 'sinks' section"
            )
        return entry_sink, sinks[entry_sink]
    if sinks:
        raise ValueError(
            f"Device {device_id!r}: sinks are configured but no sink is assigned; "
            "set device.sink or defaults.sink"
        )
    return "memory", None


def _resolve_poll_groups(
    entry: dict[str, Any],
    defaults: dict[str, Any],
) -> tuple[BlockGroup, ...]:
    raw = entry.get("poll_groups", defaults.get("poll_groups"))
    if raw is None:
        return (BlockGroup.CORE,)
    if not isinstance(raw, list) or not raw:
        raise ValueError("poll_groups must be a non-empty list")

    groups = []
    for item in raw:
        if not isinstance(item, str):
            raise ValueError("poll_groups entries must be strings")
        try:
            groups.append(BlockGroup(item.lower()))
        except ValueError:
            try:
                groups.append(BlockGroup[item.upper()])
            except KeyError as exc:
                allowed = [g.value for g in BlockGroup]
                raise ValueError(
                    f"Unknown poll_group {item!r}; allowed: {allowed}"
                ) from exc
    return tuple(groups)


def _validate_pipeline_stages(
    pipeline_specs: dict[str, Any],
    devices: list[dict[str, Any]],
    reg: PluginRegistry,
) -> None:
    """Validate stage keys for all referenced pipelines (fail-fast, once per name)."""
    if not pipeline_specs:
        return
    resolver = StageResolver(plugin_registry=reg)
    validated: set[str] = set()
    for entry in devices:
        pname = entry.get("pipeline")
        if pname and pname in pipeline_specs and pname not in validated:
            resolver.validate(pipeline_specs[pname])
            validated.add(pname)


def _build_one_runtime(
    entry: dict[str, Any],
    defaults: dict[str, Any],
    pipeline_specs: dict[str, Any],
    sinks: dict[str, Sink],
    default_sink_name: str | None,
    reg: PluginRegistry,
) -> tuple[DeviceRuntime, Sink | None]:
    """Build a single DeviceRuntime from a device entry and resolved context.

    Returns (runtime, sink_obj) where sink_obj is None when no named sink applies.
    """
    device_id = entry["id"]

    pname: str = entry["pipeline"]  # validate_runtime_config guarantees presence
    pspec = pipeline_specs[pname]
    mode = pspec.mode
    effective_defaults = _build_effective_defaults(defaults, pspec)

    vendor = _resolve(entry, effective_defaults, "vendor", "")
    protocol = _resolve(entry, effective_defaults, "protocol", "")
    profile_id = entry["profile_id"]

    transport_key, _unused_opts = resolve_transport(entry, effective_defaults)
    if not isinstance(transport_key, str) or not transport_key.strip():
        raise ValueError(f"Device {device_id!r}: resolved transport.key is missing")

    poll_interval = float(_resolve(entry, effective_defaults, "poll_interval", 30))

    sink_name, sink_obj = _resolve_sink_for_device(
        entry, default_sink_name, sinks, device_id
    )
    poll_groups = _resolve_poll_groups(entry, effective_defaults)

    try:
        client = build_client_from_entry(
            entry, defaults=effective_defaults, registry=reg
        )
    except Exception as exc:
        raise RuntimeError(
            f"Failed to build client for device {device_id!r}: {exc}"
        ) from exc

    return (
        DeviceRuntime(
            device_id=device_id,
            client=client,
            vendor=vendor,
            protocol=protocol,
            profile_id=profile_id,
            transport_key=transport_key,
            poll_interval=poll_interval,
            sink_name=sink_name,
            pipeline_name=pname,
            mode=mode,
            poll_groups=poll_groups,
        ),
        sink_obj,
    )


class RuntimeRegistry:
    """Manages N DeviceRuntime instances built from a YAML config."""

    def __init__(
        self,
        runtimes: list[DeviceRuntime],
        *,
        sinks: dict[str, Sink] | None = None,
        device_sinks: dict[str, Sink] | None = None,
    ) -> None:
        seen_ids: set[str] = set()
        for runtime in runtimes:
            if runtime.device_id in seen_ids:
                raise ValueError(f"Duplicate runtime device_id: {runtime.device_id!r}")
            seen_ids.add(runtime.device_id)
        self._runtimes: dict[str, DeviceRuntime] = {r.device_id: r for r in runtimes}
        self._sinks: dict[str, Sink] = sinks or {}
        self._device_sinks: dict[str, Sink] = device_sinks or {}

    @classmethod
    def from_config(
        cls,
        path: str | Path,
        plugin_registry: PluginRegistry | None = None,
    ) -> RuntimeRegistry:
        """Build N DeviceRuntimes from YAML config.

        Pipeline-first format is required.
        Referenced pipeline stage keys are validated via StageResolver
        before any client is built.

        Raises ValueError if the config fails validation.
        Raises RuntimeError if client construction fails for a device.
        """
        config = load_config(path)
        validate_runtime_config(config)

        defaults = config.get("defaults", {})
        devices: list[dict[str, Any]] = config.get("devices", [])
        reg = load_plugins() if plugin_registry is None else plugin_registry

        sinks = build_sinks_from_config(config.get("sinks", {}))
        default_sink_name: str | None = defaults.get("sink")
        pipeline_specs = parse_pipeline_specs(config["pipelines"])

        _validate_pipeline_stages(pipeline_specs, devices, reg)

        runtimes: list[DeviceRuntime] = []
        device_sinks: dict[str, Sink] = {}
        for entry in devices:
            runtime, sink_obj = _build_one_runtime(
                entry, defaults, pipeline_specs, sinks, default_sink_name, reg
            )
            runtimes.append(runtime)
            if sink_obj is not None:
                device_sinks[runtime.device_id] = sink_obj

        return cls(runtimes, sinks=sinks, device_sinks=device_sinks)

    def get_sink(self, device_id: str) -> Sink | None:
        """Return the configured Sink for a device, or None if not configured."""
        return self._device_sinks.get(device_id)

    def poll_all_once(
        self,
        connect: bool = False,
        disconnect: bool = False,
    ) -> list[DeviceSnapshot]:
        """Poll every device once. Errors are captured per-device, not raised."""
        return [
            r.poll_once(connect=connect, disconnect=disconnect)
            for r in self._runtimes.values()
        ]

    def dry_run(
        self,
        plugin_registry: PluginRegistry | None = None,
    ) -> list[DeviceSummary]:
        """Return resolved pipeline info per device — no I/O, no connections.

        vendor/protocol taken from DeviceRuntime YAML context (not DeviceProfile).
        """
        reg = load_plugins() if plugin_registry is None else plugin_registry
        summaries: list[DeviceSummary] = []
        for runtime in self._runtimes.values():
            manifest = reg.get(runtime.vendor, runtime.protocol)
            summaries.append(
                DeviceSummary(
                    device_id=runtime.device_id,
                    vendor=runtime.vendor,
                    protocol=runtime.protocol,
                    profile_id=runtime.profile_id,
                    transport_key=runtime.transport_key,
                    poll_interval=runtime.poll_interval,
                    can_write=manifest.can_write() if manifest else False,
                    supports_streaming=(
                        manifest.capabilities.supports_streaming if manifest else False
                    ),
                    sink_name=runtime.sink_name,
                    pipeline_name=runtime.pipeline_name,
                    mode=runtime.mode,
                    parser=manifest.key if manifest else "?",
                    model=manifest.key if manifest else "?",
                )
            )
        return summaries

    def get(self, device_id: str) -> DeviceRuntime | None:
        return self._runtimes.get(device_id)

    def __iter__(self) -> Iterator[DeviceRuntime]:
        return iter(self._runtimes.values())

    def __len__(self) -> int:
        return len(self._runtimes)
