"""Block 17400 (ATS_EVENT_EXT) - AT1 Transfer Switch Extended Settings.

Source: ProtocolParserV2.smali switch case (0x43f8 -> sswitch_a)
Parser: AT1Parser.at1SettingsParse (lines 1933-3662)
Bean: AT1BaseSettings.smali
Related Bean: AT1BaseConfigItem.smali (18 fields x 7 items)
Block Type: parser-backed
Purpose: AT1 transfer switch configuration (NESTED STRUCTURE - complex)

Structure:
- Min length: 91 bytes (0x5b)
- Data format: Hex string list (not raw bytes) → parsed via hexStrToEnableList() helper
- Core structure: 7x AT1BaseConfigItem nested objects (each with 18 fields)
- Simple fields: 9x Integer fields at indices 174-181 (BEYOND min_length)

Parser Structure (lines 1933-3662):
1. Bytes 0-91 (hex string inputs):
   - Indices 0-1: Combined → hexStrToEnableList() → chgFromGridEnable
   - Indices 2-3: Combined → hexStrToEnableList() → feedToGridEnable
   - Indices 4-5, 8-9, 10-11: delayEnable1, delayEnable2, delayEnable3
   - Indices 12-13, 14-15, 16-17: timerEnable1, timerEnable2, timerEnable3
   - Indices 0x18-0x24 (24-36): First config item helper data

2. Nested AT1BaseConfigItem structures (7 items):
   - configGrid (AT1Porn.GRID)
   - configSL1, configSL2, configSL3, configSL4 (AT1Porn.SMART_LOAD_1-4)
   - configPCS1, configPCS2 (AT1Porn.PCS_1-2)

   Each AT1BaseConfigItem has 18 fields:
   - AT1Porn enum (device type)
   - Integer type indicator
   - List<Integer> forceEnable, timerEnable
   - Integer linkageEnable
   - List<AT1ProtectItem> protectList (complex sub-parser)
   - List<AT1SOCThresholdItem> socSetList (complex sub-parser)
   - 6x Integer power limits (powerOLPL1-L3, powerULPL1-L3)
   - String labels (nameL1, nameL2)
   - 2x Integer reserved fields

3. Simple integer fields (indices 174-181, BEYOND min_length=91):
   - blackStartEnable, blackStartMode
   - generatorAutoStartEnable, offGridPowerPriority
   - voltLevelSet, acSupplyPhaseNum
   - socGenAutoStop, socGenAutoStart, socBlackStart

CRITICAL FINDING: Previous schema claimed 11 simple fields at offsets 0-10.
ALL 11 FIELDS HAVE ZERO EVIDENCE. The parser uses completely different structure
with nested AT1BaseConfigItem arrays and hexStrToEnableList() transformations.

CAUTION: This block controls AT1 automatic transfer switch settings. Incorrect
configuration may:
- Result in improper grid/generator switching behavior
- Violate electrical code requirements for transfer switches
- Cause power interruption or equipment damage
- Lead to unsafe backfeed conditions if not properly configured

Only modify with proper understanding of transfer switch operation and local codes.

Baseline Implementation: EMPTY SCHEMA (nested structure deferred).

Nested structure implementation requires:
1. Python dataclass support for AT1BaseConfigItem
2. Enum mapping for AT1Porn values
3. Helper classes for AT1ProtectItem, AT1SOCThresholdItem
4. Verification of actual block size (appears > 181 bytes despite min_length=91)
"""

from dataclasses import dataclass

from .declarative import block_schema


@block_schema(
    block_id=17400,
    name="ATS_EVENT_EXT",
    description="AT1 transfer switch extended settings (NESTED - deferred)",
    min_length=91,
    protocol_version=2000,
    strict=False,
    verification_status="partial",
)
@dataclass
class ATSEventExtBlock:
    """AT1 settings - empty baseline (nested structure deferred).

    Parser: AT1Parser.at1SettingsParse (lines 1933-3662)
    Bean: AT1BaseSettings with 7x AT1BaseConfigItem nested objects

    Structure complexity:
    - 8x List<Integer> fields (enable/timer flags from hex string parsing)
    - 2x Integer fields (grid charge/feed enable states)
    - 7x AT1BaseConfigItem nested objects (18 fields each):
        * configGrid (GRID enum type)
        * configSL1, configSL2, configSL3, configSL4 (SMART_LOAD variants)
        * configPCS1, configPCS2 (PCS variants)
    - 9x Integer fields at indices 174-181 (blackStart, generator, SOC thresholds)

    Previous schema had 11 fields at offsets 0-10. ALL INCORRECT (0% verified).
    Parser uses completely different structure with nested arrays and helper methods.

    STATUS: Schema deferred - requires:
    1. Python dataclass support for nested AT1BaseConfigItem
    2. Enum mapping for AT1Porn values
    3. Helper classes for AT1ProtectItem, AT1SOCThresholdItem
    4. Verification of actual block size (appears > 181 bytes despite min_length=91)

    SAFETY: CRITICAL - Controls AT1 automatic transfer switch operation.
    Do NOT write to this block without full verification.
    """


# Export schema instance
BLOCK_17400_SCHEMA = ATSEventExtBlock.to_schema()  # type: ignore[attr-defined]
