"""Elite 100 V2 Device Profile

Bluetti Elite 100 V2: 1056Wh, 51.2V, 1000W inverter
"""

from power_sdk.devices.types import DeviceProfile
from power_sdk.plugins.bluetti.v2.constants import V2_PROTOCOL_VERSION

from .common import BLOCK_GROUPS

EL100V2_PROFILE = DeviceProfile(
    model="EL100V2",
    type_id="31",
    protocol="v2",
    description="Bluetti Elite 100 V2 (1056Wh, 51.2V, 1000W inverter)",
    groups={
        "core": BLOCK_GROUPS["core"],
        "grid": BLOCK_GROUPS["grid"],
        "battery": BLOCK_GROUPS["battery"],
        "cells": BLOCK_GROUPS["cells"],
        "inverter": BLOCK_GROUPS["inverter"],
    },
    protocol_version=V2_PROTOCOL_VERSION,
)
