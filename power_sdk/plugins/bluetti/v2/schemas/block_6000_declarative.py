"""Block 6000 - PACK_MAIN_INFO Declarative Schema

Declarative version of Block 6000 using the declarative schema API.
Battery pack main information and status - detailed health, temperature, and protection.

Usage:
    # Get generated BlockSchema
    schema = PackMainInfoBlock.to_schema()

    # Register with parser
    parser.register_schema(schema)

    # Parse block
    parsed = parser.parse_block(6000, data)

    # Type-safe access (IDE autocomplete works!)
    voltage = parsed.values['voltage']
    soc = parsed.values['soc']
"""

from dataclasses import dataclass

from ..protocol.datatypes import UInt8, UInt16
from ..protocol.transforms import minus, scale
from .declarative import block_field, block_schema


@block_schema(
    block_id=6000,
    name="PACK_MAIN_INFO",
    description="Battery pack detailed status and health",
    min_length=64,
    protocol_version=2000,
    schema_version="1.0.0",
    strict=False,  # Allow partial data
    verification_status="smali_verified",
)
@dataclass
class PackMainInfoBlock:
    """Battery pack detailed status for Elite V2 devices.

    Comprehensive battery monitoring including voltage, current, SOC, SOH,
    temperatures, charge/discharge limits, and protection status.
    """

    # === Pack Configuration ===
    pack_volt_type: int = block_field(
        offset=0,
        type=UInt16(),
        description="Pack voltage type",
        default=0,
    )

    pack_count: int = block_field(
        offset=3,
        type=UInt8(),
        description="Number of battery packs",
        default=0,
    )

    pack_online: int = block_field(
        offset=4,
        type=UInt16(),
        description="Pack online status bitmap",
        default=0,
    )

    # === Battery Status ===
    voltage: float = block_field(
        offset=6,
        type=UInt16(),
        transform=[scale(0.1)],
        unit="V",
        required=True,
        description="Total pack voltage",
        default=0.0,
    )

    current: float = block_field(
        offset=8,
        type=UInt16(),
        transform=[scale(0.1)],
        unit="A",
        required=True,
        description="Total pack current",
        default=0.0,
    )

    power: int = block_field(
        offset=10,
        type=UInt16(),
        unit="W",
        description="Pack power (computed)",
        default=0,
    )

    soc: int = block_field(
        offset=11,
        type=UInt8(),
        unit="%",
        required=True,
        description="State of charge",
        default=0,
    )

    soh: int = block_field(
        offset=13,
        type=UInt8(),
        unit="%",
        required=True,
        description="State of health",
        default=100,
    )

    # === Temperature ===
    temp_avg: int = block_field(
        offset=14,
        type=UInt16(),
        transform=[minus(40)],
        unit="°C",
        description="Average temperature",
        default=0,
    )

    # === Operating Status ===
    running_status: int = block_field(
        offset=17,
        type=UInt8(),
        description="Running status code",
        default=0,
    )

    charging_status: int = block_field(
        offset=19,
        type=UInt8(),
        description="Charging status code",
        default=0,
    )

    # === Charge/Discharge Limits ===
    max_charge_voltage: float = block_field(
        offset=20,
        type=UInt16(),
        transform=[scale(0.1)],
        unit="V",
        description="Maximum charge voltage",
        default=0.0,
    )

    max_charge_current: float = block_field(
        offset=22,
        type=UInt16(),
        transform=[scale(0.1)],
        unit="A",
        description="Maximum charge current",
        default=0.0,
    )

    max_discharge_current: float = block_field(
        offset=24,
        type=UInt16(),
        transform=[scale(0.1)],
        unit="A",
        description="Maximum discharge current",
        default=0.0,
    )

    # === MOS Status ===
    pack_mos: int = block_field(
        offset=32,
        type=UInt16(),
        description="Pack MOS status bitmap",
        default=0,
    )

    # === Time Estimates ===
    time_to_full: int = block_field(
        offset=34,
        type=UInt16(),
        unit="min",
        description="Estimated time to full charge",
        default=0,
    )

    time_to_empty: int = block_field(
        offset=36,
        type=UInt16(),
        unit="min",
        description="Estimated time to empty",
        default=0,
    )

    # === Cell Information ===
    cell_count: int = block_field(
        offset=38,
        type=UInt16(),
        description="Number of cells in pack",
        default=0,
    )

    cycles: int = block_field(
        offset=40,
        type=UInt16(),
        description="Charge/discharge cycle count",
        default=0,
    )

    # === Temperature Min/Max ===
    temp_max: int = block_field(
        offset=50,
        type=UInt16(),
        transform=[minus(40)],
        unit="°C",
        description="Maximum cell temperature",
        default=0,
    )

    temp_min: int = block_field(
        offset=52,
        type=UInt16(),
        transform=[minus(40)],
        unit="°C",
        description="Minimum cell temperature",
        default=0,
    )

    # === Protection & Faults ===
    # Note: Protection status at offset 58-61 is complex (4-byte bitmap)
    pack_fault_bits: int = block_field(
        offset=62,
        type=UInt16(),
        description="Pack fault status bitmap",
        default=0,
    )


# Generate canonical BlockSchema object
BLOCK_6000_DECLARATIVE_SCHEMA = PackMainInfoBlock.to_schema()  # type: ignore[attr-defined]
