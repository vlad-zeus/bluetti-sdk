"""Block 15500 (DC_DC_INFO) - DC-DC Converter Device Information.

Source: ProtocolParserV2.smali switch case (0x3c8c -> sswitch_13)
Parser: DCDCParser.baseInfoParse (lines 66-1779)
Bean: DCDCInfo.smali (30+ fields)
Block Type: parser-backed
Purpose: DC-DC converter identification, voltage, current, power, and status monitoring

Structure:
- Min length from smali: 70 bytes (const v12 = 0x46)
- Core fields (offsets 0-29): Verified from smali
- Extended fields (30+): Multi-channel DC (dc1-dc6), fault maps, power totals
- Related to DCDC_SETTINGS block 15600

Smali Evidence:
- Model/SN: ASCII/DeviceSN transforms (lines 191-222)
- Voltage/Current: parseInt(16) ÷ 10.0f transform (lines 224-353)
- Power: parseInt(16) raw (no division) (lines 355-392)
- Bit-field status: hexStrToBinaryList/hexStrToEnableList (lines 395-524)

Scale Factors (verified from bytecode):
- Voltage fields: x0.1V (div-float by 10.0f constant)
- Current field: x0.1A (div-float by 10.0f constant)
- Power field: x1W (raw hex, no division)

TODO(smali-verify): Complete mapping requires:
- Multi-channel DC field offsets (dc1-dc6 voltage/current/power)
- AlarmFaultInfo bean structure analysis
- DCDCChannelItem bean structure analysis
- Actual device payload validation
"""

from dataclasses import dataclass

from ..protocol.v2.datatypes import String, UInt16
from .declarative import block_field, block_schema


@block_schema(
    block_id=15500,
    name="DC_DC_INFO",
    description="DC-DC converter device information (provisional - EVENT block)",
    min_length=70,
    protocol_version=2000,
    strict=False,
    verification_status="partial",
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
    dc_input_volt: int = block_field(
        offset=20,
        type=UInt16(),
        unit="V",
        description=(
            "DC input voltage [scale: x0.1V, transform: parseInt÷10f, "
            "bean: Float] (smali: lines 224-267)"
        ),
        required=False,
        default=0,
    )
    dc_output_volt: int = block_field(
        offset=22,
        type=UInt16(),
        unit="V",
        description=(
            "DC output voltage [scale: x0.1V, transform: parseInt÷10f, "
            "bean: Float] (smali: lines 269-310)"
        ),
        required=False,
        default=0,
    )
    dc_output_current: int = block_field(
        offset=24,
        type=UInt16(),
        unit="A",
        description=(
            "DC output current [scale: x0.1A, transform: parseInt÷10f, "
            "bean: Float] (smali: lines 312-353)"
        ),
        required=False,
        default=0,
    )
    dc_output_power: int = block_field(
        offset=26,
        type=UInt16(),
        unit="W",
        description=(
            "DC output power [scale: x1W (raw), transform: parseInt, "
            "bean: Integer] (smali: lines 355-392)"
        ),
        required=False,
        default=0,
    )
    energy_line_car_to_charger: int = block_field(
        offset=28,
        type=UInt16(),
        description=(
            "Energy line direction: car to charger [bit 0, "
            "transform: hexStrToBinaryList] (smali: lines 395-444)"
        ),
        required=False,
        default=0,
    )
    energy_line_charger_to_device: int = block_field(
        offset=28,
        type=UInt16(),
        description=(
            "Energy line direction: charger to device [bit 1, "
            "transform: hexStrToBinaryList] (smali: lines 446-457)"
        ),
        required=False,
        default=0,
    )
    # TODO: Add remaining status bit fields
    # (dcInputStatus1/2, dcOutputStatus1/2 from energyLines list)
    # TODO: Add multi-channel DC fields (dc1-dc6 voltage/current/power, offsets TBD)
    # TODO: Add fault/protection fields
    # (dcFaults, dcdcFault, dcdcProtection - AlarmFaultInfo beans)
    # TODO: Add power total fields (dcInputPowerTotal, dcOutputPowerTotal)


# Export schema instance
BLOCK_15500_SCHEMA = DCDCInfoBlock.to_schema()  # type: ignore[attr-defined]
