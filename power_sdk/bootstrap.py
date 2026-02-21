"""Internal runtime bootstrap helper. Not public API."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from .client import Client
from .plugins.registry import PluginRegistry, load_plugins
from .transport.factory import TransportFactory


def _expand_env(value: Any) -> Any:
    """Recursively expand ${VAR} placeholders."""
    if isinstance(value, str):
        return os.path.expandvars(value)
    if isinstance(value, dict):
        return {k: _expand_env(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand_env(v) for v in value]
    return value


def _require_str(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{path!r} must be a non-empty string")
    return value


def _resolve(key: str, entry: dict[str, Any], defaults: dict[str, Any]) -> str | None:
    """Resolve a top-level string field from entry, falling back to defaults."""
    v = entry.get(key) or defaults.get(key)
    return v if isinstance(v, str) and v.strip() else None


def load_config(path: str | Path) -> dict[str, Any]:
    """Load, expand env vars, and validate devices config YAML."""
    raw = Path(path).read_text(encoding="utf-8")
    data = yaml.safe_load(raw)
    if data is None:
        raise ValueError(f"Empty config: {path}")
    if not isinstance(data, dict):
        raise ValueError("Config root must be a mapping")

    config: dict[str, Any] = _expand_env(data)

    version = config.get("version", 1)
    if not isinstance(version, int) or version < 1:
        raise ValueError(f"Invalid config version: {version!r}")

    devices = config.get("devices")
    if not isinstance(devices, list) or not devices:
        raise ValueError("'devices' must be a non-empty list")

    defaults = config.get("defaults", {})
    if not isinstance(defaults, dict):
        raise ValueError("'defaults' must be a mapping")

    seen_device_ids: set[str] = set()

    for idx, entry in enumerate(devices):
        if not isinstance(entry, dict):
            raise ValueError(f"devices[{idx}] must be a mapping")
        if not entry.get("id"):
            raise ValueError(f"devices[{idx}].id is required")
        device_id = _require_str(entry.get("id"), f"devices[{idx}].id")
        if device_id in seen_device_ids:
            raise ValueError(f"Duplicate device id: {device_id!r}")
        seen_device_ids.add(device_id)

        # Mandatory fields — resolved from entry or defaults
        vendor = _resolve("vendor", entry, defaults)
        protocol = _resolve("protocol", entry, defaults)
        profile_id = entry.get("profile_id")

        # Pipeline-first format: vendor/protocol/transport.key may come from
        # the referenced pipeline template rather than entry or defaults.
        pipeline_name = entry.get("pipeline")
        pipelines_raw = config.get("pipelines", {})
        if (
            pipeline_name
            and isinstance(pipelines_raw, dict)
            and pipeline_name not in pipelines_raw
        ):
            raise ValueError(
                f"devices[{idx}]: pipeline {pipeline_name!r} not found "
                f"in 'pipelines' section. Available: {list(pipelines_raw)}"
            )
        pipeline_raw = (
            pipelines_raw.get(pipeline_name)
            if isinstance(pipelines_raw, dict) and pipeline_name
            else None
        )
        pipeline_dict: dict[str, Any] = (
            pipeline_raw if isinstance(pipeline_raw, dict) else {}
        )
        has_pipeline = bool(pipeline_dict)

        if not vendor and not (has_pipeline and pipeline_dict.get("vendor")):
            raise ValueError(
                f"devices[{idx}]: 'vendor' is required "
                "(set in entry, defaults.vendor, or pipeline template)"
            )
        if not protocol and not (has_pipeline and pipeline_dict.get("protocol")):
            raise ValueError(
                f"devices[{idx}]: 'protocol' is required "
                "(set in entry, defaults.protocol, or pipeline template)"
            )
        if not isinstance(profile_id, str) or not profile_id.strip():
            raise ValueError(f"devices[{idx}]: 'profile_id' is required")

        # transport.key
        entry_transport = entry.get("transport", {})
        default_transport = defaults.get("transport", {})
        _et_key = (
            entry_transport.get("key") if isinstance(entry_transport, dict) else None
        )
        _dt_key = (
            default_transport.get("key")
            if isinstance(default_transport, dict)
            else None
        )
        _pipeline_transport = pipeline_dict.get("transport")
        transport_key = (
            _et_key
            or _dt_key
            or (_pipeline_transport if isinstance(_pipeline_transport, str) else None)
        )
        if not isinstance(transport_key, str) or not transport_key.strip():
            raise ValueError(
                f"devices[{idx}]: 'transport.key' is required "
                "(set in entry.transport.key, defaults.transport.key, "
                "or pipeline template)"
            )

        if "transport" in entry:
            if not isinstance(entry["transport"], dict):
                raise ValueError(f"devices[{idx}].transport must be a mapping")
            opts = entry["transport"].get("opts")
            if opts is not None and not isinstance(opts, dict):
                raise ValueError(f"devices[{idx}].transport.opts must be a mapping")

    return config


def resolve_transport(
    entry: dict[str, Any], defaults: dict[str, Any]
) -> tuple[str, dict[str, Any]]:
    """Resolve transport key and merged opts."""
    default_transport = defaults.get("transport", {})
    if isinstance(default_transport, dict):
        default_key = default_transport.get("key", "")
        default_opts: dict[str, Any] = default_transport.get("opts", {})
    else:
        default_key = ""
        default_opts = {}

    raw_et = entry.get("transport")
    entry_transport: dict[str, Any] = raw_et if isinstance(raw_et, dict) else {}
    transport_key = entry_transport.get("key") or default_key

    raw_eo = entry_transport.get("opts")
    entry_opts: dict[str, Any] = raw_eo if isinstance(raw_eo, dict) else {}

    opts = {**default_opts, **entry_opts}
    return transport_key, opts


def build_client_from_entry(
    entry: dict[str, Any],
    defaults: dict[str, Any] | None = None,
    registry: PluginRegistry | None = None,
) -> Client:
    """Build a single Client from one device config entry.

    Args:
        entry: Single device entry dict.
        defaults: Optional defaults dict (merged config.defaults).
        registry: Optional PluginRegistry. Defaults to load_plugins().

    Returns:
        Configured Client instance.
    """
    defaults = defaults or {}
    registry = registry or load_plugins()

    vendor = _resolve("vendor", entry, defaults)
    protocol_key = _resolve("protocol", entry, defaults)
    profile_id = entry.get("profile_id", "")

    if not vendor:
        raise ValueError("'vendor' is required in entry or defaults")
    if not protocol_key:
        raise ValueError("'protocol' is required in entry or defaults")
    if not profile_id:
        raise ValueError("'profile_id' is required")

    manifest = registry.get(vendor, protocol_key)
    if manifest is None:
        available = registry.keys()
        raise ValueError(
            f"No plugin registered for vendor={vendor!r} protocol={protocol_key!r}. "
            f"Available: {available}"
        )

    if manifest.profile_loader is None:
        raise ValueError(f"Plugin {manifest.key!r} has no profile_loader configured")
    profile = manifest.profile_loader(profile_id)

    transport_key, transport_opts = resolve_transport(entry, defaults)
    transport = TransportFactory.create(transport_key, **transport_opts)

    if manifest.protocol_layer_factory is None:
        raise ValueError(
            f"Plugin {manifest.key!r} has no protocol_layer_factory configured"
        )
    protocol = manifest.protocol_layer_factory()

    if manifest.parser_factory is None:
        raise ValueError(f"Plugin {manifest.key!r} has no parser_factory configured")
    parser = manifest.parser_factory()

    if manifest.schema_loader is not None:
        manifest.schema_loader(profile, parser)

    options = entry.get("options") or {}
    if not isinstance(options, dict):
        raise ValueError("device.options must be a mapping")
    try:
        device_address = int(options.get("device_address", 1))
    except (TypeError, ValueError) as exc:
        raise ValueError("device.options.device_address must be an integer") from exc
    if device_address <= 0:
        raise ValueError("device.options.device_address must be positive")

    client = Client(
        transport=transport,
        profile=profile,
        protocol=protocol,
        parser=parser,
        device_address=device_address,
    )

    if manifest.handler_loader is not None:
        manifest.handler_loader(client.device, profile)

    return client
