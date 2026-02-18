"""Device Profiles Package

Device-specific configurations organized by model.

Each model has its own module with profile definition.
The registry module provides access to all profiles.

Usage:
    from power_sdk.devices.profiles import get_device_profile

    profile = get_device_profile("EL100V2")
    print(profile.description)
"""

from .common import V2_BLOCK_GROUPS
from .el30v2 import EL30V2_PROFILE
from .el100v2 import EL100V2_PROFILE
from .elite200v2 import ELITE200_V2_PROFILE
from .registry import (
    DEVICE_PROFILES,
    get_device_profile,
    is_v2_device,
    list_device_models,
)

__all__ = [
    "DEVICE_PROFILES",
    "EL30V2_PROFILE",
    "EL100V2_PROFILE",
    "ELITE200_V2_PROFILE",
    "V2_BLOCK_GROUPS",
    "get_device_profile",
    "is_v2_device",
    "list_device_models",
]

