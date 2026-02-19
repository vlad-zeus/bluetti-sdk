"""Tests for StageResolver and PipelineSpec resolution."""
from __future__ import annotations

import pytest
from power_sdk.plugins.manifest import PluginCapabilities, PluginManifest
from power_sdk.plugins.registry import PluginRegistry
from power_sdk.runtime.factory import ResolvedPipeline, StageResolver
from power_sdk.runtime.spec import PipelineSpec

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _manifest(
    vendor: str = "acme",
    protocol: str = "v1",
    *,
    can_write: bool = False,
    missing_parser: bool = False,
    missing_protocol_layer: bool = False,
    missing_profile_loader: bool = False,
) -> PluginManifest:
    return PluginManifest(
        vendor=vendor,
        protocol=protocol,
        version="1.0.0",
        description="Test manifest",
        capabilities=PluginCapabilities(
            supports_write=can_write,
            requires_device_validation_for_write=not can_write,
        ),
        parser_factory=None if missing_parser else lambda: object(),
        protocol_layer_factory=(
            None if missing_protocol_layer else lambda: object()
        ),
        profile_loader=None if missing_profile_loader else lambda pid: object(),
    )


def _registry(*manifests: PluginManifest) -> PluginRegistry:
    reg = PluginRegistry()
    for m in manifests:
        reg.register(m)
    return reg


def _spec(
    name: str = "test_pipeline",
    mode: str = "pull",
    transport: str = "mqtt",
    vendor: str = "acme",
    protocol: str = "v1",
) -> PipelineSpec:
    return PipelineSpec(
        name=name, mode=mode, transport=transport, vendor=vendor, protocol=protocol
    )


# ---------------------------------------------------------------------------
# StageResolver.validate — happy paths
# ---------------------------------------------------------------------------


class TestStageResolverValidate:
    def test_valid_pull_pipeline_passes(self) -> None:
        reg = _registry(_manifest())
        resolver = StageResolver(plugin_registry=reg)
        resolver.validate(_spec(mode="pull"))  # should not raise

    def test_valid_push_pipeline_passes(self) -> None:
        reg = _registry(_manifest())
        resolver = StageResolver(plugin_registry=reg)
        resolver.validate(_spec(mode="push"))  # should not raise

    def test_no_vendor_protocol_skips_plugin_check(self) -> None:
        """Sparse pipeline (no vendor/protocol) skips plugin lookup."""
        reg = _registry()
        resolver = StageResolver(plugin_registry=reg)
        spec = PipelineSpec(name="bare", mode="pull", transport="mqtt")
        resolver.validate(spec)  # should not raise

    def test_no_transport_skips_transport_check(self) -> None:
        reg = _registry(_manifest())
        resolver = StageResolver(plugin_registry=reg)
        spec = PipelineSpec(name="no_transport", vendor="acme", protocol="v1")
        resolver.validate(spec)  # should not raise

    def test_writable_plugin_passes(self) -> None:
        reg = _registry(_manifest(can_write=True))
        resolver = StageResolver(plugin_registry=reg)
        resolver.validate(_spec())  # should not raise


# ---------------------------------------------------------------------------
# StageResolver.validate — error paths
# ---------------------------------------------------------------------------


