"""Unit tests for config-driven bootstrap."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest
from power_sdk.bootstrap import (
    build_client_from_entry,
    load_config,
)
from power_sdk.devices.types import BlockGroupDefinition, DeviceProfile
from power_sdk.plugins.manifest import PluginManifest
from power_sdk.plugins.registry import PluginRegistry

SAMPLE_YAML = """\
version: 1
defaults:
  vendor: bluetti
  protocol: v2
  transport:
    key: mqtt
    opts:
      broker: localhost
      port: 18760
devices:
  - id: dev-1
    profile_id: EL100V2
    transport:
      key: mqtt
      opts:
        device_sn: TEST_SN
    options:
      device_address: 1
"""


def _make_fake_profile() -> DeviceProfile:
    return DeviceProfile(
        model="EL100V2",
        type_id="31",
        protocol="v2",
        description="fake",
        groups={
            "core": BlockGroupDefinition(
                name="core", blocks=[100], description="core", poll_interval=5
            )
        },
    )


def _make_mock_registry(profile: DeviceProfile) -> PluginRegistry:
    """Build a PluginRegistry with a mock Bluetti V2 manifest."""
    manifest = PluginManifest(
        vendor="bluetti",
        protocol="v2",
        version="1.0.0",
        description="test",
        profile_loader=lambda pid: profile,
        protocol_layer_factory=Mock,
        parser_factory=Mock,
        schema_loader=None,
    )
    registry = PluginRegistry()
    registry.register(manifest)
    return registry


def test_load_config_success(tmp_path: Path) -> None:
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, dir=tmp_path, encoding="utf-8"
    ) as f:
        f.write(SAMPLE_YAML)
        path = Path(f.name)
    try:
        cfg = load_config(path)
        assert cfg["version"] == 1
        assert len(cfg["devices"]) == 1
        assert cfg["devices"][0]["id"] == "dev-1"
    finally:
        path.unlink(missing_ok=True)


def test_load_config_rejects_empty_devices(tmp_path: Path) -> None:
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, dir=tmp_path, encoding="utf-8"
    ) as f:
        f.write("version: 1\ndevices: []\n")
        path = Path(f.name)
    try:
        with pytest.raises(ValueError, match="non-empty list"):
            load_config(path)
    finally:
        path.unlink(missing_ok=True)


def test_load_config_rejects_missing_profile_id(tmp_path: Path) -> None:
    yaml_text = """\
version: 1
defaults:
  vendor: bluetti
  protocol: v2
  transport:
    key: mqtt
devices:
  - id: dev-1
    transport:
      key: mqtt
      opts:
        device_sn: SN
"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, dir=tmp_path, encoding="utf-8"
    ) as f:
        f.write(yaml_text)
        path = Path(f.name)
    try:
        with pytest.raises(ValueError, match="profile_id"):
            load_config(path)
    finally:
        path.unlink(missing_ok=True)


def test_load_config_rejects_missing_vendor(tmp_path: Path) -> None:
    yaml_text = """\
version: 1
defaults:
  protocol: v2
  transport:
    key: mqtt
devices:
  - id: dev-1
    profile_id: EL100V2
    transport:
      key: mqtt
      opts:
        device_sn: SN
"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, dir=tmp_path, encoding="utf-8"
    ) as f:
        f.write(yaml_text)
        path = Path(f.name)
    try:
        with pytest.raises(ValueError, match="vendor"):
            load_config(path)
    finally:
        path.unlink(missing_ok=True)


def test_load_config_rejects_duplicate_device_ids(tmp_path: Path) -> None:
    yaml_text = """\
version: 1
defaults:
  vendor: bluetti
  protocol: v2
  transport:
    key: mqtt
devices:
  - id: dev-1
    profile_id: EL100V2
  - id: dev-1
    profile_id: EL30V2
"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, dir=tmp_path, encoding="utf-8"
    ) as f:
        f.write(yaml_text)
        path = Path(f.name)
    try:
        with pytest.raises(ValueError, match="Duplicate device id"):
            load_config(path)
    finally:
        path.unlink(missing_ok=True)


