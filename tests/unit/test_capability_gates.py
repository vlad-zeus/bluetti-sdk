"""Unit tests for PluginCapabilities gating logic."""

from __future__ import annotations

import pytest
from power_sdk.plugins.manifest import PluginCapabilities, PluginManifest


class TestPluginCapabilities:
    def test_defaults_are_safe(self) -> None:
        caps = PluginCapabilities()
        assert caps.supports_write is False
        assert caps.supports_streaming is True
        assert caps.requires_device_validation_for_write is True

    def test_can_write_false_when_supports_write_false(self) -> None:
        caps = PluginCapabilities(supports_write=False)
        assert caps.can_write() is False
        # force cannot override supports_write=False
        assert caps.can_write(force=True) is False

    def test_can_write_false_when_validation_required(self) -> None:
        caps = PluginCapabilities(
            supports_write=True,
            requires_device_validation_for_write=True,
        )
        assert caps.can_write() is False  # validation not done yet

    def test_can_write_true_when_validation_not_required(self) -> None:
        caps = PluginCapabilities(
            supports_write=True,
            requires_device_validation_for_write=False,
        )
        assert caps.can_write() is True

    def test_can_write_force_bypasses_validation_requirement(self) -> None:
        caps = PluginCapabilities(
            supports_write=True,
            requires_device_validation_for_write=True,
        )
        assert caps.can_write(force=True) is True

    def test_can_write_force_still_blocked_when_not_supported(self) -> None:
        caps = PluginCapabilities(supports_write=False)
        assert caps.can_write(force=True) is False

    def test_immutable(self) -> None:
        caps = PluginCapabilities()
        with pytest.raises((AttributeError, TypeError)):
            caps.supports_write = True  # type: ignore[misc]


class TestManifestCanWrite:
    def _make_manifest(self, **cap_kwargs) -> PluginManifest:
        return PluginManifest(
            vendor="test",
            protocol="v0",
            version="0.1.0",
            description="test",
            profile_ids=("T1",),
            transport_keys=("mqtt",),
            capabilities=PluginCapabilities(**cap_kwargs),
        )

    def test_manifest_can_write_delegates(self) -> None:
        m = self._make_manifest(
            supports_write=True, requires_device_validation_for_write=False
        )
        assert m.can_write() is True

    def test_manifest_can_write_default_false(self) -> None:
        m = self._make_manifest()
        assert m.can_write() is False

    def test_manifest_can_write_force(self) -> None:
        m = self._make_manifest(
            supports_write=True, requires_device_validation_for_write=True
        )
        assert m.can_write(force=True) is True
