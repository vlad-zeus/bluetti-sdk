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

from power_sdk.protocol.v2.datatypes import UInt8, UInt16, UInt32
from power_sdk.protocol.v2.transforms import scale
from .declarative import block_field, block_schema


@block_schema(
    block_id=1400,
    name="INV_LOAD_INFO",
    description="Load output info (DC loads, AC load per-phase)",
    min_length=72,  # Core fields for single-phase
    protocol_version=2000,
    schema_version="1.0.0",
    strict=False,  # Allow variable-length for multi-phase
    verification_status="smali_verified",
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

    # === DC 5V Output (8-11) ===
    load_5v_power: int = block_field(
        offset=8,
        type=UInt16(),
        unit="W",
        required=False,
        description="5V output power",
        default=0,
    )

    load_5v_current: float = block_field(
        offset=10,
        type=UInt16(),
        transform=[scale(0.1)],
        unit="A",
        required=False,
        description="5V output current",
        default=0.0,
    )

    # === DC 12V Output (12-15) ===
    load_12v_power: int = block_field(
        offset=12,
        type=UInt16(),
        unit="W",
        required=False,
        description="12V output power",
        default=0,
    )

    load_12v_current: float = block_field(
        offset=14,
        type=UInt16(),
        transform=[scale(0.1)],
        unit="A",
        required=False,
        description="12V output current",
        default=0.0,
    )

    # === DC 24V Output (16-19) ===
    load_24v_power: int = block_field(
        offset=16,
        type=UInt16(),
        unit="W",
        required=False,
        description="24V output power",
        default=0,
    )

    load_24v_current: float = block_field(
        offset=18,
        type=UInt16(),
        transform=[scale(0.1)],
        unit="A",
        required=False,
        description="24V output current",
        default=0.0,
    )

    # === DC aggregate measurements (24-27) ===
    dc_total_voltage: float = block_field(
        offset=24,
        type=UInt16(),
        transform=[scale(0.1)],
        unit="V",
        required=False,
        description="Total DC voltage (aggregate)",
        default=0.0,
    )

    dc_total_current: float = block_field(
        offset=26,
        type=UInt16(),
        transform=[scale(0.1)],
        unit="A",
        required=False,
        description="Total DC current (aggregate)",
        default=0.0,
    )

    # === AC Load Total (40-47) ===
    ac_total_power: int = block_field(
        offset=40,
        type=UInt32(),
        unit="W",
        required=True,
        description="Total AC load power",
        default=0,
    )

    ac_total_energy: float = block_field(
        offset=44,
        type=UInt32(),
        transform=[scale(0.1)],
        unit="kWh",
        required=True,
        description="Total AC load energy",
        default=0.0,
    )

    sys_phase_number: int = block_field(
        offset=59,
        type=UInt8(),
        required=False,
        description="System phase number (1 = single-phase, 3 = three-phase)",
        default=1,
    )

    # === Phase 0 AC Load (60-71, 12 bytes per phase) ===
    phase_0_power: int = block_field(
        offset=60,
        type=UInt16(),
        unit="W",
        required=True,
        description="Phase 0 AC load power",
        default=0,
    )

    phase_0_voltage: float = block_field(
        offset=62,
        type=UInt16(),
        transform=[scale(0.1)],
        unit="V",
        required=True,
        description="Phase 0 AC load voltage",
        default=0.0,
    )

    phase_0_current: float = block_field(
        offset=64,
        type=UInt16(),
        transform=[scale(0.1)],
        unit="A",
        required=True,
        description="Phase 0 AC load current",
        default=0.0,
    )

    phase_0_apparent: int = block_field(
        offset=66,
        type=UInt16(),
        unit="VA",
        required=False,
        description="Phase 0 apparent power",
        default=0,
    )

    # Note: Phase 1 and Phase 2 data (if sysPhaseNumber == 3)
    # starts at offset 72 and 84
    # Each phase: 12 bytes
    # (voltage, current, power, apparent_power, reactive_power, power_factor)
    # Not included in this baseline schema - use variable-length parsing


# Generate canonical BlockSchema object
BLOCK_1400_DECLARATIVE_SCHEMA = InvLoadInfoBlock.to_schema()  # type: ignore[attr-defined]
