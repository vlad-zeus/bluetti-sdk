"""Block 14700 (SMART_PLUG_SETTINGS) - Smart Plug Configuration Settings.

Source: ProtocolParserV2.reference switch case (0x396c -> sswitch_1a)
Parser: SmartPlugParser.settingsInfoParse (lines 639-1241)
Bean: SmartPlugSettingsBean.reference (11 parameters, lines 187-267)
Block Type: parser-backed (fully analyzed from reference)
Purpose: Smart plug power control and scheduling settings

Structure (VERIFIED from reference):
- Min length: 56 bytes (offsets 0-55)
- Core settings (0-23): Protection, power limits, timing controls
- Timer list (24-55): 8 x 4-byte scheduled timer items

Timer Item Structure (SmartPlugTimerItem bean, 4 bytes each):
- Bytes 0-1: Week enable bits (7 days) + action bit (on/off)
- Byte 2: Hour (0-23, hex string)
- Byte 3: Minute (0-59, hex string)
- Status field: Sourced from timeSetCtrl parent field (8 enable flags)

reference Evidence:
- Parser method: SmartPlugParser.settingsInfoParse (lines 639-1241)
- Loop structure: 8 iterations, stride=4, base offset=0x18 (24)
- Bean constructor: SmartPlugSettingsBean (11 params, line 187)
- Nested bean: SmartPlugTimerItem (6 fields, line 151)
- Transform functions: hexStrToEnableList, parseInt, bit32RegByteToNumber

Security: CRITICAL - Controls smart plug power output. Incorrect settings
may overload connected devices or create fire hazard. Only modify with
proper understanding of load requirements and safety margins.

Verification Status: verified_reference (complete field structure analyzed)
Last Updated: 2026-02-16 (Agent D reference deep dive)
"""

from dataclasses import dataclass

from ..protocol.datatypes import UInt8, UInt16, UInt32
from .declarative import block_field, block_schema


