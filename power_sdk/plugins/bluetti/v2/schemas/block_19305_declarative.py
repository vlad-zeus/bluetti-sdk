"""Block 19305 (TIMER_TASK_LIST) - Timer Task List Details.

Source: ProtocolParserV2.smali lines 3397-3600 (commTimerTaskListParse)
        ProtocolParserV2.smali lines 31973+ (parseTimerItem)
Bean: List<AT1TimerSettings>
Purpose: Individual timer task configuration details

Smali-verified structure:
- Entire block contains timer tasks (40 bytes each)
- Minimum block size: 40 bytes (0x28) for 1 timer
- Each timer task = 40 bytes (offsets i*40 to i*40+39)

Timer task structure (40 bytes):
- Offset +0 to +1: Enable flag (UInt16, typically 0 or 1)
- Offset +2: Start hour (UInt8, 0-23)
- Offset +4: Start minute (UInt8, 0-59)
- Offset +6: End hour (UInt8, 0-23)
- Offset +8: End minute (UInt8, 0-59)
- Offset +10 to +11: Days of week (UInt16 bitfield, bits 0-6 for Sun-Sat)
- Offset +12: Timer mode (UInt8)
  Mode values: 0=Disabled, 1=Grid charge, 2=PV charge, 3=Discharge,
               4=Load priority, 5=Battery priority, 6=Custom
- Offset +14 to +15: Power level (UInt16, W)
- Offset +16: Priority level (UInt8)
- Offset +17 to +39: Reserved/additional settings

Note: This schema provides baseline first timer task structure.
Full multi-timer parsing requires dynamic array support based on block size.
See also: TIMER_BLOCKS.md for complete timer documentation.
"""

from dataclasses import dataclass

from ..protocol.datatypes import UInt8, UInt16
from .declarative import block_field, block_schema


@block_schema(
    block_id=19305,
    name="TIMER_TASK_LIST",
    description="Timer task details (smali-verified, first task baseline)",
    min_length=40,
    protocol_version=2000,
    strict=False,
    verification_status="smali_verified",
)
@dataclass
class TimerTaskListBlock:
    """Timer task list schema (smali-verified for single task)."""

    # Timer 0 structure (offsets 0-39)
    timer0_enable: int = block_field(
        offset=0,
        type=UInt16(),
        description="Timer 0: Enable flag (0=disabled, 1=enabled)",
        required=True,
        default=0,
    )

    timer0_start_hour: int = block_field(
        offset=2,
        type=UInt8(),
        description="Timer 0: Start hour (0-23)",
        required=True,
        default=0,
    )

    timer0_start_minute: int = block_field(
        offset=4,
        type=UInt8(),
        description="Timer 0: Start minute (0-59)",
        required=True,
        default=0,
    )

    timer0_end_hour: int = block_field(
        offset=6,
        type=UInt8(),
        description="Timer 0: End hour (0-23)",
        required=True,
        default=0,
    )

    timer0_end_minute: int = block_field(
        offset=8,
        type=UInt8(),
        description="Timer 0: End minute (0-59)",
        required=True,
        default=0,
    )

    timer0_days_of_week: int = block_field(
        offset=10,
        type=UInt16(),
        description=(
            "Timer 0: Days of week bitfield "
            "(bit0=Sun, bit1=Mon, ..., bit6=Sat)"
        ),
        required=True,
        default=0,
    )

    timer0_mode: int = block_field(
        offset=12,
        type=UInt8(),
        description=(
            "Timer 0: Mode (0=Disabled, 1=Grid charge, 2=PV charge, "
            "3=Discharge, 4=Load priority, 5=Battery priority, 6=Custom)"
        ),
        required=True,
        default=0,
    )

    timer0_power: int = block_field(
        offset=14,
        type=UInt16(),
        description="Timer 0: Power level (W)",
        unit="W",
        required=True,
        default=0,
    )

    timer0_priority: int = block_field(
        offset=16,
        type=UInt8(),
        description="Timer 0: Priority level",
        required=False,
        default=0,
    )

    # Note: Additional timers at offsets 40, 80, 120, ... (40 bytes each)
    # Full multi-timer parsing requires dynamic structure support.
    # Application layer should iterate based on block size // 40.


BLOCK_19305_SCHEMA = TimerTaskListBlock.to_schema()  # type: ignore[attr-defined]
