"""Device Profiles - Configuration Data

DEPRECATED: This module is deprecated. Import from bluetti_sdk.devices.profiles instead.

Device-specific configurations without code.
Defines which block groups are available for each device model.
"""

import warnings

# Re-export from new location for backward compatibility
from ..devices.profiles import (
    DEVICE_PROFILES,
    EL100V2_PROFILE,
    EL30V2_PROFILE,
    ELITE200_V2_PROFILE,
    V2_BLOCK_GROUPS,
    get_device_profile,
    is_v2_device,
    list_device_models,
)

# Show deprecation warning when this module is imported
warnings.warn(
    "bluetti_sdk.models.profiles is deprecated. "
    "Use bluetti_sdk.devices.profiles instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "V2_BLOCK_GROUPS",
    "EL30V2_PROFILE",
    "EL100V2_PROFILE",
    "ELITE200_V2_PROFILE",
    "DEVICE_PROFILES",
    "get_device_profile",
    "is_v2_device",
    "list_device_models",
]
