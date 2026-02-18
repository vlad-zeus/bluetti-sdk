"""Block 26001 (TOU_TIME_INFO) - TOU time control records.

Smali evidence (FULLY VERIFIED):
- ConnectManager.smali maps block 0x6591 to TouTimeCtrlParser.parseTouTimeExt
- Parser returns List<DeviceTouTime> with 14 bytes per item
- First 10 bytes are bit-packed into 9 fields via parseTouTimeItem
- Last 4 bytes are targetReg (UInt16) and targetValue (UInt16)

Source references:
- TouTimeCtrlParser.parseTouTimeExt: TouTimeCtrlParser.smali:181-334
- TouTimeCtrlParser.parseTouTimeItem: TouTimeCtrlParser.smali:336-664
- DeviceTouTime constructor: DeviceTouTime.smali:92-126
- Switch route: ConnectManager.smali:8239 (0x6591 -> :sswitch_8)
- Event name: "TOU_TIME_INFO" (ConnectManager.smali:6144)

This schema models the FIRST item only. Full dynamic list support is deferred.
"""

from dataclasses import dataclass

from power_sdk.constants import V2_PROTOCOL_VERSION
from power_sdk.protocol.v2.datatypes import UInt16
from .declarative import block_field, block_schema


@block_schema(
    block_id=26001,
    name="TOU_TIME_INFO",
    description="TOU time control record (first item - bit-packed structure)",
    min_length=14,
    protocol_version=V2_PROTOCOL_VERSION,
    strict=False,
    verification_status="smali_verified",
)
@dataclass
class TOUTimeInfoBlock:
    """TOU time control schema (smali verified, first item only).

    Source: TouTimeCtrlParser.parseTouTimeExt (TouTimeCtrlParser.smali:181-334)
    Bean: DeviceTouTime with constructor <init>(IIJIIIIII)V
    Event: "TOU_TIME_INFO" (ConnectManager.smali:6144)

    Parser returns List<DeviceTouTime> where each item is 14 bytes with complex
    bit-packing. First 10 bytes are packed into 80 bits total, then extracted
    into 7 separate fields. Last 4 bytes are direct UInt16 values.

    SDK Limitation: The parser returns a dynamic list, but current schema
    framework only supports parsing the first item. Full list support is
    tracked in SDK enhancement backlog.

    Bit-packing structure (verified from smali):
    - Bytes 0-9 are packed as: word0 | word1<<16 | word2<<32 | word3<<48 | word4
    - Then getBits extracts fields at specific bit offsets
    - See TouTimeCtrlParser.parseTouTimeItem (lines 541-638) for details

    Field structure per item (14 bytes total):
    - secondsOfDay: 17 bits from packed data (bits 0x11-0x27)
    - weekMask: 7 bits from packed data (bits 0x18-0x1e)
    - dayOfMonthMask: 31 bits from packed data (bits 0x18-0x36) - stored as long
    - monthMask: 12 bits from packed data (bits 0x37-0x42)
    - regType: 2 bits from packed data (bits 0x43-0x44)
    - targetId: 8 bits from packed data (bits 0x45-0x4c)
    - timeType: 3 bits from packed data (bits 0x4d-0x4f)
    - targetReg: UInt16 at offset 10-11 (direct)
    - targetValue: UInt16 at offset 12-13 (direct)

    Note: Due to bit-packing complexity, this schema uses raw UInt16 words
    for the first 10 bytes. Bit extraction should be done post-parse if needed.
    """

    # Raw packed words (bytes 0-9) - bit extraction deferred
    word0: int = block_field(
        offset=0,
        type=UInt16(),
        description=(
            "Packed word 0 (bytes 0-1) - contains partial secondsOfDay bits. "
            "See parseTouTimeItem for bit extraction algorithm."
        ),
        required=False,
        default=0,
    )

    word1: int = block_field(
        offset=2,
        type=UInt16(),
        description=(
            "Packed word 1 (bytes 2-3) - contains partial weekMask bits. "
            "See parseTouTimeItem for bit extraction algorithm."
        ),
        required=False,
        default=0,
    )

    word2: int = block_field(
        offset=4,
        type=UInt16(),
        description=(
            "Packed word 2 (bytes 4-5) - contains partial dayOfMonthMask bits. "
            "See parseTouTimeItem for bit extraction algorithm."
        ),
        required=False,
        default=0,
    )

    word3: int = block_field(
        offset=6,
        type=UInt16(),
        description=(
            "Packed word 3 (bytes 6-7) - contains partial monthMask bits. "
            "See parseTouTimeItem for bit extraction algorithm."
        ),
        required=False,
        default=0,
    )

    word4: int = block_field(
        offset=8,
        type=UInt16(),
        description=(
            "Packed word 4 (bytes 8-9) - contains overflow bits for high fields. "
            "See parseTouTimeItem for bit extraction algorithm."
        ),
        required=False,
        default=0,
    )

    # Direct fields (bytes 10-13)
    target_reg: int = block_field(
        offset=10,
        type=UInt16(),
        description=(
            "Target register address - device register to control based on "
            "TOU schedule. Set via setTargetReg() after parseTouTimeItem."
        ),
        required=False,
        default=0,
    )

    target_value: int = block_field(
        offset=12,
        type=UInt16(),
        description=(
            "Target value - value to write to target register when TOU "
            "schedule activates. Set via setTargetValue() after parseTouTimeItem."
        ),
        required=False,
        default=0,
    )


# Export schema instance
BLOCK_26001_SCHEMA = TOUTimeInfoBlock.to_schema()  # type: ignore[attr-defined]
