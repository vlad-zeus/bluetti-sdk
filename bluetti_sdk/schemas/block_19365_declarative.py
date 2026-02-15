"""Block 19365 (AT1_TIMER_EVENT_A) - AT1 Timer Event Slots 1-2.

Source: ProtocolParserV2.smali lines 31973-32105 (parseTimerItem) + AT1Parser.smali
Bean: AT1TimerSettings containing List<AT1TimerSettingsItem>
Purpose: AT1 device-specific timer slot configuration (slots 1-2)

Smali-verified structure (per 4-byte timer item):
- Offset 0-1: UInt16 bit-packed (bits 0-6: days of week, bits 7-10: mode flags)
- Offset 2: UInt8 (power or setting value)
- Offset 3: UInt8 (additional setting value)

Block structure:
- Timer Item 1 (Slot 1): Offsets 0-3
- Timer Item 2 (Slot 2): Offsets 4-7

Note: This block is AT1-specific. Other devices use Block 19300/19305
      for timer settings.
"""

from dataclasses import dataclass

from ..protocol.v2.datatypes import UInt8, UInt16
from .declarative import block_field, block_schema


@block_schema(
    block_id=19365,
    name="AT1_TIMER_EVENT_A",
    description="AT1 timer event slots 1-2 (smali-verified, first slot baseline)",
    min_length=8,
    protocol_version=2000,
    strict=False,
    verification_status="inferred",
)
@dataclass
class AT1TimerEventABlock:
    """AT1 timer event slots 1-2 schema (smali-verified for single slot).

    Bit-packed structure (offsets 0-1):
    - Bits 0-6: Days of week bitfield (7 bits)
    - Bit 7: Removed/padding
    - Bits 8-11: Mode flags (4 bits)
    - Bits 12-15: Additional flags

    Full structure supports 2 timer items; baseline implementation covers slot 1.
    """

    slot1_flags: int = block_field(
        offset=0,
        type=UInt16(),
        description="Slot 1 bit-packed flags (days + mode)",
        required=True,
        default=0,
    )
    slot1_value1: int = block_field(
        offset=2,
        type=UInt8(),
        description="Slot 1 setting value 1 (power or threshold)",
        required=True,
        default=0,
    )
    slot1_value2: int = block_field(
        offset=3,
        type=UInt8(),
        description="Slot 1 setting value 2 (additional parameter)",
        required=True,
        default=0,
    )
    slot2_flags: int = block_field(
        offset=4,
        type=UInt16(),
        description="Slot 2 bit-packed flags (days + mode)",
        required=False,
        default=0,
    )
    slot2_value1: int = block_field(
        offset=6,
        type=UInt8(),
        description="Slot 2 setting value 1",
        required=False,
        default=0,
    )
    slot2_value2: int = block_field(
        offset=7,
        type=UInt8(),
        description="Slot 2 setting value 2",
        required=False,
        default=0,
    )


# Export schema instance
BLOCK_19365_SCHEMA = AT1TimerEventABlock.to_schema()  # type: ignore[attr-defined]