def test_load_config_expands_env(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("BOOTSTRAP_SN", "SN_123")
    yaml_text = """\
version: 1
defaults:
  vendor: bluetti
  protocol: v2
  transport:
    key: mqtt
devices:
  - id: dev-1
    profile_id: EL100V2
    transport:
      key: mqtt
      opts:
        device_sn: "${BOOTSTRAP_SN}"
"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, dir=tmp_path, encoding="utf-8"
    ) as f:
        f.write(yaml_text)
        path = Path(f.name)
    try:
        cfg = load_config(path)
        assert cfg["devices"][0]["transport"]["opts"]["device_sn"] == "SN_123"
    finally:
        path.unlink(missing_ok=True)


def test_build_client_from_entry_uses_registry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entry = {
        "id": "dev-1",
        "vendor": "bluetti",
        "protocol": "v2",
        "profile_id": "EL100V2",
        "transport": {"key": "mqtt", "opts": {"device_sn": "SN_TEST"}},
        "options": {"device_address": 1},
    }
    fake_profile = _make_fake_profile()
    fake_transport = Mock()
    fake_client = Mock()

    mock_registry = _make_mock_registry(fake_profile)

    monkeypatch.setattr(
        "power_sdk.bootstrap.TransportFactory.create",
        lambda key, **opts: fake_transport,
    )
    monkeypatch.setattr("power_sdk.bootstrap.Client", lambda **kwargs: fake_client)

    result = build_client_from_entry(entry, registry=mock_registry)
    assert result is fake_client


def test_build_client_rejects_unknown_plugin() -> None:
    entry = {
        "id": "dev-1",
        "vendor": "acme",
        "protocol": "xyz",
        "profile_id": "ACME100",
        "transport": {"key": "mqtt", "opts": {"device_sn": "SN"}},
    }
    registry = PluginRegistry()  # empty — no plugins registered
    with pytest.raises(ValueError, match="No plugin registered"):
        build_client_from_entry(entry, registry=registry)


def test_build_client_rejects_missing_profile_loader() -> None:
    entry = {
        "id": "dev-1",
        "vendor": "bluetti",
        "protocol": "v2",
        "profile_id": "EL100V2",
        "transport": {"key": "mqtt", "opts": {"device_sn": "SN"}},
    }
    manifest = PluginManifest(
        vendor="bluetti",
        protocol="v2",
        version="1.0.0",
        description="test",
        profile_loader=None,
        protocol_layer_factory=Mock,
        parser_factory=Mock,
    )
    registry = PluginRegistry()
    registry.register(manifest)
    with pytest.raises(ValueError, match="profile_loader"):
        build_client_from_entry(entry, registry=registry)


def test_build_client_rejects_missing_parser_factory() -> None:
    entry = {
        "id": "dev-1",
        "vendor": "bluetti",
        "protocol": "v2",
        "profile_id": "EL100V2",
        "transport": {"key": "mqtt", "opts": {"device_sn": "SN"}},
    }
    fake_profile = _make_fake_profile()
    manifest = PluginManifest(
        vendor="bluetti",
        protocol="v2",
        version="1.0.0",
        description="test",
        profile_loader=lambda _pid: fake_profile,
        protocol_layer_factory=Mock,
        parser_factory=None,
    )
    registry = PluginRegistry()
    registry.register(manifest)
    with pytest.raises(ValueError, match="parser_factory"):
        build_client_from_entry(entry, registry=registry)


def test_load_config_rejects_unresolved_env_var(tmp_path: Path) -> None:
    """load_config must raise ValueError when a ${VAR} placeholder is not expanded."""
    yaml_text = """\
version: 1
defaults:
  vendor: bluetti
  protocol: v2
  transport:
    key: mqtt
devices:
  - id: dev-1
    profile_id: EL100V2
    transport:
      key: mqtt
      opts:
        device_sn: "${UNDEFINED_BOOTSTRAP_VAR_XYZ}"
"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, dir=tmp_path, encoding="utf-8"
    ) as f:
        f.write(yaml_text)
        path = Path(f.name)
    try:
        with pytest.raises(ValueError, match="unresolved environment variable"):
            load_config(path)
    finally:
        path.unlink(missing_ok=True)
