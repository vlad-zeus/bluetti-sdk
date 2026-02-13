"""Block 1300 - INV_GRID_INFO Schema

Grid input monitoring data.
Tracks grid voltage, frequency, current, and power.
"""

from ..protocol.v2.datatypes import Int16, UInt16, UInt32
from ..protocol.v2.schema import BlockSchema, Field

BLOCK_1300_SCHEMA = BlockSchema(
    block_id=1300,
    name="INV_GRID_INFO",
    description="Grid input monitoring (voltage, frequency, power)",
    min_length=32,
    protocol_version=2000,
    schema_version="1.0.0",
    strict=True,
    fields=[
        # === Grid AC Parameters ===
        Field(
            name="frequency",
            offset=0,
            type=UInt16(),
            transform=["scale:0.1"],
            unit="Hz",
            required=True,
            description="Grid frequency (typically 50Hz or 60Hz)",
        ),
        # === Phase 0 (Main Phase) ===
        Field(
            name="phase_0_power",
            offset=26,
            type=Int16(),
            transform=["abs"],
            unit="W",
            required=True,
            description="Phase 0 power (absolute value)",
        ),
        Field(
            name="phase_0_voltage",
            offset=28,
            type=UInt16(),
            transform=["scale:0.1"],
            unit="V",
            required=True,
            description="Phase 0 voltage",
        ),
        Field(
            name="phase_0_current",
            offset=30,
            type=Int16(),
            transform=["abs", "scale:0.1"],
            unit="A",
            required=True,
            description="Phase 0 current (absolute value)",
        ),
        # === Optional: Three-Phase Support ===
        # Note: Most residential devices are single-phase
        # These fields may be zero or unavailable
        Field(
            name="phase_1_voltage",
            offset=2,
            type=UInt16(),
            transform=["scale:0.1"],
            unit="V",
            required=False,
            description="Phase 1 voltage (3-phase systems)",
        ),
        Field(
            name="phase_2_voltage",
            offset=4,
            type=UInt16(),
            transform=["scale:0.1"],
            unit="V",
            required=False,
            description="Phase 2 voltage (3-phase systems)",
        ),
        # === Energy Counters ===
        # Note: Offsets need to be verified from actual data
        # These are extended fields that may not always be present
        Field(
            name="total_charge_energy",
            offset=6,
            type=UInt32(),
            transform=["scale:0.1"],
            unit="kWh",
            required=False,
            description="Total energy charged from grid",
        ),
        Field(
            name="total_feedback_energy",
            offset=10,
            type=UInt32(),
            transform=["scale:0.1"],
            unit="kWh",
            required=False,
            description="Total energy fed back to grid",
        ),
    ],
)
