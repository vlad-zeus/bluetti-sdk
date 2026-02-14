"""Elite 100 V2 Device Profile

Bluetti Elite 100 V2: 1056Wh, 51.2V, 1000W inverter
"""

from ..types import DeviceProfile
from .common import V2_BLOCK_GROUPS

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
