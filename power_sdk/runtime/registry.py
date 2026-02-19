"""RuntimeRegistry — manages N DeviceRuntime instances from YAML config."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

from ..bootstrap import build_client_from_entry, load_config
from ..plugins.registry import PluginRegistry, load_plugins
from .config import validate_runtime_config
from .device import DeviceRuntime, DeviceSnapshot
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


def _resolve(
    entry: dict[str, Any], defaults: dict[str, Any], key: str, default: Any = None
) -> Any:
    """Return entry[key] if present and non-None, else defaults[key], else default."""
    v = entry.get(key)
    if v is not None:
        return v
    return defaults.get(key, default)


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
                raise ValueError(
                    f"Duplicate runtime device_id: {runtime.device_id!r}"
                )
            seen_ids.add(runtime.device_id)
        self._runtimes: dict[str, DeviceRuntime] = {
            r.device_id: r for r in runtimes
        }
        self._sinks: dict[str, Sink] = sinks or {}
        self._device_sinks: dict[str, Sink] = device_sinks or {}

    @classmethod
    def from_config(
        cls,
        path: str | Path,
        plugin_registry: PluginRegistry | None = None,
    ) -> RuntimeRegistry:
        """Build N DeviceRuntimes from YAML config.

        Reuses bootstrap.load_config() and build_client_from_entry().
        Stores YAML-context (vendor, protocol, profile_id, transport_key,
        poll_interval, sink_name) on each DeviceRuntime for dry-run resolution.

        Raises ValueError if the config fails validation.
        """
        config = load_config(path)
        validate_runtime_config(config)

        defaults = config.get("defaults", {})
        devices = config.get("devices", [])
        reg = load_plugins() if plugin_registry is None else plugin_registry

        # Build named sinks from config
        sinks = build_sinks_from_config(config.get("sinks", {}))
        default_sink_name = defaults.get("sink")

        runtimes: list[DeviceRuntime] = []
        device_sinks: dict[str, Sink] = {}

        for entry in devices:
            device_id = entry["id"]

            # Resolve YAML-context fields
            vendor = _resolve(entry, defaults, "vendor", "")
            protocol = _resolve(entry, defaults, "protocol", "")
            profile_id = entry["profile_id"]

            # Transport key: entry.transport.key > defaults.transport.key
            entry_transport = entry.get("transport")
            if entry_transport is not None and not isinstance(entry_transport, dict):
                raise ValueError(
                    f"Device {device_id!r}: transport must be a mapping"
                )
            defaults_transport = defaults.get("transport", {})
            if not isinstance(defaults_transport, dict):
                raise ValueError("'defaults.transport' must be a mapping")

            _et_key = (
                entry_transport.get("key")
                if isinstance(entry_transport, dict)
                else None
            )
            _dt_key = defaults_transport.get("key")
            transport_key = _et_key or _dt_key
            if not isinstance(transport_key, str) or not transport_key.strip():
                raise ValueError(
                    f"Device {device_id!r}: resolved transport.key is missing"
                )

            # Poll interval (validate_runtime_config already ensured > 0)
            raw_interval = _resolve(entry, defaults, "poll_interval", 30)
            try:
                poll_interval = float(raw_interval)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"Device {device_id!r}: invalid poll_interval={raw_interval!r}"
                ) from exc
            if poll_interval <= 0:
                raise ValueError(
                    f"Device {device_id!r}: poll_interval must be > 0"
                )

            # Resolved sink name for this device
            entry_sink = entry.get("sink", default_sink_name)
            if entry_sink and entry_sink in sinks:
                sink_name = entry_sink
                device_sinks[device_id] = sinks[entry_sink]
            elif sinks:
                # sinks configured but no explicit assignment — use first defined
                first_name = next(iter(sinks))
                sink_name = first_name
                device_sinks[device_id] = sinks[first_name]
            else:
                sink_name = "memory"  # default display label (MemorySink fallback)

            try:
                client = build_client_from_entry(entry, defaults=defaults, registry=reg)
            except Exception as exc:
                raise RuntimeError(
                    f"Failed to build client for device {device_id!r}: {exc}"
                ) from exc

            runtimes.append(
                DeviceRuntime(
                    device_id=device_id,
                    client=client,
                    vendor=vendor,
                    protocol=protocol,
                    profile_id=profile_id,
                    transport_key=transport_key,
                    poll_interval=poll_interval,
                    sink_name=sink_name,
                )
            )

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
                        manifest.capabilities.supports_streaming
                        if manifest
                        else False
                    ),
                    sink_name=runtime.sink_name,
                )
            )
        return summaries

    def get(self, device_id: str) -> DeviceRuntime | None:
        return self._runtimes.get(device_id)

    def __iter__(self) -> Iterator[DeviceRuntime]:
        return iter(self._runtimes.values())

    def __len__(self) -> int:
        return len(self._runtimes)
