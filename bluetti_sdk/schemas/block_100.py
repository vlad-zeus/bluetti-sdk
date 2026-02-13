"""Block 100 - APP_HOME_DATA Schema

Main dashboard data for Elite V2 devices.
Primary data source for monitoring power flows, SOC, and energy totals.
"""

from ..protocol.v2.schema import BlockSchema, Field
from ..protocol.v2.datatypes import UInt16, UInt32, Int32, UInt8, String


BLOCK_100_SCHEMA = BlockSchema(
    block_id=100,
    name="APP_HOME_DATA",
    description="Main dashboard data (SOC, power flows, energy totals)",
    min_length=120,  # Core fields, extended fields optional
    protocol_version=2000,
    schema_version="1.0.0",
    strict=False,  # Allow partial data for older firmware
    fields=[
        # === Battery Status (0-19) ===
        Field(
            name="pack_voltage",
            offset=0,
            type=UInt16(),
            transform=["scale:0.1"],
            unit="V",
            required=True,
            description="Total pack voltage"
        ),
        Field(
            name="pack_current",
            offset=2,
            type=UInt16(),
            transform=["scale:0.1"],
            unit="A",
            required=True,
            description="Total pack current"
        ),
        Field(
            name="soc",
            offset=4,
            type=UInt16(),
            unit="%",
            required=True,
            description="State of charge (battery %)"
        ),
        Field(
            name="pack_online",
            offset=16,
            type=UInt16(),
            description="Pack online status bitmap"
        ),

        # === Device Info (20-47) ===
        Field(
            name="device_model",
            offset=20,
            type=String(length=12),
            description="Device model string"
        ),
        Field(
            name="device_serial",
            offset=32,
            type=String(length=8),
            description="Device serial number"
        ),

        # === Temperatures (48-53) ===
        Field(
            name="pack_temp_avg",
            offset=48,
            type=UInt16(),
            transform=["minus:40"],
            unit="°C",
            description="Average pack temperature"
        ),
        Field(
            name="pack_temp_max",
            offset=50,
            type=UInt16(),
            transform=["minus:40"],
            unit="°C",
            description="Maximum pack temperature"
        ),
        Field(
            name="pack_temp_min",
            offset=52,
            type=UInt16(),
            transform=["minus:40"],
            unit="°C",
            description="Minimum pack temperature"
        ),

        # === Power Flows (80-95) ===
        # Requires protocol >= 2001
        Field(
            name="dc_input_power",
            offset=80,
            type=UInt32(),
            unit="W",
            min_protocol_version=2001,
            description="Total DC input power"
        ),
        Field(
            name="ac_input_power",
            offset=84,
            type=UInt32(),
            unit="W",
            min_protocol_version=2001,
            description="Total AC input power"
        ),
        Field(
            name="pv_power",
            offset=88,
            type=UInt32(),
            unit="W",
            min_protocol_version=2001,
            description="Total PV (solar) power"
        ),
        Field(
            name="grid_power",
            offset=92,
            type=Int32(),  # SIGNED! Negative = export
            unit="W",
            min_protocol_version=2001,
            description="Grid power (negative = export to grid)"
        ),

        # === Energy Totals (100-119) ===
        Field(
            name="total_energy_charge",
            offset=100,
            type=UInt32(),
            transform=["scale:0.1"],
            unit="kWh",
            min_protocol_version=2001,
            description="Total DC energy charged"
        ),
        Field(
            name="ac_output_power",
            offset=104,
            type=UInt32(),
            unit="W",
            min_protocol_version=2001,
            description="Total AC output power"
        ),
        Field(
            name="pv_charge_energy",
            offset=108,
            type=UInt32(),
            transform=["scale:0.1"],
            unit="kWh",
            min_protocol_version=2001,
            description="Total PV charging energy"
        ),
        Field(
            name="total_energy_discharge",
            offset=112,
            type=UInt32(),
            transform=["scale:0.1"],
            unit="kWh",
            min_protocol_version=2001,
            description="Total discharge energy"
        ),
        Field(
            name="total_feedback_energy",
            offset=116,
            type=UInt32(),
            transform=["scale:0.1"],
            unit="kWh",
            min_protocol_version=2001,
            description="Total grid feedback (export) energy"
        ),

        # === State of Health (120+) ===
        Field(
            name="soh",
            offset=120,
            type=UInt16(),
            unit="%",
            description="State of health (battery degradation)"
        ),

        # === PV Details (124-135) ===
        Field(
            name="pv1_voltage",
            offset=124,
            type=UInt16(),
            transform=["scale:0.1"],
            unit="V",
            description="PV1 voltage"
        ),
        Field(
            name="pv1_current",
            offset=126,
            type=UInt16(),
            transform=["scale:0.1"],
            unit="A",
            description="PV1 current"
        ),
        Field(
            name="pv2_voltage",
            offset=128,
            type=UInt16(),
            transform=["scale:0.1"],
            unit="V",
            description="PV2 voltage"
        ),
        Field(
            name="pv2_current",
            offset=130,
            type=UInt16(),
            transform=["scale:0.1"],
            unit="A",
            description="PV2 current"
        ),

        # === Power (calculated, derived from voltage * current) ===
        Field(
            name="pack_power",
            offset=6,
            type=UInt32(),
            unit="W",
            description="Pack power (calculated in device model)"
        ),
        Field(
            name="load_power",
            offset=10,
            type=UInt32(),
            unit="W",
            description="Load power (calculated in device model)"
        ),
    ]
)
