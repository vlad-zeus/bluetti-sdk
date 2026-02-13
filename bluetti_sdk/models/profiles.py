"""Device Profiles - Configuration Data

Device-specific configurations without code.
Defines which block groups are available for each device model.
"""

from ..devices.types import BlockGroupDefinition, DeviceProfile

# ============================================================================
# V2 Block Group Definitions
# ============================================================================

V2_BLOCK_GROUPS = {
    "core": BlockGroupDefinition(
        name="core",
        blocks=[100],
        description="Main dashboard (SOC, power flows, energy)",
        poll_interval=5,
    ),
    "grid": BlockGroupDefinition(
        name="grid",
        blocks=[1300],
        description="Grid voltage, frequency, power",
        poll_interval=5,
    ),
    "battery": BlockGroupDefinition(
        name="battery",
        blocks=[6000],
        description="Battery pack status",
        poll_interval=10,
    ),
    "cells": BlockGroupDefinition(
        name="cells",
        blocks=[6100],
        description="Individual cell voltages/temps (expensive!)",
        poll_interval=60,  # Poll rarely
    ),
    "inverter": BlockGroupDefinition(
        name="inverter",
        blocks=[1100, 1400, 1500],
        description="Inverter details",
        poll_interval=10,
    ),
}


# ============================================================================
# Device Profiles
# ============================================================================

EL30V2_PROFILE = DeviceProfile(
    model="EL30V2",
    type_id="32",
    protocol="v2",
    description="Bluetti Elite 30 V2 (336Wh, 25.6V, 600W inverter)",
    groups={
        "core": V2_BLOCK_GROUPS["core"],
        "grid": V2_BLOCK_GROUPS["grid"],
        "battery": V2_BLOCK_GROUPS["battery"],
    },
)

EL100V2_PROFILE = DeviceProfile(
    model="EL100V2",
    type_id="31",
    protocol="v2",
    description="Bluetti Elite 100 V2 (1056Wh, 51.2V, 1000W inverter)",
    groups={
        "core": V2_BLOCK_GROUPS["core"],
        "grid": V2_BLOCK_GROUPS["grid"],
        "battery": V2_BLOCK_GROUPS["battery"],
        "cells": V2_BLOCK_GROUPS["cells"],
        "inverter": V2_BLOCK_GROUPS["inverter"],
    },
)

ELITE200_V2_PROFILE = DeviceProfile(
    model="Elite 200 V2",
    type_id="8",
    protocol="v2",
    description="Bluetti Elite 200 V2 (2073.6Wh, 51.2V, 2400W inverter)",
    groups={
        "core": V2_BLOCK_GROUPS["core"],
        "grid": V2_BLOCK_GROUPS["grid"],
        "battery": V2_BLOCK_GROUPS["battery"],
    },
)


# ============================================================================
# Device Registry
# ============================================================================

DEVICE_PROFILES = {
    # Elite V2 series
    "EL30V2": EL30V2_PROFILE,
    "EL100V2": EL100V2_PROFILE,
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


def is_v2_device(model: str) -> bool:
    """Check if device uses V2 protocol.

    Args:
        model: Device model name

    Returns:
        True if V2 device
    """
    try:
        profile = get_device_profile(model)
        return profile.protocol == "v2"
    except ValueError:
        return False
