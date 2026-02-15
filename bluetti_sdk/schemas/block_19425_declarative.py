"""Block 19425 (AT1_TIMER_EVENT_B) - AT1 Timer Event Slots 3-4.

Source: ProtocolParserV2.smali lines 31973-32105 (parseTimerItem) + AT1Parser.smali
Bean: AT1TimerSettings containing List<AT1TimerSettingsItem>
Purpose: AT1 device-specific timer slot configuration (slots 3-4)

Smali-verified structure (per 4-byte timer item):
- Offset 0-1: UInt16 bit-packed (bits 0-6: days of week, bits 7-10: mode flags)
- Offset 2: UInt8 (power or setting value)
- Offset 3: UInt8 (additional setting value)

Block structure:
- Timer Item 3 (Slot 3): Offsets 0-3
- Timer Item 4 (Slot 4): Offsets 4-7

Note: This block is AT1-specific. Other devices use Block 19300/19305
      for timer settings.
"""

from dataclasses import dataclass

from ..protocol.v2.datatypes import UInt8, UInt16
from .declarative import block_field, block_schema


@block_schema(
    block_id=19425,
    name="AT1_TIMER_EVENT_B",
    description="AT1 timer event slots 3-4 (smali-verified, first slot baseline)",
    min_length=8,
    protocol_version=2000,
    strict=False,
)
@dataclass
class AT1TimerEventBBlock:
    """AT1 timer event slots 3-4 schema (smali-verified for single slot).

    Bit-packed structure (offsets 0-1):
    - Bits 0-6: Days of week bitfield (7 bits)
    - Bit 7: Removed/padding
    - Bits 8-11: Mode flags (4 bits)
    - Bits 12-15: Additional flags

    Full structure supports 2 timer items; baseline implementation covers slot 3.
    """

    slot3_flags: int = block_field(
        offset=0,
        type=UInt16(),
        description="Slot 3 bit-packed flags (days + mode)",
        required=True,
        default=0,
    )
    slot3_value1: int = block_field(
        offset=2,
        type=UInt8(),
        description="Slot 3 setting value 1 (power or threshold)",
        required=True,
        default=0,
    )
    slot3_value2: int = block_field(
        offset=3,
        type=UInt8(),
        description="Slot 3 setting value 2 (additional parameter)",
        required=True,
        default=0,
    )
    slot4_flags: int = block_field(
        offset=4,
        type=UInt16(),
        description="Slot 4 bit-packed flags (days + mode)",
        required=False,
        default=0,
    )
    slot4_value1: int = block_field(
        offset=6,
        type=UInt8(),
        description="Slot 4 setting value 1",
        required=False,
        default=0,
    )
    slot4_value2: int = block_field(
        offset=7,
        type=UInt8(),
        description="Slot 4 setting value 2",
        required=False,
        default=0,
    )


# Export schema instance
BLOCK_19425_SCHEMA = AT1TimerEventBBlock.to_schema()  # type: ignore[attr-defined]
