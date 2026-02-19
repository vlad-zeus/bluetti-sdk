"""Unit tests for DeviceRuntime and RuntimeRegistry."""
from __future__ import annotations

import pytest
from power_sdk.runtime import DeviceRuntime, DeviceSnapshot, RuntimeRegistry

# --- helpers ---


def _make_yaml(tmp_path, devices: list[dict], defaults: dict | None = None) -> str:
    """Write a runtime.yaml with N devices, return path string."""
    import yaml

    config = {
        "version": 1,
        "defaults": defaults
        or {
            "vendor": "acme",
            "protocol": "v1",
            "poll_interval": 30,
            "transport": {"key": "stub", "opts": {}},
        },
        "devices": devices,
    }
    p = tmp_path / "runtime.yaml"
    p.write_text(yaml.dump(config))
    return str(p)


def _make_mock_client():
    from unittest.mock import Mock

    client = Mock()
    client.profile.model = "ACME_DEV1"
    client.connect = Mock()
    client.disconnect = Mock()
    client.read_group = Mock(return_value=[])
    client.get_device_state = Mock(return_value={"ok": True})
    return client


def _make_device_runtime(
    device_id="dev1", *, vendor="acme", protocol="v1"
) -> DeviceRuntime:
    return DeviceRuntime(
        device_id=device_id,
        client=_make_mock_client(),
        vendor=vendor,
        protocol=protocol,
        profile_id="ACME_DEV1",
        transport_key="stub",
        poll_interval=30.0,
    )


# --- tests ---


def test_device_runtime_poll_once_returns_ok_snapshot():
    runtime = _make_device_runtime()
    snapshot = runtime.poll_once()
    assert snapshot.ok
    assert snapshot.device_id == "dev1"
    assert snapshot.blocks_read == 0  # mock returns []


def test_device_runtime_poll_once_captures_error():
    from power_sdk.errors import TransportError

    runtime = _make_device_runtime()
    runtime.client.read_group.side_effect = TransportError("boom")
    snapshot = runtime.poll_once()
    assert not snapshot.ok
    assert snapshot.error is not None
    assert snapshot.blocks_read == 0


def test_device_runtime_connect_flag_calls_connect():
    runtime = _make_device_runtime()
    runtime.poll_once(connect=True, disconnect=True)
    runtime.client.connect.assert_called_once()
    runtime.client.disconnect.assert_called_once()


def test_device_runtime_last_snapshot_updated():
    runtime = _make_device_runtime()
    assert runtime.last_snapshot is None
    runtime.poll_once()
    assert runtime.last_snapshot is not None


def test_runtime_registry_built_from_runtimes():
    runtimes = [_make_device_runtime(f"dev{i}") for i in range(3)]
    reg = RuntimeRegistry(runtimes)
    assert len(reg) == 3
    assert reg.get("dev0") is not None
    assert reg.get("dev2") is not None


def test_runtime_registry_rejects_duplicate_runtime_ids():
    r1 = _make_device_runtime("dev1")
    r2 = _make_device_runtime("dev1")
    with pytest.raises(ValueError, match="Duplicate runtime device_id"):
        RuntimeRegistry([r1, r2])


def test_poll_all_once_returns_all_snapshots():
    runtimes = [_make_device_runtime(f"dev{i}") for i in range(3)]
    reg = RuntimeRegistry(runtimes)
    snapshots = reg.poll_all_once()
    assert len(snapshots) == 3
    assert all(isinstance(s, DeviceSnapshot) for s in snapshots)


def test_poll_all_once_error_in_one_does_not_stop_others():
    from power_sdk.errors import TransportError

    r1 = _make_device_runtime("dev1")
    r2 = _make_device_runtime("dev2")
    r3 = _make_device_runtime("dev3")
    r2.client.read_group.side_effect = TransportError("boom")
    reg = RuntimeRegistry([r1, r2, r3])
    snapshots = reg.poll_all_once()
    assert len(snapshots) == 3
    assert snapshots[0].ok
    assert not snapshots[1].ok
    assert snapshots[2].ok


def test_dry_run_returns_device_summaries():
    from power_sdk.plugins.registry import PluginRegistry

    from tests.stubs.acme.plugin import ACME_V1_MANIFEST

    plugin_reg = PluginRegistry()
    plugin_reg.register(ACME_V1_MANIFEST)

    runtimes = [
        _make_device_runtime("dev1", vendor="acme", protocol="v1"),
        _make_device_runtime("dev2", vendor="acme", protocol="v1"),
    ]
    reg = RuntimeRegistry(runtimes)
    summaries = reg.dry_run(plugin_registry=plugin_reg)
    assert len(summaries) == 2
    assert summaries[0].vendor == "acme"
    assert summaries[0].can_write is False
    assert summaries[0].supports_streaming is True


def test_from_config_rejects_invalid_defaults_transport_type(
    tmp_path, monkeypatch
):
    from power_sdk.plugins.registry import PluginRegistry

    yaml_path = _make_yaml(
        tmp_path,
        devices=[
            {
                "id": "dev1",
                "profile_id": "ACME_DEV1",
                "transport": {"key": "stub"},
            }
        ],
        defaults={
            "vendor": "acme",
            "protocol": "v1",
            "poll_interval": 30,
            "transport": "not-a-mapping",
        },
    )

    monkeypatch.setattr(
        "power_sdk.runtime.registry.build_client_from_entry",
        lambda entry, defaults, registry: _make_mock_client(),
    )

    with pytest.raises(ValueError, match=r"defaults\.transport"):
        RuntimeRegistry.from_config(yaml_path, plugin_registry=PluginRegistry())
