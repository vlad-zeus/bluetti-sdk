"""Shared pytest fixtures for the test suite."""

from __future__ import annotations

from unittest.mock import Mock

import pytest
from power_sdk.contracts.parser import ParserInterface
from power_sdk.devices.types import BlockGroupDefinition, DeviceProfile
from power_sdk.protocol.factory import ProtocolFactory


@pytest.fixture(autouse=True)
def reset_protocol_factory() -> None:
    """Reset ProtocolFactory class state between tests to prevent state leakage."""
    yield
    ProtocolFactory._reset()


# ---------------------------------------------------------------------------
# Vendor-neutral stubs — usable by any core test without importing plugins
# ---------------------------------------------------------------------------


def make_test_profile(
    model: str = "TEST_DEVICE",
    protocol: str = "v2",
) -> DeviceProfile:
    """Build a minimal DeviceProfile without importing any plugin."""
    return DeviceProfile(
        model=model,
        type_id="test",
        protocol=protocol,
        description="Test profile (no plugin dependency)",
        groups={
            "core": BlockGroupDefinition(
                name="core", blocks=[100], description="core", poll_interval=5
            ),
            "grid": BlockGroupDefinition(
                name="grid", blocks=[1300], description="grid", poll_interval=10
            ),
            "battery": BlockGroupDefinition(
                name="battery", blocks=[6000], description="battery", poll_interval=30
            ),
            "inverter": BlockGroupDefinition(
                name="inverter",
                blocks=[1100, 1400, 1500],
                description="inverter",
                poll_interval=10,
            ),
        },
    )


@pytest.fixture
def test_profile() -> DeviceProfile:
    """Minimal DeviceProfile with no plugin imports."""
    return make_test_profile()


@pytest.fixture
def mock_parser() -> Mock:
    """Stub parser that satisfies ParserInterface without any plugin import."""
    parser = Mock(spec=ParserInterface)
    parser.get_schema = Mock(return_value=None)
    parser.list_schemas = Mock(return_value={})
    parser.register_schema = Mock()
    return parser
