"""Device Profile Registry

Central registry for all device profiles.
"""

from typing import Dict

from power_sdk.devices.types import DeviceProfile

from .el30v2 import EL30V2_PROFILE
from .el100v2 import EL100V2_PROFILE
from .elite200v2 import ELITE200_V2_PROFILE

# ============================================================================
# Device Registry
# ============================================================================

DEVICE_PROFILES: Dict[str, DeviceProfile] = {
    # Elite V2 series
    "EL30V2": EL30V2_PROFILE,
    "EL100V2": EL100V2_PROFILE,
    "ELITE200V2": ELITE200_V2_PROFILE,
    "Elite 200 V2": ELITE200_V2_PROFILE,
    # Aliases
    "Elite 30 V2": EL30V2_PROFILE,
    "Elite 100 V2": EL100V2_PROFILE,
}


def get_device_profile(model: str) -> DeviceProfile:
    """Get device profile by model name.

    Args:
        model: Device model name

    Returns:
        DeviceProfile

    Raises:
        ValueError: If model not found
    """
    if model not in DEVICE_PROFILES:
        raise ValueError(
            f"Unknown device model: {model}. Available: {list(DEVICE_PROFILES.keys())}"
        )

    return DEVICE_PROFILES[model]


def list_device_models() -> list[str]:
    """List all available device models.

    Returns:
        List of device model names
    """
    return list(DEVICE_PROFILES.keys())
