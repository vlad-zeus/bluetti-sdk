"""Block 1400 - INV_LOAD_INFO Declarative Schema

Declarative version of Block 1400 using the declarative schema API.
Load output information including DC loads (5V/12V/24V) and AC load per-phase data.

Usage:
    # Get generated BlockSchema
    schema = InvLoadInfoBlock.to_schema()

    # Register with parser
    parser.register_schema(schema)

    # Parse block
    parsed = parser.parse_block(1400, data)

    # Type-safe access (IDE autocomplete works!)
    dc_total_power = parsed.values['dc_total_power']
    load_5v_power = parsed.values['load_5v_power']
"""

from dataclasses import dataclass

from ..protocol.v2.datatypes import Int16, UInt16, UInt32
from ..protocol.v2.transforms import abs_, scale
from .declarative import block_field, block_schema


@block_schema(
    block_id=1400,
    name="INV_LOAD_INFO",
    description="Load output info (DC loads, AC load per-phase)",
    min_length=72,  # Core fields for single-phase
    protocol_version=2000,
    schema_version="1.0.0",
    strict=False,  # Allow variable-length for multi-phase
)
@dataclass
class InvLoadInfoBlock:
    """Load output information for Elite V2 devices.

    Primary data source for monitoring DC load outputs (5V, 12V, 24V)
    and AC load per-phase data (voltage, current, power).

    Note: Per-phase AC data is variable-length based on sysPhaseNumber.
    This schema includes Phase 0 (single-phase baseline).
    """

    # === DC Load Total (0-13) ===
    dc_total_power: int = block_field(
        offset=0,
        type=UInt32(),
        unit="W",
        required=True,
        description="Total DC load power",
        default=0,
    )

    dc_total_energy: float = block_field(
        offset=4,
        type=UInt32(),
        transform=[scale(0.1)],
        unit="kWh",
        required=True,
        description="Total DC load energy",
        default=0.0,
    )

    # === DC 5V Output (14-23) ===
    load_5v_power: int = block_field(
        offset=14,
        type=UInt16(),
        unit="W",
        required=False,
        description="5V output power",
        default=0,
    )

    load_5v_energy: float = block_field(
        offset=16,
        type=UInt32(),
        transform=[scale(0.1)],
        unit="kWh",
        required=False,
        description="5V output energy",
        default=0.0,
    )

    # === DC 12V Output (24-33) ===
    load_12v_power: int = block_field(
        offset=24,
        type=UInt16(),
        unit="W",
        required=False,
        description="12V output power",
        default=0,
    )

    load_12v_energy: float = block_field(
        offset=26,
        type=UInt32(),
        transform=[scale(0.1)],
        unit="kWh",
        required=False,
        description="12V output energy",
        default=0.0,
    )

    # === DC 24V Output (34-43) ===
    load_24v_power: int = block_field(
        offset=34,
        type=UInt16(),
        unit="W",
        required=False,
        description="24V output power",
        default=0,
    )

    load_24v_energy: float = block_field(
        offset=36,
        type=UInt32(),
        transform=[scale(0.1)],
        unit="kWh",
        required=False,
        description="24V output energy",
        default=0.0,
    )

    # === AC Load Total (44-59) ===
    ac_total_power: int = block_field(
        offset=44,
        type=UInt32(),
        unit="W",
        required=True,
        description="Total AC load power",
        default=0,
    )

    ac_total_energy: float = block_field(
        offset=48,
        type=UInt32(),
        transform=[scale(0.1)],
        unit="kWh",
        required=True,
        description="Total AC load energy",
        default=0.0,
    )

    # === Phase 0 AC Load (60-71, 12 bytes per phase) ===
    phase_0_voltage: float = block_field(
        offset=60,
        type=UInt16(),
        transform=[scale(0.1)],
        unit="V",
        required=True,
        description="Phase 0 AC load voltage",
        default=0.0,
    )

    phase_0_current: float = block_field(
        offset=62,
        type=Int16(),
        transform=[abs_(), scale(0.1)],
        unit="A",
        required=True,
        description="Phase 0 AC load current",
        default=0.0,
    )

    phase_0_power: int = block_field(
        offset=64,
        type=Int16(),
        transform=[abs_()],
        unit="W",
        required=True,
        description="Phase 0 AC load power",
        default=0,
    )

    phase_0_apparent_power: int = block_field(
        offset=66,
        type=UInt16(),
        unit="VA",
        required=False,
        description="Phase 0 apparent power",
        default=0,
    )

    phase_0_reactive_power: int = block_field(
        offset=68,
        type=Int16(),
        unit="var",
        required=False,
        description="Phase 0 reactive power",
        default=0,
    )

    phase_0_power_factor: float = block_field(
        offset=70,
        type=Int16(),
        transform=[scale(0.001)],
        required=False,
        description="Phase 0 power factor",
        default=0.0,
    )

    # Note: Phase 1 and Phase 2 data (if sysPhaseNumber == 3)
    # starts at offset 72 and 84
    # Each phase: 12 bytes
    # (voltage, current, power, apparent_power, reactive_power, power_factor)
    # Not included in this baseline schema - use variable-length parsing


# Generate canonical BlockSchema object
BLOCK_1400_DECLARATIVE_SCHEMA = InvLoadInfoBlock.to_schema()  # type: ignore[attr-defined]
