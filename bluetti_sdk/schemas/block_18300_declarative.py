"""Block 18300 (EPAD_SETTINGS) - Energy Pad Base Settings.

Source: ProtocolParserV2.smali switch case (0x477c -> sswitch_8)
Related: ProtocolAddrV2.smali defines EPAD_BASE_SETTINGS at 0x477c
Block Type: parser-backed (EpadParser.baseSettingsParse)
Purpose: Energy Pad configuration and control settings

Structure (PROVISIONAL):
- Min length from smali: 76 bytes (0x4c) or 75 bytes (0x4b) - protocol dependent
- Conditional check: if (v1 >= v6) then 0x4c else 0x4b
- Likely contains: operating mode, power limits, channel enable flags,
  protection settings

CAUTION: This block controls Energy Pad operation settings. Incorrect
configuration may:
- Result in improper power distribution or channel control
- Exceed safe operating limits for connected devices
- Cause equipment damage or safety hazards
- Lead to inefficient energy management

Only modify with proper understanding of EPAD specifications and load requirements.

TODO(smali-verify): Complete field mapping when EPAD device available.
Requires reverse engineering of EPADSettings bean or actual device testing.
"""

from dataclasses import dataclass

from ..protocol.v2.datatypes import UInt8, UInt16
from .declarative import block_field, block_schema


@block_schema(
    block_id=18300,
    name="EPAD_SETTINGS",
    description="Energy Pad configuration settings (provisional - EVENT block)",
    min_length=75,
    protocol_version=2000,
    strict=False,
    verification_status="partial",
)
@dataclass
class EPadSettingsBlock:
    """Energy Pad settings schema (provisional baseline).

    This block follows EVENT pattern without dedicated parse method.
    Field mapping is provisional pending actual EPAD device testing.

    CAUTION: Energy management control - verify safe operating limits.
    """

    operating_mode: int = block_field(
        offset=0,
        type=UInt8(),
        description="EPAD operating mode selector (TODO: verify offset and mode enum)",
        required=False,
        default=0,
    )

    enable_flags: int = block_field(
        offset=1,
        type=UInt16(),
        description="Channel/port enable flags (TODO: verify offset and bit mapping)",
        required=False,
        default=0,
    )

    max_power_limit: int = block_field(
        offset=3,
        type=UInt16(),
        unit="W",
        description="Maximum total power limit (TODO: verify offset)",
        required=False,
        default=0,
    )

    max_current_limit: int = block_field(
        offset=5,
        type=UInt16(),
        unit="0.1A",
        description="Maximum current limit (TODO: verify offset)",
        required=False,
        default=0,
    )

    voltage_set_point: int = block_field(
        offset=7,
        type=UInt16(),
        unit="0.1V",
        description="Output voltage set point (TODO: verify offset)",
        required=False,
        default=0,
    )

    protection_enable: int = block_field(
        offset=9,
        type=UInt8(),
        description="Protection features enable (TODO: verify offset)",
        required=False,
        default=0,
    )

    overvoltage_threshold: int = block_field(
        offset=10,
        type=UInt16(),
        unit="0.1V",
        description="Overvoltage protection threshold (TODO: verify offset)",
        required=False,
        default=0,
    )

    undervoltage_threshold: int = block_field(
        offset=12,
        type=UInt16(),
        unit="0.1V",
        description="Undervoltage protection threshold (TODO: verify offset)",
        required=False,
        default=0,
    )

    overcurrent_threshold: int = block_field(
        offset=14,
        type=UInt16(),
        unit="0.1A",
        description="Overcurrent protection threshold (TODO: verify offset)",
        required=False,
        default=0,
    )

    temperature_limit: int = block_field(
        offset=16,
        type=UInt16(),
        unit="0.1°C",
        description="Overtemperature protection limit (TODO: verify offset)",
        required=False,
        default=0,
    )

    auto_restart_enable: int = block_field(
        offset=18,
        type=UInt8(),
        description="Auto restart after fault clear (TODO: verify offset)",
        required=False,
        default=0,
    )

    priority_mode: int = block_field(
        offset=19,
        type=UInt8(),
        description="Channel priority mode (TODO: verify offset)",
        required=False,
        default=0,
    )


# Export schema instance
BLOCK_18300_SCHEMA = EPadSettingsBlock.to_schema()  # type: ignore[attr-defined]
