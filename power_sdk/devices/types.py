"""Device configuration types."""

from dataclasses import dataclass


@dataclass
class BlockGroupDefinition:
    """Definition of a block group."""

    name: str
    blocks: list[int]  # Block IDs in this group
    description: str
    # NOTE: Per-group poll_interval is declared here for future use but is NOT
    # currently consumed by the runtime. All groups poll at DeviceRuntime.poll_interval.
    # See: power_sdk/runtime/device.py
    poll_interval: int = 5


@dataclass
class DeviceProfile:
    """Device-specific configuration.

    This is configuration data, not code.
    """

    model: str
    type_id: str
    protocol: str  # e.g. "v2"
    groups: dict[str, BlockGroupDefinition]  # Available groups
    description: str
    protocol_version: int = 0  # Protocol version (e.g. 2000 for Bluetti V2)