class TestStageResolverValidateErrors:
    def test_invalid_mode_raises(self) -> None:
        reg = _registry(_manifest())
        resolver = StageResolver(plugin_registry=reg)
        with pytest.raises(ValueError, match="mode="):
            resolver.validate(_spec(mode="stream"))

    def test_unknown_transport_raises(self) -> None:
        reg = _registry(_manifest())
        resolver = StageResolver(plugin_registry=reg)
        with pytest.raises(ValueError, match="transport="):
            resolver.validate(_spec(transport="kafka"))

    def test_unknown_plugin_raises(self) -> None:
        reg = _registry()  # empty registry
        resolver = StageResolver(plugin_registry=reg)
        with pytest.raises(ValueError, match="no plugin registered"):
            resolver.validate(_spec(vendor="unknown", protocol="v99"))

    def test_missing_parser_factory_raises(self) -> None:
        reg = _registry(_manifest(missing_parser=True))
        resolver = StageResolver(plugin_registry=reg)
        with pytest.raises(ValueError, match="parser_factory"):
            resolver.validate(_spec())

    def test_missing_protocol_layer_factory_raises(self) -> None:
        reg = _registry(_manifest(missing_protocol_layer=True))
        resolver = StageResolver(plugin_registry=reg)
        with pytest.raises(ValueError, match="protocol_layer_factory"):
            resolver.validate(_spec())

    def test_missing_profile_loader_raises(self) -> None:
        reg = _registry(_manifest(missing_profile_loader=True))
        resolver = StageResolver(plugin_registry=reg)
        with pytest.raises(ValueError, match="profile_loader"):
            resolver.validate(_spec())

    def test_multiple_errors_all_reported(self) -> None:
        """All errors collected before raising — not fail-fast."""
        reg = _registry()  # empty — unknown plugin
        resolver = StageResolver(plugin_registry=reg)
        spec = PipelineSpec(
            name="bad",
            mode="unknown_mode",
            transport="kafka",
            vendor="x",
            protocol="y",
        )
        with pytest.raises(ValueError) as exc_info:
            resolver.validate(spec)
        msg = str(exc_info.value)
        assert "mode=" in msg
        assert "transport=" in msg
        assert "no plugin" in msg


# ---------------------------------------------------------------------------
# StageResolver.resolve
# ---------------------------------------------------------------------------


class TestStageResolverResolve:
    def test_resolve_returns_resolved_pipeline(self) -> None:
        reg = _registry(_manifest(vendor="acme", protocol="v1"))
        resolver = StageResolver(plugin_registry=reg)
        result = resolver.resolve(_spec())
        assert isinstance(result, ResolvedPipeline)
        assert result.pipeline_name == "test_pipeline"
        assert result.mode == "pull"
        assert result.transport == "mqtt"
        assert result.vendor == "acme"
        assert result.protocol == "v1"

    def test_resolve_can_write_false_by_default(self) -> None:
        reg = _registry(_manifest(can_write=False))
        result = StageResolver(reg).resolve(_spec())
        assert result.can_write is False

    def test_resolve_can_write_true_when_manifest_allows(self) -> None:
        reg = _registry(_manifest(can_write=True))
        result = StageResolver(reg).resolve(_spec())
        assert result.can_write is True

    def test_resolve_supports_streaming_from_manifest(self) -> None:
        reg = _registry(_manifest())
        result = StageResolver(reg).resolve(_spec())
        assert result.supports_streaming is True  # PluginCapabilities default

    def test_resolve_parser_and_model_use_plugin_key(self) -> None:
        reg = _registry(_manifest(vendor="acme", protocol="v1"))
        result = StageResolver(reg).resolve(_spec())
        assert result.parser == "acme/v1"
        assert result.model == "acme/v1"

    def test_resolve_raises_on_invalid_spec(self) -> None:
        reg = _registry()
        resolver = StageResolver(plugin_registry=reg)
        with pytest.raises(ValueError):
            resolver.resolve(_spec(transport="kafka"))

    def test_resolve_multiple_pipelines_different_plugins(self) -> None:
        """Two pipelines with different plugins resolve independently."""
        m1 = _manifest(vendor="acme", protocol="v1", can_write=False)
        m2 = _manifest(vendor="acme", protocol="v2", can_write=True)
        reg = _registry(m1, m2)
        resolver = StageResolver(plugin_registry=reg)

        r1 = resolver.resolve(_spec(name="p1", vendor="acme", protocol="v1"))
        r2 = resolver.resolve(
            _spec(name="p2", vendor="acme", protocol="v2", mode="push")
        )
        assert r1.can_write is False
        assert r2.can_write is True
        assert r2.mode == "push"
