"""CI guard: verify that legacy symbols are not exposed in the public API."""

from __future__ import annotations


def test_legacy_bootstrap_not_in_public_api() -> None:
    import power_sdk

    assert not hasattr(power_sdk, "build_all_clients")
    assert not hasattr(power_sdk, "build_client_from_entry")
    assert not hasattr(power_sdk, "load_config")


def test_v2device_alias_removed() -> None:
    from power_sdk.models import __all__ as models_all

    assert "V2Device" not in models_all


def test_mqtt_not_eagerly_imported_at_top_level() -> None:
    """MQTTTransport/MQTTConfig must NOT be in the top-level public API.

    They carry a paho-mqtt hard dependency.  Users who don't use MQTT
    must be able to import power_sdk without paho-mqtt installed.
    """
    import power_sdk

    assert not hasattr(power_sdk, "MQTTTransport"), (
        "MQTTTransport must not be a top-level export (use power_sdk.transport.mqtt)"
    )
    assert not hasattr(power_sdk, "MQTTConfig"), (
        "MQTTConfig must not be a top-level export (use power_sdk.transport.mqtt)"
    )


def test_mqtt_not_in_transport_init_all() -> None:
    """MQTTTransport/MQTTConfig must NOT be re-exported from power_sdk.transport."""
    from power_sdk import transport as transport_module

    assert "MQTTTransport" not in transport_module.__all__
    assert "MQTTConfig" not in transport_module.__all__


def test_core_public_symbols_present() -> None:
    """Core SDK symbols must be importable from top-level power_sdk."""
    import power_sdk

    required = [
        "Client",
        "AsyncClient",
        "Device",
        "DeviceProfile",
        "ParserInterface",
        "SDKError",
        "TransportError",
        "ProtocolError",
        "ParserError",
        "TransportFactory",
        "ReadGroupResult",
    ]
    for name in required:
        assert hasattr(power_sdk, name), f"'{name}' missing from power_sdk public API"
