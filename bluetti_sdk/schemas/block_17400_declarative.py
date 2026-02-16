"""Block 17400 (AT1_SETTINGS) - AT1 Transfer Switch Extended Settings.

Source: ProtocolParserV2.smali switch case (0x43f8 -> sswitch_a)
Parser: AT1Parser.at1SettingsParse (lines 1933-3662)
Bean: AT1BaseSettings (20 components: 13 top-level + 7 nested AT1BaseConfigItem objects)
Block Type: parser-backed
Evidence: docs/re/17400-EVIDENCE.md (complete 147-field nested structure analysis)
Purpose: AT1 automatic transfer switch configuration (COMPLEX NESTED STRUCTURE)

Structure:
- Min length: 91 bytes (0x5b)
- Data format: List<String> (hex strings, not raw bytes)
- Total fields mapped: 147 (21 top-level + 7x18 nested = 126 nested parameters)
- Verification: 90 fields PROVEN (61%), 40 fields PARTIAL (27%),
  17 fields NOT_VERIFIED (12%)

Nested Object Hierarchy:
- AT1BaseSettings (top-level bean)
  - 13 top-level fields (chgFromGridEnable, feedToGridEnable, delayEnable1-3, etc.)
  - 7x AT1BaseConfigItem nested objects:
    * configGrid (AT1Porn.GRID)
    * configSL1-4 (AT1Porn.SMART_LOAD_1-4)
    * configPCS1-2 (AT1Porn.PCS_1-2)
  - Each AT1BaseConfigItem has:
    * 18 parameters (porn enum, type, forceEnable, timerEnable, linkageEnable, etc.)
    * List<AT1ProtectItem> protectList (up to 10 items, 14 fields each)
    * List<AT1SOCThresholdItem> socSetList (6 items, 8 fields each)

Verification Status:
- Overall: partial (2 BLOCKERS prevent smali_verified upgrade)
- Top-level fields: 100% verified (21/21 mapped to smali with line references)
- Nested parameters: 100% structurally verified (126/126 mapped to bean constructor)
- Sub-bean semantics: PARTIAL (AT1ProtectItem field meanings require device tests)

CRITICAL FINDING: Previous Schema Analysis
- Old schema: 11 fields at offsets 0-10
- Evidence: ALL 11 fields had INCORRECT offsets (100% ERROR RATE)
- Root cause: Assumed flat structure, ignored nested AT1BaseConfigItem arrays
- Parser reality: Nested beans + hexStrToEnableList() transforms + List<String> data

BLOCKERS for smali_verified upgrade:
1. Framework Support: Declarative schema does NOT support nested @dataclass objects
   - Requires: nested_field() decorator, List<NestedObject> support
   - Status: NOT IMPLEMENTED (framework limitation)
   - Alternative: Implement top-level fields only (13 fields), defer nested (134 fields)

2. Device Validation: Sub-bean field semantics require testing
   - AT1ProtectItem: 11 integer fields with unclear meanings (enable1-3, opp1-3, upp1-5)
   - AT1SOCThresholdItem: Flag bitfield extraction needs validation
   - Device tests: 5 tests planned (~6-8 hours, see evidence doc)

Schema Design Options:
- Option A (Flattened): 130+ fields with offset collisions → NOT FEASIBLE
- Option B (Nested): 20 components matching bean structure → RECOMMENDED but blocked

CAUTION: This block controls AT1 automatic transfer switch settings. Incorrect
configuration may:
- Result in improper grid/generator switching behavior
- Violate electrical code requirements for transfer switches
- Cause power interruption or equipment damage
- Lead to unsafe backfeed conditions if not properly configured

Only modify with proper understanding of transfer switch operation and local codes.

Current Implementation: EMPTY SCHEMA (nested structure deferred until
framework support).

Upgrade Path:
- IF framework adds nested dataclass support → Implement Option B + device tests
- THEN: partial → smali_verified (estimated 12-14 hours: impl + tests)
- UNTIL THEN: Remains partial (framework blocker documented)
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
