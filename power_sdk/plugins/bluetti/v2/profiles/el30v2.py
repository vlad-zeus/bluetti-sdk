"""Elite 30 V2 Device Profile

Bluetti Elite 30 V2: 336Wh, 25.6V, 600W inverter
"""

from power_sdk.devices.types import DeviceProfile
from power_sdk.plugins.bluetti.v2.constants import V2_PROTOCOL_VERSION

from .common import BLOCK_GROUPS

EL30V2_PROFILE = DeviceProfile(
    model="EL30V2",
    type_id="32",
    protocol="v2",
    description="Bluetti Elite 30 V2 (336Wh, 25.6V, 600W inverter)",
    groups={
        "core": BLOCK_GROUPS["core"],
        "grid": BLOCK_GROUPS["grid"],
        "battery": BLOCK_GROUPS["battery"],
    },
    protocol_version=V2_PROTOCOL_VERSION,
)
