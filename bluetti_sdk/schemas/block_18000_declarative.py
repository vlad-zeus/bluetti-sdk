"""Block 18000 (EPAD_INFO) - Energy Pad Base Information.

Source: ProtocolParserV2.smali switch case (0x4650 -> sswitch_9)
Related: ProtocolAddrV2.smali defines EPAD_BASE_INFO at 0x4650
Block Type: parser-backed (EpadParser.baseInfoParse)
Purpose: Energy Pad (EPAD) device comprehensive status monitoring

Verification Status: SMALI_VERIFIED (Core Fields)
- Parser method: EpadParser.baseInfoParse (lines 972-1590)
- Bean constructor: EpadBaseInfo (14 fields)
- Evidence: AT1Parser.smali lines 1032-1581

Structure (VERIFIED):
- Min length from smali: 2019 bytes (0x7e3)
- Bytes 0-11: Reserved/unused (parser starts at offset 12)
- Bytes 12-37: Core monitoring fields (13 UInt16 values) - VERIFIED
- Bytes 38-2018: Alarm/fault history list - complex sub-structure

Core Monitoring Fields (13/14 VERIFIED from smali):
- 3x liquid level sensors (bytes 12-17)
- 3x temperature sensors (bytes 18-23)
- 3x remaining capacity values (bytes 24-29)
- 1x connection status (bytes 30-31)
- 3x ambient temperature readings (bytes 32-37)

Advanced Features (PARTIAL):
- epadAlarmList: Variable-length alarm records spanning bytes 38-2018
  Parsed via alarmListParse() sub-method (lines 1543-1581)
  Structure pending detailed analysis - NOT required for basic monitoring

All core monitoring fields verified with direct byte offsets, UInt16 types,
and unambiguous setter calls. Suitable for production EPAD integration.
"""

from dataclasses import dataclass

from ..protocol.v2.datatypes import UInt16
from .declarative import block_field, block_schema


@block_schema(
    block_id=18000,
    name="EPAD_INFO",
    description="Energy Pad base information (smali-verified core fields)",
    min_length=2019,
    protocol_version=2000,
    strict=False,
    verification_status="smali_verified",
)
@dataclass
class EPadInfoBlock:
    """Energy Pad information schema (smali-verified).

    Core monitoring fields verified from EpadParser.baseInfoParse smali disassembly.
    All 13 primary fields have confirmed byte offsets and UInt16 types.

    Evidence: EpadParser.smali lines 1032-1541
    Bean: EpadBaseInfo.smali constructor signature
    """

    # Liquid level sensors (bytes 12-17)
    liquid_level_1: int = block_field(
        offset=12,
        type=UInt16(),
        description="Liquid level sensor 1 reading (0-100%)",
        required=True,
        default=0,
    )

    liquid_level_2: int = block_field(
        offset=14,
        type=UInt16(),
        description="Liquid level sensor 2 reading (0-100%)",
        required=True,
        default=0,
    )

    liquid_level_3: int = block_field(
        offset=16,
        type=UInt16(),
        description="Liquid level sensor 3 reading (0-100%)",
        required=True,
        default=0,
    )

    # Temperature sensors (bytes 18-23)
    sensor_temp_1: int = block_field(
        offset=18,
        type=UInt16(),
        unit="0.1°C",
        description="Temperature sensor 1 reading",
        required=True,
        default=0,
    )

    sensor_temp_2: int = block_field(
        offset=20,
        type=UInt16(),
        unit="0.1°C",
        description="Temperature sensor 2 reading",
        required=True,
        default=0,
    )

    sensor_temp_3: int = block_field(
        offset=22,
        type=UInt16(),
        unit="0.1°C",
        description="Temperature sensor 3 reading",
        required=True,
        default=0,
    )

    # Remaining capacity (bytes 24-29)
    remaining_capacity_1: int = block_field(
        offset=24,
        type=UInt16(),
        unit="%",
        description="Remaining capacity sensor 1",
        required=True,
        default=0,
    )

    remaining_capacity_2: int = block_field(
        offset=26,
        type=UInt16(),
        unit="%",
        description="Remaining capacity sensor 2",
        required=True,
        default=0,
    )

    remaining_capacity_3: int = block_field(
        offset=28,
        type=UInt16(),
        unit="%",
        description="Remaining capacity sensor 3",
        required=True,
        default=0,
    )

    # Connection status (bytes 30-31)
    connection_status: int = block_field(
        offset=30,
        type=UInt16(),
        description="EPAD connection status flags",
        required=True,
        default=0,
    )

    # Ambient temperature (bytes 32-37)
    ambient_temp_1: int = block_field(
        offset=32,
        type=UInt16(),
        unit="0.1°C",
        description="Ambient temperature sensor 1",
        required=True,
        default=0,
    )

    ambient_temp_2: int = block_field(
        offset=34,
        type=UInt16(),
        unit="0.1°C",
        description="Ambient temperature sensor 2",
        required=True,
        default=0,
    )

    ambient_temp_3: int = block_field(
        offset=36,
        type=UInt16(),
        unit="0.1°C",
        description="Ambient temperature sensor 3",
        required=True,
        default=0,
    )

    # NOTE: Bytes 38-2018 contain alarm/fault history list
    # Parsed via EpadParser.alarmListParse() - complex sub-structure
    # Not required for basic EPAD monitoring functionality


# Export schema instance
BLOCK_18000_SCHEMA = EPadInfoBlock.to_schema()  # type: ignore[attr-defined]
