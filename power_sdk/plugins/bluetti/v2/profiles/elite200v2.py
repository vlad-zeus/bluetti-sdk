"""Elite 200 V2 Device Profile

Bluetti Elite 200 V2: 2073.6Wh, 51.2V, 2400W inverter
"""

from power_sdk.devices.types import DeviceProfile
from power_sdk.plugins.bluetti.v2.constants import V2_PROTOCOL_VERSION

from .common import BLOCK_GROUPS

ELITE200_V2_PROFILE = DeviceProfile(
    model="Elite 200 V2",
    type_id="8",
    protocol="v2",
    description="Bluetti Elite 200 V2 (2073.6Wh, 51.2V, 2400W inverter)",
    groups={
        "core": BLOCK_GROUPS["core"],
        "grid": BLOCK_GROUPS["grid"],
        "battery": BLOCK_GROUPS["battery"],
    },
    protocol_version=V2_PROTOCOL_VERSION,
)
