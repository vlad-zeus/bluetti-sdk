"""Tests for write gate: WritePolicySpec + PluginCapabilities + StageResolver."""

from __future__ import annotations

import pytest
from power_sdk.plugins.manifest import PluginCapabilities, PluginManifest
from power_sdk.plugins.registry import PluginRegistry
from power_sdk.runtime.factory import ResolvedPipeline, StageResolver
from power_sdk.runtime.spec import PipelineSpec, WritePolicySpec

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _caps(
    *,
    supports_write: bool = False,
    requires_validation: bool = True,
) -> PluginCapabilities:
    return PluginCapabilities(
        supports_write=supports_write,
        requires_device_validation_for_write=requires_validation,
    )


def _manifest(
    *,
    supports_write: bool = False,
    requires_validation: bool = True,
) -> PluginManifest:
    return PluginManifest(
        vendor="acme",
        protocol="v1",
        version="1.0.0",
        description="test",
        capabilities=_caps(
            supports_write=supports_write,
            requires_validation=requires_validation,
        ),
        parser_factory=lambda: object(),
        protocol_layer_factory=lambda: object(),
        profile_loader=lambda pid: object(),
    )


def _registry(manifest: PluginManifest) -> PluginRegistry:
    reg = PluginRegistry()
    reg.register(manifest)
    return reg


def _spec() -> PipelineSpec:
    return PipelineSpec(
        name="p", mode="pull", transport="mqtt", vendor="acme", protocol="v1"
    )


# ---------------------------------------------------------------------------
# WritePolicySpec — dataclass contract
# ---------------------------------------------------------------------------


class TestWritePolicySpec:
    def test_defaults(self) -> None:
        wp = WritePolicySpec()
        assert wp.force_allowed is False
        assert wp.require_validation is True

    def test_force_allowed_true(self) -> None:
        wp = WritePolicySpec(force_allowed=True)
        assert wp.force_allowed is True

    def test_require_validation_false(self) -> None:
        wp = WritePolicySpec(require_validation=False)
        assert wp.require_validation is False

    def test_both_fields(self) -> None:
        wp = WritePolicySpec(force_allowed=True, require_validation=False)
        assert wp.force_allowed is True
        assert wp.require_validation is False


# ---------------------------------------------------------------------------
# PluginCapabilities.can_write — gate logic
# ---------------------------------------------------------------------------


class TestPluginCapabilitiesCanWrite:
    def test_write_disabled_returns_false(self) -> None:
        caps = _caps(supports_write=False)
        assert caps.can_write() is False
        assert caps.can_write(force=True) is False

    def test_write_enabled_validation_required_no_force_returns_false(self) -> None:
        caps = _caps(supports_write=True, requires_validation=True)
        assert caps.can_write() is False

    def test_write_enabled_validation_required_with_force_returns_true(self) -> None:
        caps = _caps(supports_write=True, requires_validation=True)
        assert caps.can_write(force=True) is True

    def test_write_enabled_no_validation_returns_true(self) -> None:
        caps = _caps(supports_write=True, requires_validation=False)
        assert caps.can_write() is True
        assert caps.can_write(force=True) is True

    def test_write_disabled_force_still_returns_false(self) -> None:
        """force=True does NOT bypass supports_write=False."""
        caps = _caps(supports_write=False, requires_validation=False)
        assert caps.can_write(force=True) is False


# ---------------------------------------------------------------------------
# PluginManifest.can_write — delegates to capabilities
# ---------------------------------------------------------------------------


class TestPluginManifestCanWrite:
    def test_delegates_to_capabilities(self) -> None:
        m = _manifest(supports_write=True, requires_validation=False)
        assert m.can_write() == m.capabilities.can_write()
        assert m.can_write(force=True) == m.capabilities.can_write(force=True)

    def test_write_disabled_manifest(self) -> None:
        m = _manifest(supports_write=False)
        assert m.can_write() is False
        assert m.can_write(force=True) is False

    def test_write_enabled_no_validation_manifest(self) -> None:
        m = _manifest(supports_write=True, requires_validation=False)
        assert m.can_write() is True

    def test_write_enabled_validation_required_manifest(self) -> None:
        m = _manifest(supports_write=True, requires_validation=True)
        assert m.can_write() is False
        assert m.can_write(force=True) is True


# ---------------------------------------------------------------------------
# StageResolver.resolve — can_write surfaced in ResolvedPipeline
# ---------------------------------------------------------------------------


class TestResolvedPipelineCanWrite:
    def test_can_write_false_when_write_disabled(self) -> None:
        reg = _registry(_manifest(supports_write=False))
        result = StageResolver(reg).resolve(_spec())
        assert result.can_write is False

    def test_can_write_false_when_validation_required_no_force(self) -> None:
        """Default resolve() calls can_write(force=False)."""
        reg = _registry(_manifest(supports_write=True, requires_validation=True))
        result = StageResolver(reg).resolve(_spec())
        assert result.can_write is False

    def test_can_write_true_when_no_validation_required(self) -> None:
        reg = _registry(_manifest(supports_write=True, requires_validation=False))
        result = StageResolver(reg).resolve(_spec())
        assert result.can_write is True

    def test_resolved_pipeline_is_dataclass(self) -> None:
        reg = _registry(_manifest())
        result = StageResolver(reg).resolve(_spec())
        assert isinstance(result, ResolvedPipeline)

    def test_write_gate_independent_of_streaming(self) -> None:
        """supports_streaming does not affect can_write."""
        caps = PluginCapabilities(
            supports_write=True,
            requires_device_validation_for_write=False,
            supports_streaming=False,
        )
        m = PluginManifest(
            vendor="acme",
            protocol="v1",
            version="1.0",
            description="t",
            capabilities=caps,
            parser_factory=lambda: object(),
            protocol_layer_factory=lambda: object(),
            profile_loader=lambda pid: object(),
        )
        reg = _registry(m)
        result = StageResolver(reg).resolve(_spec())
        assert result.can_write is True
        assert result.supports_streaming is False


# ---------------------------------------------------------------------------
# Write gate policy combinations
# ---------------------------------------------------------------------------


class TestWriteGatePolicyCombinations:
    """Matrix of WritePolicySpec x PluginCapabilities combinations."""

    @pytest.mark.parametrize(
        "supports_write,requires_validation,force_allowed,expected",
        [
            # supports_write=False → always blocked
            (False, True, False, False),
            (False, True, True, False),
            (False, False, False, False),
            (False, False, True, False),
            # supports_write=True, requires_validation=False → always allowed
            (True, False, False, True),
            (True, False, True, True),
            # supports_write=True, requires_validation=True, no force → blocked
            (True, True, False, False),
            # supports_write=True, requires_validation=True, force=True → allowed
            (True, True, True, True),
        ],
    )
    def test_policy_matrix(
        self,
        supports_write: bool,
        requires_validation: bool,
        force_allowed: bool,
        expected: bool,
    ) -> None:
        """Verify write gate outcome for all meaningful policy combinations.

        The effective write permission is:
            can_write(force=force_allowed)
        where force=True bypasses the validation requirement (but not supports_write).
        """
        caps = PluginCapabilities(
            supports_write=supports_write,
            requires_device_validation_for_write=requires_validation,
        )
        result = caps.can_write(force=force_allowed)
        assert result is expected
