"""Common V2 Block Group Definitions

Shared block groups used across different V2 device models.
"""

from ..types import BlockGroupDefinition

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
