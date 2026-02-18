"""Shared pytest fixtures for the test suite."""

from __future__ import annotations

import pytest
from power_sdk.protocol.factory import ProtocolFactory


@pytest.fixture(autouse=True)
def reset_protocol_factory() -> None:
    """Reset ProtocolFactory class state between tests to prevent state leakage.

    ProtocolFactory uses class-level _builders and _bootstrapped vars.
    Without reset, a test that calls register() or triggers bootstrap
    would pollute subsequent tests.
    """
    yield
    ProtocolFactory._reset()
