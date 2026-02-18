"""Elite 30 V2 Device Profile

Bluetti Elite 30 V2: 336Wh, 25.6V, 600W inverter
"""

from power_sdk.devices.types import DeviceProfile
from .common import V2_BLOCK_GROUPS

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
