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

from ..protocol.datatypes import UInt8, UInt16, UInt32
from ..protocol.transforms import scale
from .declarative import block_field, block_schema


@block_schema(
    block_id=1500,
    name="INV_INV_INFO",
    description="Inverter output info (frequency, energy, per-phase data)",
    min_length=30,  # Core fields for single-phase
    protocol_version=2000,
    schema_version="1.0.0",
    strict=False,  # Allow variable-length for multi-phase
    verification_status="verified_reference",
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
        offset=2,
        type=UInt32(),
        transform=[scale(0.1)],
        unit="kWh",
        required=True,
        description="Total inverter output energy",
        default=0.0,
    )

    sys_phase_number: int = block_field(
        offset=17,
        type=UInt8(),
        required=True,
        description="System phase number (1 = single-phase, 3 = three-phase)",
        default=1,
    )

    # === Phase 0 Output (18-29, 12 bytes per phase) ===
    phase_0_work_status: int = block_field(
        offset=19,
        type=UInt8(),
        required=False,
        description="Phase 0 work status code",
        default=0,
    )

    phase_0_power: int = block_field(
        offset=20,
        type=UInt16(),
        unit="W",
        required=True,
        description="Phase 0 inverter output power",
        default=0,
    )

    phase_0_voltage: float = block_field(
        offset=22,
        type=UInt16(),
        transform=[scale(0.1)],
        unit="V",
        required=True,
        description="Phase 0 inverter output voltage",
        default=0.0,
    )

    phase_0_current: float = block_field(
        offset=24,
        type=UInt16(),
        transform=[scale(0.1)],
        unit="A",
        required=False,
        description="Phase 0 inverter output current",
        default=0.0,
    )

    # Note: Phase 1 and Phase 2 data (if sys_phase_number == 3)
    # starts at offset 30 and 42
    # Each phase: 12 bytes
    # (reserved, work_status, power, voltage, current, ...)
    # Not included in this baseline schema - use variable-length parsing


# Generate canonical BlockSchema object
BLOCK_1500_DECLARATIVE_SCHEMA = InvInvInfoBlock.to_schema()  # type: ignore[attr-defined]
