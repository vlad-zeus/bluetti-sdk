"""RuntimeRegistry — manages N DeviceRuntime instances from YAML config."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

from ..bootstrap import build_client_from_entry, load_config
from ..plugins.registry import PluginRegistry, load_plugins
from .device import DeviceRuntime, DeviceSnapshot

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

    def __init__(self, runtimes: list[DeviceRuntime]) -> None:
        self._runtimes: dict[str, DeviceRuntime] = {r.device_id: r for r in runtimes}

    @classmethod
    def from_config(
        cls,
        path: str | Path,
        plugin_registry: PluginRegistry | None = None,
    ) -> RuntimeRegistry:
        """Build N DeviceRuntimes from YAML config.

        Reuses bootstrap.load_config() and build_client_from_entry().
        Stores YAML-context (vendor, protocol, profile_id, transport_key,
        poll_interval) on each DeviceRuntime for dry-run resolution.
        """
        config = load_config(path)
        defaults = config.get("defaults", {})
        devices = config.get("devices", [])
        reg = load_plugins() if plugin_registry is None else plugin_registry

        runtimes: list[DeviceRuntime] = []
        for entry in devices:
            device_id = entry["id"]

            # Resolve YAML-context fields (no I/O, no profile loading yet)
            vendor = _resolve(entry, defaults, "vendor", "")
            protocol = _resolve(entry, defaults, "protocol", "")
            profile_id = entry["profile_id"]

            # Transport key: entry.transport.key > defaults.transport.key > "mqtt"
            entry_transport = entry.get("transport", {})
            defaults_transport = defaults.get("transport", {})
            transport_key = (
                entry_transport.get("key")
                or defaults_transport.get("key")
                or "mqtt"
            )

            # Poll interval: entry > defaults > 30; validate > 0
            raw_interval = _resolve(entry, defaults, "poll_interval", 30)
            try:
                poll_interval = float(raw_interval)
            except (TypeError, ValueError):
                poll_interval = 30.0
            if poll_interval <= 0:
                logger.warning(
                    "Device %r: poll_interval=%r invalid; using 30s",
                    device_id,
                    raw_interval,
                )
                poll_interval = 30.0

            try:
                client = build_client_from_entry(entry, defaults=defaults, registry=reg)
            except Exception as exc:
                # Fail fast on build errors — caller decides how to handle
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
                )
            )

        return cls(runtimes)

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
                )
            )
        return summaries

    def get(self, device_id: str) -> DeviceRuntime | None:
        return self._runtimes.get(device_id)

    def __iter__(self) -> Iterator[DeviceRuntime]:
        return iter(self._runtimes.values())

    def __len__(self) -> int:
        return len(self._runtimes)
