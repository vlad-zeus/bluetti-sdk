"""Block 15500 (DC_DC_INFO) - DC-DC Converter Device Information.

Source: ProtocolParserV2.smali switch case (0x3c8c -> sswitch_13)
Block Type: EVENT (no dedicated parse method)
Purpose: DC-DC converter identification, voltage, current, and status

Structure (PROVISIONAL):
- Min length from smali: 70 bytes (const v12 = 0x46)
- Likely contains: model, SN, input/output voltage, current, power, temperature
- Related to DCDC_SETTINGS block 15600

Note: This is a provisional baseline implementation. Full field mapping requires:
- Actual DC-DC converter device for testing
- Event payload capture and analysis
- Bean structure verification (DCDCInfo class)

TODO(smali-verify): Complete field mapping when DC-DC device available
"""

from dataclasses import dataclass

from ..protocol.v2.datatypes import String, UInt16, UInt32
from .declarative import block_field, block_schema


@block_schema(
    block_id=15500,
    name="DC_DC_INFO",
    description="DC-DC converter device information (provisional - EVENT block)",
    min_length=70,
    protocol_version=2000,
    strict=False,
    verification_status="inferred",
)
@dataclass
class DCDCInfoBlock:
    """DC-DC converter information schema (provisional baseline).

    This block follows EVENT pattern without dedicated parse method.
    Field mapping is provisional pending actual device testing.
    """

    model: str = block_field(
        offset=0,
        type=String(length=12),
        description="DC-DC converter model name (ASCII)",
        required=False,
        default="",
    )
    serial_number: str = block_field(
        offset=12,
        type=String(length=8),
        description="DC-DC converter serial number",
        required=False,
        default="",
    )
    software_version: int = block_field(
        offset=20,
        type=UInt32(),
        description="Firmware version (TODO: verify offset)",
        required=False,
        default=0,
    )
    input_voltage: int = block_field(
        offset=24,
        type=UInt16(),
        unit="V",
        description="Input voltage (TODO: verify offset and scale)",
        required=False,
        default=0,
    )
    output_voltage: int = block_field(
        offset=26,
        type=UInt16(),
        unit="V",
        description="Output voltage (TODO: verify offset and scale)",
        required=False,
        default=0,
    )
    input_current: int = block_field(
        offset=28,
        type=UInt16(),
        unit="A",
        description="Input current (TODO: verify offset and scale)",
        required=False,
        default=0,
    )
    output_current: int = block_field(
        offset=30,
        type=UInt16(),
        unit="A",
        description="Output current (TODO: verify offset and scale)",
        required=False,
        default=0,
    )
    power: int = block_field(
        offset=32,
        type=UInt16(),
        unit="W",
        description="Converter power (TODO: verify offset and scale)",
        required=False,
        default=0,
    )
    temperature: int = block_field(
        offset=34,
        type=UInt16(),
        unit="°C",
        description="Converter temperature (TODO: verify offset and scale)",
        required=False,
        default=0,
    )
    status: int = block_field(
        offset=36,
        type=UInt16(),
        description="Status/error flags (TODO: verify bit mapping)",
        required=False,
        default=0,
    )


# Export schema instance
BLOCK_15500_SCHEMA = DCDCInfoBlock.to_schema()  # type: ignore[attr-defined]
