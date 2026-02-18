"""Unit tests for config-driven bootstrap."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest
from power_sdk.bootstrap import (
    build_all_clients,
    build_client_from_entry,
    load_config,
)
from power_sdk.devices.types import BlockGroupDefinition, DeviceProfile
from power_sdk.errors import TransportError

SAMPLE_YAML = """\
version: 1
defaults:
  transport:
    key: mqtt
    opts:
      broker: localhost
      port: 18760
  protocol: v2
devices:
  - id: dev-1
    profile:
      model: EL100V2
      protocol: v2
    transport:
      key: mqtt
      opts:
        device_sn: TEST_SN
    options:
      device_address: 1
"""


def test_load_config_success() -> None:
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, dir=".", encoding="utf-8"
    ) as cfg_file:
        cfg_file.write(SAMPLE_YAML)
        cfg_path = Path(cfg_file.name)
    try:
        cfg = load_config(cfg_path)
        assert cfg["version"] == 1
        assert len(cfg["devices"]) == 1
        assert cfg["devices"][0]["id"] == "dev-1"
    finally:
        cfg_path.unlink(missing_ok=True)


def test_load_config_rejects_empty_devices() -> None:
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, dir=".", encoding="utf-8"
    ) as cfg_file:
        cfg_file.write("version: 1\ndevices: []\n")
        cfg_path = Path(cfg_file.name)
    try:
        with pytest.raises(ValueError, match="non-empty list"):
            load_config(cfg_path)
    finally:
        cfg_path.unlink(missing_ok=True)


def test_load_config_expands_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BOOTSTRAP_SN", "SN_123")
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, dir=".", encoding="utf-8"
    ) as cfg_file:
        cfg_file.write(
            """\
version: 1
devices:
  - id: dev-1
    profile:
      model: EL100V2
    transport:
      key: mqtt
      opts:
        device_sn: "${BOOTSTRAP_SN}"
""",
        )
        cfg_path = Path(cfg_file.name)
    try:
        cfg = load_config(cfg_path)
        assert cfg["devices"][0]["transport"]["opts"]["device_sn"] == "SN_123"
    finally:
        cfg_path.unlink(missing_ok=True)


def test_build_client_from_entry_uses_factories(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entry = {
        "id": "dev-1",
        "profile": {"model": "EL100V2", "protocol": "v2"},
        "transport": {"key": "mqtt", "opts": {"device_sn": "SN_TEST"}},
        "options": {"device_address": 1},
    }

    fake_profile = DeviceProfile(
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
    fake_transport = Mock()
    fake_protocol = Mock()
    fake_client = Mock()

    monkeypatch.setattr(
        "power_sdk.bootstrap.get_device_profile", lambda model: fake_profile
    )
    monkeypatch.setattr(
        "power_sdk.bootstrap.TransportFactory.create",
        lambda key, **opts: fake_transport,
    )
    monkeypatch.setattr(
        "power_sdk.bootstrap.ProtocolFactory.create",
        lambda key: fake_protocol,
    )
    monkeypatch.setattr("power_sdk.bootstrap.Client", lambda **kwargs: fake_client)

    result = build_client_from_entry(entry)
    assert result is fake_client


def test_build_all_clients_wraps_errors() -> None:
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, dir=".", encoding="utf-8"
    ) as cfg_file:
        cfg_file.write(SAMPLE_YAML)
        cfg_path = Path(cfg_file.name)

    def _raise_builder(_key: str, **_opts: object) -> object:
        raise ValueError("boom")

    try:
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                "power_sdk.bootstrap.TransportFactory.create",
                _raise_builder,
            )
            with pytest.raises(TransportError, match="Failed to build client"):
                build_all_clients(cfg_path)
    finally:
        cfg_path.unlink(missing_ok=True)


