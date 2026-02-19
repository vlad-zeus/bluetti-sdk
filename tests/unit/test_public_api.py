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
