"""Block 26001 (TOU_SETTINGS) - Time-of-Use Rate Schedule Settings.

Source: ProtocolParserV2.smali switch case (0x6591 -> sswitch_3)
Related: ProtocolAddrV2.smali defines TOU_CTRL at 0x6591
Block Type: EVENT (no dedicated parse method)
Purpose: Time-of-Use electricity rate schedule configuration

Structure (PROVISIONAL):
- Min length from smali: 126 bytes (0x7e)
- Related field: TOU_CTRL_ENABLE at 0x6590
- Likely contains: rate period definitions, time windows, pricing tiers
- Used for optimizing charge/discharge based on electricity rates

CAUTION: This block controls time-of-use scheduling for energy management.
Incorrect TOU configuration may:
- Result in charging during expensive peak rate periods
- Cause missed opportunities for low-rate charging
- Lead to higher electricity costs
- Interfere with grid demand response programs

Verify TOU time windows and rate tiers match your utility's actual schedule.
Incorrect settings can significantly impact energy costs.

TODO(smali-verify): Complete field mapping requires:
- Understanding of TOU rate structure (how many periods, time slots)
- Reverse engineering of TouSettings bean
- Analysis of TOU_CTRL_ENABLE flag interactions
"""

from dataclasses import dataclass

from ..protocol.v2.datatypes import UInt8, UInt16
from .declarative import block_field, block_schema


@block_schema(
    block_id=26001,
    name="TOU_SETTINGS",
    description="Time-of-Use rate schedule settings (provisional - EVENT block)",
    min_length=126,
    protocol_version=2000,
    strict=False,
    verification_status="inferred",
)
@dataclass
class TOUSettingsBlock:
    """Time-of-Use settings schema (provisional baseline).

    This block follows EVENT pattern without dedicated parse method.
    Field mapping is provisional pending actual device testing.

    CAUTION: TOU scheduling control - verify rate periods match utility schedule.
    """

    tou_enable: int = block_field(
        offset=0,
        type=UInt8(),
        description="TOU scheduling enable flag (TODO: verify offset)",
        required=False,
        default=0,
    )

    tou_mode: int = block_field(
        offset=1,
        type=UInt8(),
        description="TOU mode selector (TODO: verify offset and mode enum)",
        required=False,
        default=0,
    )

    # Rate period definitions (assuming 4-6 rate periods)
    # Each period likely has: start time, end time, rate tier, days of week

    period_1_start_hour: int = block_field(
        offset=2,
        type=UInt8(),
        description="Rate period 1 start hour (TODO: verify offset)",
        required=False,
        default=0,
    )

    period_1_start_minute: int = block_field(
        offset=3,
        type=UInt8(),
        description="Rate period 1 start minute (TODO: verify offset)",
        required=False,
        default=0,
    )

    period_1_end_hour: int = block_field(
        offset=4,
        type=UInt8(),
        description="Rate period 1 end hour (TODO: verify offset)",
        required=False,
        default=0,
    )

    period_1_end_minute: int = block_field(
        offset=5,
        type=UInt8(),
        description="Rate period 1 end minute (TODO: verify offset)",
        required=False,
        default=0,
    )

    period_1_rate_tier: int = block_field(
        offset=6,
        type=UInt8(),
        description="Rate period 1 tier (peak/mid/off-peak) (TODO: verify offset)",
        required=False,
        default=0,
    )

    period_1_days_of_week: int = block_field(
        offset=7,
        type=UInt8(),
        description="Period 1 active days (bit field: Sun-Sat) (TODO: verify offset)",
        required=False,
        default=0,
    )

    # Additional periods would follow similar pattern
    # Exact number of periods and structure needs device testing

    charge_priority_enable: int = block_field(
        offset=60,
        type=UInt8(),
        description=(
            "Prioritize charging in low-rate periods (TODO: verify offset)"
        ),
        required=False,
        default=0,
    )

    discharge_priority_enable: int = block_field(
        offset=61,
        type=UInt8(),
        description=(
            "Prioritize discharge in high-rate periods (TODO: verify offset)"
        ),
        required=False,
        default=0,
    )

    peak_rate_threshold: int = block_field(
        offset=62,
        type=UInt16(),
        description="Peak rate cost threshold (TODO: verify offset and unit)",
        required=False,
        default=0,
    )

    off_peak_rate_threshold: int = block_field(
        offset=64,
        type=UInt16(),
        description="Off-peak rate cost threshold (TODO: verify offset and unit)",
        required=False,
        default=0,
    )

    tou_schedule_version: int = block_field(
        offset=66,
        type=UInt16(),
        description="TOU schedule version/revision (TODO: verify offset)",
        required=False,
        default=0,
    )


# Export schema instance
BLOCK_26001_SCHEMA = TOUSettingsBlock.to_schema()  # type: ignore[attr-defined]
