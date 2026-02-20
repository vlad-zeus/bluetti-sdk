"""Tests for plugin discovery via entry_points."""

from __future__ import annotations

import importlib.metadata
import logging
from unittest.mock import MagicMock

import pytest
from power_sdk.plugins.registry import load_plugins


def _make_fake_ep(name: str, manifest: object) -> MagicMock:
    ep = MagicMock()
    ep.name = name
    ep.load.return_value = manifest
    return ep


class _EmptyEps:
    def select(self, group: str) -> list:  # type: ignore[return]
        return []

    def get(self, group: str, default: object = None) -> object:
        return default or []


class _FakeEps:
    def __init__(self, eps: list) -> None:
        self._eps = eps

    def select(self, group: str) -> list:
        return self._eps if group == "power_sdk.plugins" else []

    def get(self, group: str, default: object = None) -> object:
        return self._eps if group == "power_sdk.plugins" else (default or [])


class TestRegistryDiscovery:
    def test_no_entry_points_returns_empty_registry(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """If no sources found, registry is empty."""
        monkeypatch.setattr(importlib.metadata, "entry_points", lambda: _EmptyEps())
        monkeypatch.setattr(
            "power_sdk.plugins.registry._discover_from_local_package", list
        )
        reg = load_plugins()
        assert len(reg) == 0

    def test_discovery_registers_manifest(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """entry_points returns ACME manifest → it is registered, no fallback."""
        from tests.stubs.acme.plugin import ACME_V1_MANIFEST

        fake_eps = _FakeEps([_make_fake_ep("acme/v1", ACME_V1_MANIFEST)])
        monkeypatch.setattr(importlib.metadata, "entry_points", lambda: fake_eps)
        monkeypatch.setattr(
            "power_sdk.plugins.registry._discover_from_local_package", list
        )
        reg = load_plugins()

        assert "acme/v1" in reg
        assert len(reg) == 1  # no Bluetti fallback

    def test_broken_ep_logged_and_skipped(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A broken entry point is logged as warning and skipped."""
        bad_ep = MagicMock()
        bad_ep.name = "bad/v0"
        bad_ep.load.side_effect = ImportError("missing dep")

        fake_eps = _FakeEps([bad_ep])
        monkeypatch.setattr(importlib.metadata, "entry_points", lambda: fake_eps)
        monkeypatch.setattr(
            "power_sdk.plugins.registry._discover_from_local_package", list
        )
        with caplog.at_level(logging.WARNING, logger="power_sdk.plugins.registry"):
            reg = load_plugins()

        assert len(reg) == 0  # broken plugin skipped, no fallback
        assert "bad/v0" in caplog.text

    def test_local_source_discovery_registers_manifest(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Local source scan can discover plugins without package installation."""
        from tests.stubs.acme.plugin import ACME_V1_MANIFEST

        monkeypatch.setattr(importlib.metadata, "entry_points", lambda: _EmptyEps())
        monkeypatch.setattr(
            "power_sdk.plugins.registry._discover_from_local_package",
            lambda: [ACME_V1_MANIFEST],
        )
        reg = load_plugins()
        assert "acme/v1" in reg
        assert len(reg) == 1
