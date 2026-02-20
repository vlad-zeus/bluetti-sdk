"""Block 1300 - INV_GRID_INFO Declarative Schema

Declarative version of Block 1300 using the declarative schema API.
Grid input monitoring data - tracks voltage, frequency, current, and power.

Usage:
    # Get generated BlockSchema
    schema = InvGridInfoBlock.to_schema()

    # Register with parser
    parser.register_schema(schema)

    # Parse block
    parsed = parser.parse_block(1300, data)

    # Type-safe access (IDE autocomplete works!)
    frequency = parsed.values['frequency']
    voltage = parsed.values['phase_0_voltage']
"""

from dataclasses import dataclass

from ..protocol.datatypes import Int16, UInt16, UInt32
from ..protocol.transforms import abs_, scale
from .declarative import block_field, block_schema


@block_schema(
    block_id=1300,
    name="INV_GRID_INFO",
    description="Grid input monitoring (voltage, frequency, power)",
    min_length=32,
    protocol_version=2000,
    schema_version="1.0.0",
    strict=True,
    verification_status="verified_reference",
)
@dataclass
class InvGridInfoBlock:
    """Grid input monitoring for Elite V2 devices.

    Primary data source for monitoring grid voltage, frequency, and power flows.
    """

    # === Grid AC Parameters ===
    frequency: float = block_field(
        offset=0,
        type=UInt16(),
        transform=[scale(0.1)],
        unit="Hz",
        required=True,
        description="Grid frequency (typically 50Hz or 60Hz)",
        default=0.0,
    )

    # === Three-Phase Support (Optional) ===
    # Note: Most residential devices are single-phase
    # These fields may be zero or unavailable
    phase_1_voltage: float = block_field(
        offset=2,
        type=UInt16(),
        transform=[scale(0.1)],
        unit="V",
        required=False,
        description="Phase 1 voltage (3-phase systems)",
        default=0.0,
    )

    phase_2_voltage: float = block_field(
        offset=4,
        type=UInt16(),
        transform=[scale(0.1)],
        unit="V",
        required=False,
        description="Phase 2 voltage (3-phase systems)",
        default=0.0,
    )

    # === Energy Counters ===
    # Note: These are extended fields that may not always be present
    total_charge_energy: float = block_field(
        offset=6,
        type=UInt32(),
        transform=[scale(0.1)],
        unit="kWh",
        required=False,
        description="Total energy charged from grid",
        default=0.0,
    )

    total_feedback_energy: float = block_field(
        offset=10,
        type=UInt32(),
        transform=[scale(0.1)],
        unit="kWh",
        required=False,
        description="Total energy fed back to grid",
        default=0.0,
    )

    # === Phase 0 (Main Phase) ===
    phase_0_power: int = block_field(
        offset=26,
        type=Int16(),
        transform=[abs_()],
        unit="W",
        required=True,
        description="Phase 0 power (absolute value)",
        default=0,
    )

    phase_0_voltage: float = block_field(
        offset=28,
        type=UInt16(),
        transform=[scale(0.1)],
        unit="V",
        required=True,
        description="Phase 0 voltage",
        default=0.0,
    )

    phase_0_current: float = block_field(
        offset=30,
        type=Int16(),
        transform=[abs_(), scale(0.1)],
        unit="A",
        required=True,
        description="Phase 0 current (absolute value)",
        default=0.0,
    )


# Generate canonical BlockSchema object
BLOCK_1300_DECLARATIVE_SCHEMA = InvGridInfoBlock.to_schema()  # type: ignore[attr-defined]
