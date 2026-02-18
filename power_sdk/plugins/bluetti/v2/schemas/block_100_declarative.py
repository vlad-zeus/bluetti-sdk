"""Block 100 - APP_HOME_DATA Declarative Schema

Declarative version of Block 100 using the declarative schema API.
This demonstrates type-safe block definitions with IDE autocomplete support.

Usage:
    # Get generated BlockSchema
    schema = AppHomeDataBlock.to_schema()

    # Register with parser
    parser.register_schema(schema)

    # Parse block
    parsed = parser.parse_block(100, data)

    # Type-safe access (IDE autocomplete works!)
    voltage = parsed.values['pack_voltage']
"""

from dataclasses import dataclass

from power_sdk.protocol.v2.datatypes import Int32, String, UInt16, UInt32
from power_sdk.protocol.v2.transforms import minus, scale
from .declarative import block_field, block_schema


@block_schema(
    block_id=100,
    name="APP_HOME_DATA",
    description="Main dashboard data (SOC, power flows, energy totals)",
    min_length=120,  # Core fields, extended fields optional
    protocol_version=2000,
    schema_version="1.0.0",
    strict=False,  # Allow partial data for older firmware
    verification_status="smali_verified",
)
@dataclass
class AppHomeDataBlock:
    """Main dashboard data for Elite V2 devices.

    Primary data source for monitoring power flows, SOC, and energy totals.
    """

    # === Battery Status (0-19) ===
    pack_voltage: float = block_field(
        offset=0,
        type=UInt16(),
        transform=[scale(0.1)],
        unit="V",
        required=True,
        description="Total pack voltage",
        default=0.0,
    )

    pack_current: float = block_field(
        offset=2,
        type=UInt16(),
        transform=[scale(0.1)],
        unit="A",
        required=True,
        description="Total pack current",
        default=0.0,
    )

    soc: int = block_field(
        offset=4,
        type=UInt16(),
        unit="%",
        required=True,
        description="State of charge (battery %)",
        default=0,
    )

    pack_power: int = block_field(
        offset=6,
        type=UInt32(),
        unit="W",
        description="Pack power (calculated in device model)",
        default=0,
    )

    load_power: int = block_field(
        offset=10,
        type=UInt32(),
        unit="W",
        description="Load power (calculated in device model)",
        default=0,
    )

    pack_online: int = block_field(
        offset=16, type=UInt16(), description="Pack online status bitmap", default=0
    )

    # === Device Info (20-47) ===
    device_model: str = block_field(
        offset=20, type=String(length=12), description="Device model string", default=""
    )

    device_serial: str = block_field(
        offset=32, type=String(length=8), description="Device serial number", default=""
    )

    # === Temperatures (48-53) ===
    pack_temp_avg: int = block_field(
        offset=48,
        type=UInt16(),
        transform=[minus(40)],
        unit="°C",
        description="Average pack temperature",
        default=0,
    )

    pack_temp_max: int = block_field(
        offset=50,
        type=UInt16(),
        transform=[minus(40)],
        unit="°C",
        description="Maximum pack temperature",
        default=0,
    )

    pack_temp_min: int = block_field(
        offset=52,
        type=UInt16(),
        transform=[minus(40)],
        unit="°C",
        description="Minimum pack temperature",
        default=0,
    )

    # === Power Flows (80-95) ===
    # Requires protocol >= 2001
    dc_input_power: int = block_field(
        offset=80,
        type=UInt32(),
        unit="W",
        min_protocol_version=2001,
        description="Total DC input power",
        default=0,
    )

    ac_input_power: int = block_field(
        offset=84,
        type=UInt32(),
        unit="W",
        min_protocol_version=2001,
        description="Total AC input power",
        default=0,
    )

    pv_power: int = block_field(
        offset=88,
        type=UInt32(),
        unit="W",
        min_protocol_version=2001,
        description="Total PV (solar) power",
        default=0,
    )

    grid_power: int = block_field(
        offset=92,
        type=Int32(),  # SIGNED! Negative = export
        unit="W",
        min_protocol_version=2001,
        description="Grid power (negative = export to grid)",
        default=0,
    )

    # === Energy Totals (100-119) ===
    total_energy_charge: float = block_field(
        offset=100,
        type=UInt32(),
        transform=[scale(0.1)],
        unit="kWh",
        min_protocol_version=2001,
        description="Total DC energy charged",
        default=0.0,
    )

    ac_output_power: int = block_field(
        offset=104,
        type=UInt32(),
        unit="W",
        min_protocol_version=2001,
        description="Total AC output power",
        default=0,
    )

    pv_charge_energy: float = block_field(
        offset=108,
        type=UInt32(),
        transform=[scale(0.1)],
        unit="kWh",
        min_protocol_version=2001,
        description="Total PV charging energy",
        default=0.0,
    )

    total_energy_discharge: float = block_field(
        offset=112,
        type=UInt32(),
        transform=[scale(0.1)],
        unit="kWh",
        min_protocol_version=2001,
        description="Total discharge energy",
        default=0.0,
    )

    total_feedback_energy: float = block_field(
        offset=116,
        type=UInt32(),
        transform=[scale(0.1)],
        unit="kWh",
        min_protocol_version=2001,
        description="Total grid feedback (export) energy",
        default=0.0,
    )

    # === State of Health (120+) ===
    soh: int = block_field(
        offset=120,
        type=UInt16(),
        unit="%",
        description="State of health (battery degradation)",
        default=100,
    )

    # === PV Details (124-135) ===
    pv1_voltage: float = block_field(
        offset=124,
        type=UInt16(),
        transform=[scale(0.1)],
        unit="V",
        description="PV1 voltage",
        default=0.0,
    )

    pv1_current: float = block_field(
        offset=126,
        type=UInt16(),
        transform=[scale(0.1)],
        unit="A",
        description="PV1 current",
        default=0.0,
    )

    pv2_voltage: float = block_field(
        offset=128,
        type=UInt16(),
        transform=[scale(0.1)],
        unit="V",
        description="PV2 voltage",
        default=0.0,
    )

    pv2_current: float = block_field(
        offset=130,
        type=UInt16(),
        transform=[scale(0.1)],
        unit="A",
        description="PV2 current",
        default=0.0,
    )


# Generate canonical BlockSchema object
BLOCK_100_DECLARATIVE_SCHEMA = AppHomeDataBlock.to_schema()  # type: ignore[attr-defined]
