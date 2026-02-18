"""Config-driven client bootstrap.

Builds one or more clients from a declarative YAML configuration.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, cast

import yaml

from .client import Client
from power_sdk.plugins.bluetti.v2.profiles import get_device_profile
from .devices.types import DeviceProfile
from .errors import TransportError
from .protocol.factory import ProtocolFactory
from .transport.factory import TransportFactory


def _expand_env_in_obj(value: Any) -> Any:
    """Recursively expand ${VAR} placeholders in nested objects."""
    if isinstance(value, str):
        return os.path.expandvars(value)
    if isinstance(value, dict):
        return {k: _expand_env_in_obj(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand_env_in_obj(v) for v in value]
    return value


def _require_dict(value: Any, key_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"'{key_name}' must be a mapping")
    return value


def load_config(path: str | Path) -> dict[str, Any]:
    """Load and validate devices config YAML."""
    raw = Path(path).read_text(encoding="utf-8")
    data = yaml.safe_load(raw)
    if data is None:
        raise ValueError(f"Empty config: {path}")
    if not isinstance(data, dict):
        raise ValueError("Config root must be a mapping")

    config = cast(dict[str, Any], _expand_env_in_obj(data))
    version = config.get("version", 1)
    if not isinstance(version, int) or version < 1:
        raise ValueError(f"Invalid config version: {version}")

    devices = config.get("devices")
    if not isinstance(devices, list) or not devices:
        raise ValueError("'devices' must be a non-empty list")

    for idx, entry in enumerate(devices):
        if not isinstance(entry, dict):
            raise ValueError(f"devices[{idx}] must be a mapping")
        if not entry.get("id"):
            raise ValueError(f"devices[{idx}].id is required")
        profile = _require_dict(entry.get("profile"), f"devices[{idx}].profile")
        if not profile.get("model"):
            raise ValueError(f"devices[{idx}].profile.model is required")
        if "transport" in entry:
            transport = _require_dict(entry["transport"], f"devices[{idx}].transport")
            if not transport.get("key"):
                raise ValueError(f"devices[{idx}].transport.key is required")
            if "opts" in transport and not isinstance(transport["opts"], dict):
                raise ValueError(f"devices[{idx}].transport.opts must be a mapping")

    if "defaults" in config and not isinstance(config["defaults"], dict):
        raise ValueError("'defaults' must be a mapping")
    if "schedulers" in config and not isinstance(config["schedulers"], dict):
        raise ValueError("'schedulers' must be a mapping")

    return config


def _resolve_transport_cfg(
    entry: dict[str, Any], defaults: dict[str, Any]
) -> tuple[str, dict[str, Any]]:
    default_transport = defaults.get("transport", {})
    if default_transport and not isinstance(default_transport, dict):
        raise ValueError("defaults.transport must be a mapping")

    default_key = default_transport.get("key", "mqtt")
    default_opts = default_transport.get("opts", {})
    if not isinstance(default_opts, dict):
        raise ValueError("defaults.transport.opts must be a mapping")

    entry_transport = entry.get("transport", {})
    if entry_transport and not isinstance(entry_transport, dict):
        raise ValueError("device.transport must be a mapping")

    transport_key = entry_transport.get("key", default_key)
    if not isinstance(transport_key, str) or not transport_key:
        raise ValueError("transport key must be a non-empty string")

    entry_opts = entry_transport.get("opts", {})
    if not isinstance(entry_opts, dict):
        raise ValueError("device.transport.opts must be a mapping")

    transport_opts = {**default_opts, **entry_opts}
    return transport_key, transport_opts


def build_client_from_entry(
    entry: dict[str, Any],
    defaults: dict[str, Any] | None = None,
) -> Client:
    """Build a single client from one device entry."""
    defaults = defaults or {}
    profile_cfg = _require_dict(entry.get("profile"), "profile")
    model = profile_cfg.get("model")
    if not isinstance(model, str) or not model:
        raise ValueError("profile.model must be a non-empty string")

    profile: DeviceProfile = get_device_profile(model)
    protocol_key = (
        profile_cfg.get("protocol")
        or defaults.get("protocol")
        or profile.protocol
    )
    if not isinstance(protocol_key, str) or not protocol_key:
        raise ValueError("profile.protocol must be a non-empty string")

    transport_key, transport_opts = _resolve_transport_cfg(entry, defaults)
    transport = TransportFactory.create(transport_key, **transport_opts)
    protocol = ProtocolFactory.create(protocol_key)

    options = entry.get("options", {})
    if not isinstance(options, dict):
        raise ValueError("device.options must be a mapping")

    device_address_raw = options.get("device_address", 1)
    try:
        device_address = int(device_address_raw)
    except (TypeError, ValueError) as exc:
        raise ValueError("device.options.device_address must be an integer") from exc
    if device_address <= 0:
        raise ValueError("device.options.device_address must be positive")

    return Client(
        transport=transport,
        profile=profile,
        protocol=protocol,
        device_address=device_address,
    )


def build_all_clients(path: str | Path) -> list[tuple[str, Client]]:
    """Build all configured clients from config file."""
    config = load_config(path)
    defaults = config.get("defaults", {})
    devices = config["devices"]

    clients: list[tuple[str, Client]] = []
    for entry in devices:
        device_id = entry["id"]
        try:
            client = build_client_from_entry(entry, defaults=defaults)
        except Exception as exc:
            raise TransportError(
                f"Failed to build client for '{device_id}': {exc}"
            ) from exc
        clients.append((device_id, client))
    return clients

