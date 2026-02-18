"""PluginManifest and PluginRegistry conformance tests.

Any plugin that wants to merge must pass these tests.
Run with: pytest tests/conformance/test_plugin_manifest_conformance.py
"""

from __future__ import annotations

import pytest
from power_sdk.contracts.parser import ParserInterface
from power_sdk.contracts.protocol import ProtocolLayerInterface
from power_sdk.devices.types import DeviceProfile
from power_sdk.plugins.manifest import PluginManifest
from power_sdk.plugins.registry import PluginRegistry

# ---------------------------------------------------------------------------
# Fixture: the registry under test (both vendors, no load_plugins() call)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def registry() -> PluginRegistry:
    from power_sdk.plugins.bluetti.v2.manifest_instance import BLUETTI_V2_MANIFEST

    from tests.stubs.acme.plugin import ACME_V1_MANIFEST

    reg = PluginRegistry()
    reg.register(BLUETTI_V2_MANIFEST)
    reg.register(ACME_V1_MANIFEST)
    return reg


@pytest.fixture(
    params=["bluetti/v2", "acme/v1"],
    scope="module",
)
def manifest(
    request: pytest.FixtureRequest, registry: PluginRegistry
) -> PluginManifest:
    vendor, protocol = request.param.split("/")
    m = registry.get(vendor, protocol)
    if m is None:
        pytest.skip(f"Plugin {request.param!r} not registered")
    return m  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Registry-level conformance
# ---------------------------------------------------------------------------


class TestPluginRegistryConformance:
    def test_load_plugins_returns_registry(self, registry: PluginRegistry) -> None:
        assert isinstance(registry, PluginRegistry)

    def test_registry_has_at_least_one_plugin(
        self, registry: PluginRegistry
    ) -> None:
        assert len(registry) >= 1

    def test_registry_keys_are_vendor_slash_protocol(
        self, registry: PluginRegistry
    ) -> None:
        for key in registry:
            parts = key.split("/")
            assert len(parts) == 2, f"Key {key!r} must be 'vendor/protocol'"
            assert all(p for p in parts), (
                f"Key {key!r} must have non-empty vendor and protocol"
            )


# ---------------------------------------------------------------------------
# Manifest-level conformance
# ---------------------------------------------------------------------------


class TestPluginManifestConformance:
    def test_key_is_vendor_slash_protocol(self, manifest: PluginManifest) -> None:
        assert manifest.key == f"{manifest.vendor}/{manifest.protocol}"

    def test_vendor_is_non_empty_string(self, manifest: PluginManifest) -> None:
        assert isinstance(manifest.vendor, str) and manifest.vendor

    def test_protocol_is_non_empty_string(self, manifest: PluginManifest) -> None:
        assert isinstance(manifest.protocol, str) and manifest.protocol

    def test_version_is_semver_like(self, manifest: PluginManifest) -> None:
        parts = manifest.version.split(".")
        assert len(parts) >= 2, (
            f"version {manifest.version!r} must have at least major.minor"
        )

    def test_profile_ids_is_non_empty_tuple(
        self, manifest: PluginManifest
    ) -> None:
        assert isinstance(manifest.profile_ids, tuple)
        assert len(manifest.profile_ids) >= 1

    def test_transport_keys_is_non_empty_tuple(
        self, manifest: PluginManifest
    ) -> None:
        assert isinstance(manifest.transport_keys, tuple)
        assert len(manifest.transport_keys) >= 1

    def test_parser_factory_is_set(self, manifest: PluginManifest) -> None:
        assert manifest.parser_factory is not None

    def test_protocol_layer_factory_is_set(
        self, manifest: PluginManifest
    ) -> None:
        assert manifest.protocol_layer_factory is not None

    def test_profile_loader_is_set(self, manifest: PluginManifest) -> None:
        assert manifest.profile_loader is not None

    def test_parser_factory_returns_parser_interface(
        self, manifest: PluginManifest
    ) -> None:
        parser = manifest.parser_factory()
        assert isinstance(parser, ParserInterface)

    def test_protocol_layer_factory_returns_layer_interface(
        self, manifest: PluginManifest
    ) -> None:
        layer = manifest.protocol_layer_factory()
        assert isinstance(layer, ProtocolLayerInterface)

    def test_profile_loader_resolves_all_declared_profile_ids(
        self, manifest: PluginManifest
    ) -> None:
        """Every profile_id declared in the manifest must resolve to a DeviceProfile."""
        assert manifest.profile_loader is not None
        for pid in manifest.profile_ids:
            profile = manifest.profile_loader(pid)
            assert isinstance(profile, DeviceProfile), (
                f"profile_loader({pid!r}) returned {type(profile).__name__}, "
                f"expected DeviceProfile"
            )

    def test_profile_loader_raises_for_unknown_profile(
        self, manifest: PluginManifest
    ) -> None:
        """profile_loader() must raise for an unknown profile_id."""
        assert manifest.profile_loader is not None
        with pytest.raises((ValueError, KeyError, LookupError)):
            manifest.profile_loader("__CONFORMANCE_UNKNOWN_PROFILE_ID__")
