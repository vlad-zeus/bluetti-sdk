"""Block 6000 - PACK_MAIN_INFO Schema

Battery pack main information and status.
Detailed battery health, temperature, and protection status.
"""

from ..protocol.v2.datatypes import UInt8, UInt16
from ..protocol.v2.schema import BlockSchema, Field

BLOCK_6000_SCHEMA = BlockSchema(
    block_id=6000,
    name="PACK_MAIN_INFO",
    description="Battery pack detailed status and health",
    min_length=64,
    protocol_version=2000,
    schema_version="1.0.0",
    strict=False,  # Allow partial data
    fields=[
        # === Pack Configuration ===
        Field(
            name="pack_volt_type",
            offset=0,
            type=UInt16(),
            description="Pack voltage type",
        ),
        Field(
            name="pack_count",
            offset=3,
            type=UInt8(),
            description="Number of battery packs",
        ),
        Field(
            name="pack_online",
            offset=4,
            type=UInt16(),
            description="Pack online status bitmap",
        ),
        # === Battery Status ===
        Field(
            name="voltage",
            offset=6,
            type=UInt16(),
            transform=["scale:0.1"],
            unit="V",
            required=True,
            description="Total pack voltage",
        ),
        Field(
            name="current",
            offset=8,
            type=UInt16(),
            transform=["scale:0.1"],
            unit="A",
            required=True,
            description="Total pack current",
        ),
        Field(
            name="soc",
            offset=11,
            type=UInt8(),
            unit="%",
            required=True,
            description="State of charge",
        ),
        Field(
            name="soh",
            offset=13,
            type=UInt8(),
            unit="%",
            required=True,
            description="State of health",
        ),
        # === Temperature ===
        Field(
            name="temp_avg",
            offset=14,
            type=UInt16(),
            transform=["minus:40"],
            unit="°C",
            description="Average temperature",
        ),
        # Note: temp_max and temp_min may be at different offsets
        # Need to verify from actual data
        # === Operating Status ===
        Field(
            name="running_status",
            offset=17,
            type=UInt8(),
            description="Running status code",
        ),
        Field(
            name="charging_status",
            offset=19,
            type=UInt8(),
            description="Charging status code",
        ),
        # === Charge/Discharge Limits ===
        Field(
            name="max_charge_voltage",
            offset=20,
            type=UInt16(),
            transform=["scale:0.1"],
            unit="V",
            description="Maximum charge voltage",
        ),
        Field(
            name="max_charge_current",
            offset=22,
            type=UInt16(),
            transform=["scale:0.1"],
            unit="A",
            description="Maximum charge current",
        ),
        Field(
            name="max_discharge_current",
            offset=24,
            type=UInt16(),
            transform=["scale:0.1"],
            unit="A",
            description="Maximum discharge current",
        ),
        # === MOS Status ===
        Field(
            name="pack_mos",
            offset=32,
            type=UInt16(),
            description="Pack MOS status bitmap",
        ),
        # === Time Estimates ===
        Field(
            name="time_to_full",
            offset=34,
            type=UInt16(),
            unit="min",
            description="Estimated time to full charge",
        ),
        Field(
            name="time_to_empty",
            offset=36,
            type=UInt16(),
            unit="min",
            description="Estimated time to empty",
        ),
        # === Protection & Faults ===
        # Note: Protection status at offset 58-61 is complex (4-byte bitmap)
        # Pack fault bits at offset 62-63 (if size >= 64)
        Field(
            name="pack_fault_bits",
            offset=62,
            type=UInt16(),
            description="Pack fault status bitmap",
        ),
        # === Computed Fields ===
        Field(
            name="power",
            offset=10,  # Placeholder, computed as voltage * current
            type=UInt16(),
            unit="W",
            description="Pack power (computed)",
        ),
        Field(
            name="cell_count",
            offset=38,
            type=UInt16(),
            description="Number of cells in pack",
        ),
        Field(
            name="cycles",
            offset=40,
            type=UInt16(),
            description="Charge/discharge cycle count",
        ),
        # === Status Flags (derived from bitmaps) ===
        Field(
            name="charging",
            offset=19,  # Derived from charging_status
            type=UInt8(),
            description="Is charging (boolean flag)",
        ),
        Field(
            name="discharging",
            offset=17,  # Derived from running_status
            type=UInt8(),
            description="Is discharging (boolean flag)",
        ),
        # === Temperature Min/Max ===
        Field(
            name="temp_max",
            offset=50,
            type=UInt16(),
            transform=["minus:40"],
            unit="°C",
            description="Maximum cell temperature",
        ),
        Field(
            name="temp_min",
            offset=52,
            type=UInt16(),
            transform=["minus:40"],
            unit="°C",
            description="Minimum cell temperature",
        ),
    ],
)
