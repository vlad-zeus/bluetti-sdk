"""Pipeline and write-policy specification dataclasses for runtime DSL."""
from __future__ import annotations

from dataclasses import dataclass

VALID_MODES: frozenset[str] = frozenset({"pull", "push"})


@dataclass
class PipelineSpec:
    """Named pipeline — a reusable device configuration template.

    Declares which transport and vendor/protocol plugin handle a device,
    and whether the device should be driven in pull (poll) or push
    (subscription callback) mode.
    """

    name: str
    mode: str = "pull"      # "pull" | "push"
    transport: str = ""     # TransportFactory key, e.g. "mqtt"
    vendor: str = ""        # PluginRegistry vendor key
    protocol: str = ""      # PluginRegistry protocol key


@dataclass
class WritePolicySpec:
    """Write-path policy declared per pipeline or per device.

    Controls whether write commands are allowed and whether device
    identity validation is required before issuing writes.
    """

    force_allowed: bool = False
    """If True, callers may bypass requires_device_validation_for_write."""

    require_validation: bool = True
    """If True, writes require a device identity read before proceeding."""
