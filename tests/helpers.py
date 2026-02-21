"""Shared test helpers — plain functions, not fixtures.

Import directly in test modules::

    from tests.helpers import make_parsed_block, make_device_runtime, make_registry
"""

from unittest.mock import Mock

from power_sdk.contracts.types import ParsedRecord
from power_sdk.runtime import DeviceRuntime, RuntimeRegistry


def make_parsed_block(block_id: int, **overrides: object) -> ParsedRecord:
    """Create a minimal ParsedRecord stub for unit tests."""
    defaults: dict = dict(
        block_id=block_id,
        name=f"BLOCK_{block_id}",
        values={"ok": True},
        raw=b"",
        length=0,
        protocol_version=None,
        schema_version="1.0.0",
        timestamp=0.0,
    )
    defaults.update(overrides)
    return ParsedRecord(**defaults)


def make_device_runtime(
    device_id: str = "dev1",
    poll_interval: float = 0.01,
    mode: str = "pull",
    with_connect_once: bool = True,
    vendor: str = "acme",
    protocol: str = "v1",
    profile_id: str = "DEV1",
) -> DeviceRuntime:
    """Create a DeviceRuntime with a fully-mocked Client for unit tests.

    Args:
        device_id: Identifier for the device.
        poll_interval: Polling interval in seconds (use small values in tests).
        mode: Execution mode — "pull" or "push".
        with_connect_once: When True, adds a connect_once mock (required by
            reconnect tests that call client.connect_once()).
        vendor: Vendor string stored on the runtime.
        protocol: Protocol string stored on the runtime.
        profile_id: Profile identifier stored on the runtime.
    """
    client = Mock()
    client.profile.model = "M"
    client.connect = Mock()
    client.disconnect = Mock()
    if with_connect_once:
        client.connect_once = Mock()
    client.read_group = Mock(return_value=[])
    client.get_device_state = Mock(return_value={})
    return DeviceRuntime(
        device_id=device_id,
        client=client,
        vendor=vendor,
        protocol=protocol,
        profile_id=profile_id,
        transport_key="stub",
        poll_interval=poll_interval,
        mode=mode,
    )


def make_registry(*runtimes: DeviceRuntime) -> RuntimeRegistry:
    """Wrap one or more DeviceRuntime instances in a RuntimeRegistry."""
    return RuntimeRegistry(list(runtimes))
