"""Block 19300 (TIMER_SETTINGS) - Timer Settings and Task List.

Source: ProtocolParserV2.smali lines 3249-3395 (commTimerSettingsParse)
Bean: DeviceCommTimerSettings
Purpose: Scheduled charge/discharge timer configuration

CAUTION: This block controls automated charge/discharge scheduling. Incorrect
timer configuration may:
- Result in unexpected battery charge/discharge cycles
- Cause energy cost issues if TOU (time-of-use) rates are not properly configured
- Lead to battery over-discharge or over-charge if limits are incorrect
- Interfere with grid compliance if combined with improper inverter settings

Verify timer power levels, time windows, and mode settings before deployment.

Smali-verified structure:
- Offsets 0-7: Enable list (8 bytes, bit-packed)
  Each 2-byte hex string contains 4 timer enable flags (2 bits per timer)
  Total: 32 timers supported (bits 0-1: disabled/enabled for each timer)
- Offset 8: Reserved byte
- Offset 9: Timer count (1 byte, number of active timers)
- Offsets 10+: Timer task list (40 bytes per timer)
  If size >= 0x5A (90 bytes): parse 2 timers (offsets 10-89)
  If size < 0x5A: parse 1 timer (offsets 10-49)

Timer task structure (40 bytes each):
- Offsets 0-1: Enable flag (parsed separately)
- Offsets 2-3: Start hour (UInt8)
- Offsets 4-5: Start minute (UInt8)
- Offsets 6-7: End hour (UInt8)
- Offsets 8-9: End minute (UInt8)
- Offsets 10-11: Days of week (bit field, 7 bits for Sun-Sat)
- Offsets 12-13: Timer mode (UInt8)
- Offsets 14-15: Power level (UInt16, W)
- Offsets 16-39: Additional settings (priority, reserved)

See also: TIMER_BLOCKS.md for detailed timer task parsing.
"""

from dataclasses import dataclass

from ..protocol.v2.datatypes import UInt8, UInt16
from .declarative import block_field, block_schema


@block_schema(
    block_id=19300,
    name="TIMER_SETTINGS",
    description="Timer configuration with enable flags and task list (smali-verified)",
    min_length=50,
    protocol_version=2000,
    strict=False,
    verification_status="smali_verified",
)
@dataclass
class TimerSettingsBlock:
    """Timer settings schema (smali-verified)."""

    # Enable list (offsets 0-7, bit-packed, 32 timers)
    enable_flags_01: int = block_field(
        offset=0,
        type=UInt16(),
        description=(
            "Enable flags for timers 0-3 (bit-packed: 2 bits per timer)"
        ),
        required=True,
        default=0,
    )

    enable_flags_02: int = block_field(
        offset=2,
        type=UInt16(),
        description=(
            "Enable flags for timers 4-7 (bit-packed: 2 bits per timer)"
        ),
        required=True,
        default=0,
    )

    enable_flags_03: int = block_field(
        offset=4,
        type=UInt16(),
        description=(
            "Enable flags for timers 8-11 (bit-packed: 2 bits per timer)"
        ),
        required=True,
        default=0,
    )

    enable_flags_04: int = block_field(
        offset=6,
        type=UInt16(),
        description=(
            "Enable flags for timers 12-15 (bit-packed: 2 bits per timer)"
        ),
        required=True,
        default=0,
    )

    # Timer count (offset 9)
    timer_count: int = block_field(
        offset=9,
        type=UInt8(),
        description="Number of active timers (0-32)",
        required=True,
        default=0,
    )

    # Note: Timer task list at offsets 10+ requires dynamic parsing
    # based on timer_count. Each timer is 40 bytes.
    # Use commTimerTaskListParse (Block 19305) for full timer task access.
    # This schema provides enable flags and count only as baseline.


BLOCK_19300_SCHEMA = TimerSettingsBlock.to_schema()  # type: ignore[attr-defined]
