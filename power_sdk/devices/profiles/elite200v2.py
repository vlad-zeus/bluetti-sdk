"""Elite 200 V2 Device Profile

Bluetti Elite 200 V2: 2073.6Wh, 51.2V, 2400W inverter
"""

from ..types import DeviceProfile
from .common import V2_BLOCK_GROUPS

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
