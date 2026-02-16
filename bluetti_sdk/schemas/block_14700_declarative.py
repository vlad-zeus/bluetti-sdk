"""Block 14700 (SMART_PLUG_SETTINGS) - Smart Plug Configuration Settings.

Source: ProtocolParserV2.smali switch case (0x396c -> sswitch_1a)
Related: ProtocolAddrV2.smali defines SMART_PLUG_SET_ENABLE_1 at 0x396d
Block Type: parser-backed (SmartPlugParser.settingsInfoParse)
Purpose: Smart plug power control and scheduling settings

Structure (PROVISIONAL):
- Min length from smali: 32 bytes (const v18)
- Likely contains: enable flags, power limits, scheduling parameters

Security: CRITICAL - Controls smart plug power output. Incorrect settings
may overload connected devices or create fire hazard. Only modify with
proper understanding of load requirements and safety margins.

TODO(smali-verify): Complete field mapping when smart plug device available.
Requires reverse engineering of SmartPlugSettings bean or actual device testing.
"""

from dataclasses import dataclass

from ..protocol.v2.datatypes import UInt8, UInt16, UInt32
from .declarative import block_field, block_schema


@block_schema(
    block_id=14700,
    name="SMART_PLUG_SETTINGS",
    description="Smart plug control settings (provisional - EVENT block)",
    min_length=32,
    protocol_version=2000,
    strict=False,
    verification_status="partial",
)
@dataclass
class SmartPlugSettingsBlock:
    """Smart plug settings schema (provisional baseline).

    This block follows EVENT pattern without dedicated parse method.
    Field mapping is provisional pending actual device testing.

    SECURITY WARNING: Power control settings - verify safe operating limits.
    """

    enable_flags: int = block_field(
        offset=0,
        type=UInt16(),
        description="Smart plug enable/control flags (TODO: verify bit mapping)",
        required=False,
        default=0,
    )
    max_power: int = block_field(
        offset=2,
        type=UInt16(),
        unit="W",
        description="Maximum power limit (TODO: verify offset and scale)",
        required=False,
        default=0,
    )
    schedule_enable: int = block_field(
        offset=4,
        type=UInt8(),
        description="Schedule control enable (TODO: verify)",
        required=False,
        default=0,
    )
    schedule_time: int = block_field(
        offset=6,
        type=UInt32(),
        description="Schedule timestamp (TODO: verify format)",
        required=False,
        default=0,
    )


# Export schema instance
BLOCK_14700_SCHEMA = SmartPlugSettingsBlock.to_schema()  # type: ignore[attr-defined]
