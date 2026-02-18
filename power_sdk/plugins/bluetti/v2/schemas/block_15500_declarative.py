"""Block 15500 (DC_DC_INFO) - DC-DC Converter Device Information.

Source: ProtocolParserV2.smali switch case (0x3c8c -> sswitch_13)
Parser: DCDCParser.baseInfoParse (lines 66-1779)
Bean: DCDCInfo.smali (30+ fields)
Block Type: parser-backed
Purpose: DC-DC converter identification, voltage, current, power, and status monitoring

Structure:
- Min length: 30 bytes (covers offsets 0-29, basic device info)
- Core fields (offsets 0-29): VERIFIED from smali (all 8 fields proven)
- Extended fields (30+): Multi-channel DC (dc1-dc6), fault maps, power totals
- Related to DCDC_SETTINGS block 15600

Smali Evidence (All Current Fields Verified):
- Model: offset 0-11, getASCIIStr (lines 191-207)
- Serial: offset 12-19, getDeviceSN (lines 209-222)
- DC Input Voltage: offset 20-21, parseInt(16)÷10f (lines 224-267)
- DC Output Voltage: offset 22-23, parseInt(16)÷10f (lines 269-310)
- DC Output Current: offset 24-25, parseInt(16)÷10f (lines 312-353)
- DC Output Power: offset 26-27, parseInt(16) raw (lines 355-392)
- Energy Line Car->Charger: offset 28-29 bit[0], hexStrToBinaryList (lines 395-444)
- Energy Line Charger->Device: offset 28-29 bit[1], hexStrToBinaryList (lines 446-457)

Scale Factors (verified from bytecode):
- Voltage fields: x0.1V (div-float by 10.0f constant)
- Current field: x0.1A (div-float by 10.0f constant)
- Power field: x1W (raw hex, no division)

Note: Additional fields exist in DCDCInfo bean but are not included in this baseline
schema (workingMode, batteryTypeInput, dc1-6 channels, fault maps, etc.). These require
larger packet sizes and conditional parsing based on list.size() checks.
"""

from dataclasses import dataclass

from ..protocol.datatypes import String, UInt16
from .declarative import block_field, block_schema


@block_schema(
    block_id=15500,
    name="DC_DC_INFO",
    description="DC-DC converter device information (baseline - EVENT block)",
    min_length=30,
    protocol_version=2000,
    strict=False,
    verification_status="smali_verified",
)
@dataclass
class DCDCInfoBlock:
    """DC-DC converter information schema (smali-verified baseline).

    All 8 fields verified from DCDCParser.baseInfoParse smali bytecode.
    This represents the minimum packet structure (30 bytes). Additional
    fields exist in the bean but require larger packets with conditional parsing.
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
            "Energy line direction: car to charger [extracted from bit 0 of "
            "UInt16 at offset 28-29, transform: hexStrToBinaryList] "
            "(smali: lines 395-444)"
        ),
        required=False,
        default=0,
    )
    energy_line_charger_to_device: int = block_field(
        offset=28,
        type=UInt16(),
        description=(
            "Energy line direction: charger to device [extracted from bit 1 of "
            "UInt16 at offset 28-29, transform: hexStrToBinaryList] "
            "(smali: lines 446-457)"
        ),
        required=False,
        default=0,
    )
    # NOTE: Additional fields exist in DCDCInfo bean but not included in baseline:
    # - batteryTypeInput (offset 30-31, requires size > 34)
    # - dcInputStatus1/2, dcOutputStatus1/2 (derived from energyLines list)
    # - dc1-dc6 channels (voltage/current/power, conditional on packet size)
    # - Fault/protection fields (dcFaults, dcdcFault, dcdcProtection)
    # - Power totals (dcInputPowerTotal, dcOutputPowerTotal)
    # - workingMode (derived field, requires offset 32-33, size check)
    # These require packet sizes > 30 bytes and separate verification.


# Export schema instance
BLOCK_15500_SCHEMA = DCDCInfoBlock.to_schema()  # type: ignore[attr-defined]
