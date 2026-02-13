"""Domain model types."""

from enum import Enum


class BlockGroup(Enum):
    """V2 block groups."""
    CORE = "core"           # Block 100 - Dashboard
    GRID = "grid"           # Block 1300 - Grid input
    BATTERY = "battery"     # Block 6000 - Battery pack
    CELLS = "cells"         # Block 6100 - Cell details
    INVERTER = "inverter"   # Blocks 1100, 1400, 1500
