"""Block 26001 (TOU_SETTINGS) - TOU time control records.

Smali evidence:
- ConnectManager.smali maps block 0x6591 to TouTimeCtrlParser.parseTouTimeExt(...)
- TouTimeCtrlParser.parseTouTimeExt processes data in 14-byte records:
  - bytes 0..9: parseTouTimeItem payload
  - bytes 10..11: targetReg (UInt16)
  - bytes 12..13: targetValue (UInt16)

This schema models a low-level baseline for record 0 only.
Full dynamic list support is deferred.
"""

from dataclasses import dataclass

from ..protocol.v2.datatypes import UInt16
from .declarative import block_field, block_schema


@block_schema(
    block_id=26001,
    name="TOU_SETTINGS",
    description="TOU control records baseline (item0 raw words + target fields)",
    min_length=126,
    protocol_version=2000,
    strict=False,
    verification_status="partial",
)
@dataclass
class TOUSettingsBlock:
    """TOU settings schema (partial, parser-backed baseline).

    Each TOU record is 14 bytes. This schema captures record 0 in raw form:
    five UInt16 words from parseTouTimeItem input plus target register/value.
    Dynamic multi-record parsing is deferred.
    """

    item0_word0: int = block_field(
        offset=0,
        type=UInt16(),
        description="Record 0 word0 (raw bits for TOU item decoding)",
        required=False,
        default=0,
    )

    item0_word1: int = block_field(
        offset=2,
        type=UInt16(),
        description="Record 0 word1 (raw bits for TOU item decoding)",
        required=False,
        default=0,
    )

    item0_word2: int = block_field(
        offset=4,
        type=UInt16(),
        description="Record 0 word2 (raw bits for TOU item decoding)",
        required=False,
        default=0,
    )

    item0_word3: int = block_field(
        offset=6,
        type=UInt16(),
        description="Record 0 word3 (raw bits for TOU item decoding)",
        required=False,
        default=0,
    )

    item0_word4: int = block_field(
        offset=8,
        type=UInt16(),
        description="Record 0 word4 (raw bits for TOU item decoding)",
        required=False,
        default=0,
    )

    item0_target_reg: int = block_field(
        offset=10,
        type=UInt16(),
        description="Record 0 target register (setTargetReg)",
        required=False,
        default=0,
    )

    item0_target_value: int = block_field(
        offset=12,
        type=UInt16(),
        description="Record 0 target value (setTargetValue)",
        required=False,
        default=0,
    )


# Export schema instance
BLOCK_26001_SCHEMA = TOUSettingsBlock.to_schema()  # type: ignore[attr-defined]
