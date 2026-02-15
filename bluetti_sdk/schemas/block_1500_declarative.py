"""Block 1500 - INV_INV_INFO Declarative Schema

Declarative version of Block 1500 using the declarative schema API.
Inverter output information including frequency, energy, and per-phase output data.

Usage:
    # Get generated BlockSchema
    schema = InvInvInfoBlock.to_schema()

    # Register with parser
    parser.register_schema(schema)

    # Parse block
    parsed = parser.parse_block(1500, data)

    # Type-safe access (IDE autocomplete works!)
    frequency = parsed.values['frequency']
    total_energy = parsed.values['total_energy']
"""

from dataclasses import dataclass

from ..protocol.v2.datatypes import Int16, UInt8, UInt16, UInt32
from ..protocol.v2.transforms import abs_, scale
from .declarative import block_field, block_schema


@block_schema(
    block_id=1500,
    name="INV_INV_INFO",
    description="Inverter output info (frequency, energy, per-phase data)",
    min_length=30,  # Core fields for single-phase
    protocol_version=2000,
    schema_version="1.0.0",
    strict=False,  # Allow variable-length for multi-phase
)
@dataclass
class InvInvInfoBlock:
    """Inverter output information for Elite V2 devices.

    Primary data source for monitoring inverter frequency, output energy,
    and per-phase inverter output (voltage, current, power).

    Note: Per-phase data is variable-length based on sysPhaseNumber.
    This schema includes Phase 0 (single-phase baseline).
    """

    # === Global Parameters (0-17) ===
    frequency: float = block_field(
        offset=0,
        type=UInt16(),
        transform=[scale(0.1)],
        unit="Hz",
        required=True,
        description="Inverter output frequency",
        default=0.0,
    )

    total_energy: float = block_field(
        offset=14,
        type=UInt32(),
        transform=[scale(0.1)],
        unit="kWh",
        required=True,
        description="Total inverter output energy",
        default=0.0,
    )

    sys_phase_number: int = block_field(
        offset=2,
        type=UInt8(),
        required=True,
        description="System phase number (1 = single-phase, 3 = three-phase)",
        default=1,
    )

    # === Phase 0 Output (18-29, 12 bytes per phase) ===
    phase_0_voltage: float = block_field(
        offset=18,
        type=UInt16(),
        transform=[scale(0.1)],
        unit="V",
        required=True,
        description="Phase 0 inverter output voltage",
        default=0.0,
    )

    phase_0_current: float = block_field(
        offset=20,
        type=Int16(),
        transform=[abs_(), scale(0.1)],
        unit="A",
        required=True,
        description="Phase 0 inverter output current",
        default=0.0,
    )

    phase_0_power: int = block_field(
        offset=22,
        type=Int16(),
        transform=[abs_()],
        unit="W",
        required=True,
        description="Phase 0 inverter output power",
        default=0,
    )

    phase_0_apparent_power: int = block_field(
        offset=24,
        type=UInt16(),
        unit="VA",
        required=False,
        description="Phase 0 apparent power",
        default=0,
    )

    phase_0_reactive_power: int = block_field(
        offset=26,
        type=Int16(),
        unit="var",
        required=False,
        description="Phase 0 reactive power",
        default=0,
    )

    phase_0_power_factor: float = block_field(
        offset=28,
        type=Int16(),
        transform=[scale(0.001)],
        required=False,
        description="Phase 0 power factor",
        default=0.0,
    )

    # Note: Phase 1 and Phase 2 data (if sys_phase_number == 3)
    # starts at offset 30 and 42
    # Each phase: 12 bytes
    # (voltage, current, power, apparent_power, reactive_power, power_factor)
    # Not included in this baseline schema - use variable-length parsing


# Generate canonical BlockSchema object
BLOCK_1500_DECLARATIVE_SCHEMA = InvInvInfoBlock.to_schema()  # type: ignore[attr-defined]
