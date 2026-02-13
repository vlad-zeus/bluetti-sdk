"""Device configuration types."""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class BlockGroupDefinition:
    """Definition of a block group."""
    name: str
    blocks: List[int]  # Block IDs in this group
    description: str
    poll_interval: int = 5  # Recommended poll interval (seconds)


@dataclass
class DeviceProfile:
    """Device-specific configuration.

    This is configuration data, not code.
    """
    model: str
    type_id: str
    protocol: str  # "v1" or "v2"
    groups: Dict[str, BlockGroupDefinition]  # Available groups
    description: str