@block_schema(
    block_id=14700,
    name="SMART_PLUG_SETTINGS",
    description="Smart plug control settings (reference-verified EVENT block)",
    min_length=56,  # Updated from 32 to 56 based on reference evidence
    strict=False,
    verification_status="verified_reference",  # Upgraded from partial
)
@dataclass
class SmartPlugSettingsBlock:
    """Smart plug settings schema (reference-verified structure).

    All fields verified from SmartPlugParser.settingsInfoParse method.
    Field offsets, types, and transforms confirmed from Android bytecode.

    SECURITY WARNING: Power control settings - verify safe operating limits.
    overloadProtectionPower and underloadProtectionPower control circuit
    breaker behavior. Incorrect values may fail to protect against overcurrent.
    """

    # === Protection and Enable Control (0-11) ===
    protection_ctrl: int = block_field(
        offset=0,
        type=UInt16(),
        description=(
            "Protection feature enable flags (16 bits) "
            "[transform: hexStrToEnableList] (reference: lines 692-736)"
        ),
        required=False,
        default=0,
    )
    set_enable_1: int = block_field(
        offset=2,
        type=UInt16(),
        description=(
            "Output control enable set 1 (16 bits) "
            "[transform: hexStrToEnableList] (reference: lines 739-777)"
        ),
        required=False,
        default=0,
    )
    set_enable_2: int = block_field(
        offset=4,
        type=UInt16(),
        description=(
            "Output control enable set 2 (16 bits) "
            "[transform: hexStrToEnableList] (reference: lines 780-820)"
        ),
        required=False,
        default=0,
    )
    # Note: Offset 6-7 appears to be padding/reserved (not referenced in parser)

    time_set_ctrl: int = block_field(
        offset=8,
        type=UInt32(),  # Spans 8-11 (4 bytes), populated via 2 separate calls
        description=(
            "Timer enable control flags (8 timers, from offsets 8-9 and 10-11) "
            "[transform: hexStrToEnableList x 2] (reference: lines 823-906)"
        ),
        required=False,
        default=0,
    )

    # === Power Protection Limits (12-17) ===
    overload_protection_power: int = block_field(
        offset=12,
        type=UInt16(),
        unit="W",
        description=(
            "Maximum power limit for overload protection (SAFETY CRITICAL) "
            "[transform: parseInt radix=16] (reference: lines 908-947) "
            "Typical range: 0-1800W for 15A plugs"
        ),
        required=False,
        default=0,
    )
    underload_protection_power: int = block_field(
        offset=14,
        type=UInt16(),
        unit="W",
        description=(
            "Minimum power threshold for underload detection (SAFETY CRITICAL) "
            "[transform: parseInt radix=16] (reference: lines 949-986) "
            "Used to detect device disconnection"
        ),
        required=False,
        default=0,
    )
    indicator_light: int = block_field(
        offset=16,
        type=UInt16(),
        description=(
            "LED indicator control setting "
            "[transform: parseInt radix=16] (reference: lines 989-1023)"
        ),
        required=False,
        default=0,
    )

    # === Timer Settings (18-23) ===
    timer_set: int = block_field(
        offset=18,
        type=UInt32(),
        unit="s",
        description=(
            "Master timer setting in seconds (countdown/duration) "
            "[transform: bit32RegByteToNumber] (reference: lines 1026-1054)"
        ),
        required=False,
        default=0,
    )
    delay_hour_set: int = block_field(
        offset=22,
        type=UInt8(),
        unit="h",
        description=(
            "Delay timer hours component (0-23) "
            "[transform: parseInt radix=16] (reference: lines 1057-1071)"
        ),
        required=False,
        default=0,
    )
    delay_min_set: int = block_field(
        offset=23,
        type=UInt8(),
        unit="min",
        description=(
            "Delay timer minutes component (0-59) "
            "[transform: parseInt radix=16] (reference: lines 1073-1090)"
        ),
        required=False,
        default=0,
    )

    # === Scheduled Timer List (24-55) ===
    # NOTE: timerList is a complex structure (List<SmartPlugTimerItem>) that requires
    # custom parsing logic. Each of the 8 timer items contains:
    #   - week: List<Int> (7 bits for days Sun-Sat)
    #   - action: Int (bit 7 from week field, 0=off 1=on)
    #   - hour: UInt8 (0-23)
    #   - min: UInt8 (0-59)
    #   - remark: String (nullable, not in payload)
    #   - status: Int (from timeSetCtrl field above)
    #
    # Timer item offsets: 24, 28, 32, 36, 40, 44, 48, 52
    # Each item: 4 bytes (bytes 0-1=week+action, byte 2=hour, byte 3=min)
    #
    # For advanced parsing, use SmartPlugTimerItem structure:
    # - Parser: SmartPlugParser.settingsInfoParse (lines 1093-1241)
    # - Bean: SmartPlugTimerItem.reference (constructor line 151, 6 parameters)
    # - Loop: 8 iterations, stride=4, base offset=0x18 (24 decimal)
    #
    # To parse timer items, extract 4-byte chunks and decode:
    #   week_action = bytes[0:2] as UInt16 binary (hexStrToBinaryList)
    #   week_days = week_action[0:7]  # bits 0-6
    #   action = week_action[7]  # bit 7
    #   hour = bytes[2] as UInt8 hex
    #   minute = bytes[3] as UInt8 hex
    #   status = time_set_ctrl bit for this timer index
    #
    # Example: Timer 0 at offset 24-27, Timer 1 at 28-31, ..., Timer 7 at 52-55

    timer_list_raw: int = block_field(
        offset=24,
        type=UInt32(),  # Placeholder - first 4 bytes of 32-byte timer array
        description=(
            "Scheduled timer list (8 items x 4 bytes = 32 bytes, offsets 24-55). "
            "See docstring for SmartPlugTimerItem structure and parsing details. "
            "[reference: lines 1093-1241, SmartPlugTimerItem bean line 151]"
        ),
        required=False,
        default=0,
    )


# Export schema instance
BLOCK_14700_SCHEMA = SmartPlugSettingsBlock.to_schema()  # type: ignore[attr-defined]
