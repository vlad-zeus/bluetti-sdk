"""Block 17400 (AT1_SETTINGS) - AT1 Transfer Switch Extended Settings.

Source: ProtocolParserV2.smali switch case (0x43f8 -> sswitch_a)
Parser: AT1Parser.at1SettingsParse (lines 1933-3662)
Bean: AT1BaseSettings (20 components: 13 top-level + 7 nested AT1BaseConfigItem)
Block Type: parser-backed
Evidence: docs/re/17400-EVIDENCE.md (complete 147-field nested structure analysis)
Purpose: AT1 automatic transfer switch configuration (COMPLEX NESTED STRUCTURE)

Byte Offset Convention (data_index = byte_offset):
Each List<String> element in the Java parser = 1 hex-string byte value.
Therefore: byte_offset = data_index (1:1 mapping).
Fields at bytes 174+ are beyond min_length=91; marked required=False.

Structure:
- Min length: 91 bytes (0x5b)
- Data format: List<String> (hex strings → byte values)
- Total fields mapped in evidence: 147 across 20 components
- Verification: 90 PROVEN (61%), 40 PARTIAL (27%), 17 NOT_VERIFIED (12%)

Nested Object Hierarchy (AT1BaseSettings):
- 7x AT1BaseConfigItem nested objects (18 fields each):
  * configGrid (AT1Porn.GRID)
  * configSL1-4 (AT1Porn.SMART_LOAD_1-4)
  * configPCS1-2 (AT1Porn.PCS_1-2)
- 9x simple integer fields at bytes 176-181

Verification Status:
- Overall: partial (2 blockers remain - see below)
- Simple end-fields (bytes 176-181): SMALI_PROVEN offsets and transforms
- Nested config groups (config_grid, config_sl1): max_current PROVEN
- hexStrToEnableList fields: DEFERRED (transform not in framework)

BLOCKERS for smali_verified upgrade:
1. Transform: hexStrToEnableList() not in transform framework. Affects 9 top-level
   fields (bytes 0-11, 174-175) and per-item linkageEnable/type sub-fields.
   FieldGroup/NestedGroupSpec nested framework: CLEARED (2026-02-17).
2. Device: AT1ProtectItem/AT1SOCThresholdItem sub-bean semantics unverified.
   Full device validation required before upgrade (safety-critical block).

COMPLETION PASS (2026-02-17) - Evidence Re-Scan Results:
Evidence re-scan found 0 additional proven fields to add to the current schema.
All remaining PROVEN fields in docs/re/17400-EVIDENCE.md fall into one of:
- hexStrToEnableList transform (not in framework): chg_from_grid_enable,
  feed_to_grid_enable, delay_enable_1-3, black_start_enable, black_start_mode,
  generator_auto_start_enable, off_grid_power_priority, and per-config-item
  linkageEnable and type fields.
- Complex list parsing (not in FieldGroup model): forceEnable, timerEnable,
  protectList (protectEnableParse), socSetList (socThresholdParse).
- Pattern-inferred only (no direct smali ref): configSL2-4 max_current offsets
  (evidence says "pattern continues" but no explicit smali lines for SL2-4).
- Hardcoded constructor defaults (not read from data): powerOLPL1-3, powerULPL1-3,
  nameL1, nameL2, reserved1, reserved2.
All 7 currently modeled sub-fields are smali-proven. Status stays partial pending
device validation and hexStrToEnableList transform implementation.

CRITICAL FINDING: Previous schema with 11 fields was 100% INCORRECT.
Parser uses hexStrToEnableList() transformations and nested AT1BaseConfigItem
arrays, not flat integer fields as previously assumed.

CAUTION: Controls AT1 automatic transfer switch settings.
Incorrect configuration may:
- Result in improper grid/generator switching behavior
- Violate electrical code requirements for transfer switches
- Cause power interruption or equipment damage
- Lead to unsafe backfeed conditions
DO NOT write to this block without full verification.

Deferred fields (require hexStrToEnableList transform - NOT YET MODELED):
- chg_from_grid_enable (bytes 0-1, smali: 2012-2129)
- feed_to_grid_enable (bytes 2-3, smali: 2051-2142)
- delay_enable_1 (bytes 6-7, smali: 2145-2179)
- delay_enable_2 (bytes 8-9, smali: 2182-2216)
- delay_enable_3 (bytes 10-11, smali: 2219-2253)
- black_start_enable (bytes 174-175, smali: 3426-3478)
- black_start_mode (bytes 174-175, smali: 3480-3493)
- generator_auto_start_enable (bytes 174-175, smali: 3495-3508)
- off_grid_power_priority (bytes 174-175, smali: 3510-3523)

Deferred nested sub-fields (protectList, socSetList per config item):
- AT1ProtectItem (14 fields per item, up to 10 per config item)
- AT1SOCThresholdItem (8 fields per item, 6 per config item)
- All require complex sub-parser logic beyond current FieldGroup model
"""

from dataclasses import dataclass

from ..protocol.v2.datatypes import UInt8, UInt16
from ..protocol.v2.schema import Field
from .declarative import block_schema, nested_group


@block_schema(
    block_id=17400,
    name="ATS_EVENT_EXT",
    description="AT1 transfer switch extended settings (nested framework, partial)",
    min_length=91,
    protocol_version=2000,
    strict=False,
    verification_status="partial",
)
@dataclass
class ATSEventExtBlock:
    """AT1 settings - nested schema (evidence-accurate, device test pending).

    Parser: AT1Parser.at1SettingsParse (lines 1933-3662)
    Bean: AT1BaseSettings with 7x AT1BaseConfigItem nested objects

    Nested groups model the 7 AT1BaseConfigItem config objects plus
    the simple integer fields at bytes 176-181. Each group contains
    only the sub-fields with fully proven absolute byte offsets from
    smali analysis (see docs/re/17400-EVIDENCE.md).

    hexStrToEnableList-based fields are DEFERRED - see module docstring.

    STATUS: Uses nested framework; verification_status stays "partial"
    until device validation gate is cleared.

    SAFETY: CRITICAL - Controls AT1 automatic transfer switch.
    Do NOT write to this block without full device verification.
    """

    # ------------------------------------------------------------------
    # Nested groups: AT1BaseConfigItem objects (smali: lines 2466-3424)
    # Each group uses absolute byte offsets for its sub-fields.
    # Fields within min_length=91 bytes are conditionally required=False
    # since exact presence depends on packet variant.
    # ------------------------------------------------------------------

    # configGrid (AT1Porn.GRID) - smali: AT1Parser lines 2466-2613
    # max_current: data[84-85] → byte 84, UInt16 (PROVEN, smali: line 2578)
    config_grid = nested_group(
        "config_grid",
        sub_fields=[
            Field(
                name="max_current",
                offset=84,
                type=UInt16(),
                required=False,
                description=(
                    "Grid max current limit [parse hex] "
                    "(smali: line 2578, data[84-85])"
                ),
            ),
        ],
        required=False,
        description=(
            "AT1 grid config item (configGrid, AT1Porn.GRID). "
            "Smali: AT1Parser lines 2466-2613. "
            "18 parameters total; max_current proven at byte 84. "
            "Other fields deferred: forceEnable, timerEnable, protectList, "
            "socSetList require hexStrToEnableList transform."
        ),
        evidence_status="partial",
    )

    # configSL1 (AT1Porn.SMART_LOAD_1) - smali: AT1Parser lines 2616-2779
    # max_current: data[86-87] → byte 86, UInt16 (PROVEN, smali: lines 2744-2746)
    config_sl1 = nested_group(
        "config_sl1",
        sub_fields=[
            Field(
                name="max_current",
                offset=86,
                type=UInt16(),
                required=False,
                description=(
                    "SL1 max current limit [parse hex] "
                    "(smali: lines 2744-2746, data[86-87])"
                ),
            ),
        ],
        required=False,
        description=(
            "AT1 smart load 1 config item (configSL1, AT1Porn.SMART_LOAD_1). "
            "Smali: AT1Parser lines 2616-2779. "
            "18 parameters total; max_current proven at byte 86. "
            "Other fields deferred."
        ),
        evidence_status="partial",
    )

    # configSL2 (AT1Porn.SMART_LOAD_2) - smali: AT1Parser lines 2782-2939
    # max_current byte offset NOT proven in evidence (pattern suggests 88, deferred)
    config_sl2 = nested_group(
        "config_sl2",
        sub_fields=[],
        required=False,
        description=(
            "AT1 smart load 2 config item (configSL2, AT1Porn.SMART_LOAD_2). "
            "Smali: AT1Parser lines 2782-2939. "
            "max_current absolute offset not proven (deferred). "
            "Pattern from configGrid/SL1 suggests byte 88, unconfirmed."
        ),
        evidence_status="partial",
    )

    # configSL3 (AT1Porn.SMART_LOAD_3) - smali: AT1Parser lines 2942-3097
    config_sl3 = nested_group(
        "config_sl3",
        sub_fields=[],
        required=False,
        description=(
            "AT1 smart load 3 config item (configSL3, AT1Porn.SMART_LOAD_3). "
            "Smali: AT1Parser lines 2942-3097. "
            "max_current absolute offset not proven (deferred)."
        ),
        evidence_status="partial",
    )

    # configSL4 (AT1Porn.SMART_LOAD_4) - smali: AT1Parser lines 3100-3264
    config_sl4 = nested_group(
        "config_sl4",
        sub_fields=[],
        required=False,
        description=(
            "AT1 smart load 4 config item (configSL4, AT1Porn.SMART_LOAD_4). "
            "Smali: AT1Parser lines 3100-3264. "
            "max_current absolute offset not proven (deferred)."
        ),
        evidence_status="partial",
    )

    # configPCS1 (AT1Porn.PCS_1) - smali: AT1Parser lines 3267-3345
    config_pcs1 = nested_group(
        "config_pcs1",
        sub_fields=[],
        required=False,
        description=(
            "AT1 PCS1 config item (configPCS1, AT1Porn.PCS_1). "
            "Smali: AT1Parser lines 3267-3345. "
            "Data indices 95-159 (absolute sub-field offsets not proven)."
        ),
        evidence_status="partial",
    )

    # configPCS2 (AT1Porn.PCS_2) - smali: AT1Parser lines 3348-3424
    config_pcs2 = nested_group(
        "config_pcs2",
        sub_fields=[],
        required=False,
        description=(
            "AT1 PCS2 config item (configPCS2, AT1Porn.PCS_2). "
            "Smali: AT1Parser lines 3348-3424. "
            "Data indices 94-159 (absolute sub-field offsets not proven)."
        ),
        evidence_status="partial",
    )

    # ------------------------------------------------------------------
    # Simple integer fields at bytes 176-181 (beyond min_length=91)
    # Source: AT1Parser.smali lines 3525-3645 (ALL PROVEN)
    # Grouped into a single FieldGroup since they form a logical unit
    # and two fields (volt_level_set, ac_supply_phase_num) share the
    # same byte pair (176-177) with different bit extractions.
    # ------------------------------------------------------------------
    simple_end_fields = nested_group(
        "simple_end_fields",
        sub_fields=[
            Field(
                name="volt_level_set",
                offset=176,
                type=UInt16(),
                required=False,
                transform=("bitmask:0x7",),
                description=(
                    "Voltage level set [AND 0x7] "
                    "(smali: lines 3525-3567, data[176-177])"
                ),
            ),
            Field(
                name="ac_supply_phase_num",
                offset=176,
                type=UInt16(),
                required=False,
                transform=("shift:3", "bitmask:0x7"),
                description=(
                    "AC supply phase number [SHR 3, AND 0x7] "
                    "(smali: lines 3569-3578, data[176-177])"
                ),
            ),
            Field(
                name="soc_gen_auto_stop",
                offset=178,
                type=UInt8(),
                required=False,
                transform=("clamp:0:100",),
                description=(
                    "Generator auto-stop SOC threshold [0-100%] "
                    "(smali: lines 3580-3605, data[178])"
                ),
            ),
            Field(
                name="soc_gen_auto_start",
                offset=179,
                type=UInt8(),
                required=False,
                description=(
                    "Generator auto-start SOC threshold [parse hex] "
                    "(smali: lines 3607-3626, data[179])"
                ),
            ),
            Field(
                name="soc_black_start",
                offset=181,
                type=UInt8(),
                required=False,
                description=(
                    "Black start SOC threshold [parse hex] "
                    "(smali: lines 3628-3645, data[181])"
                ),
            ),
        ],
        required=False,
        description=(
            "Proven simple integer fields at bytes 176-181 "
            "(beyond min_length=91, required=False). "
            "Source: AT1Parser.smali lines 3525-3645 (smali_verified). "
            "Contains bit-extracted fields (volt_level_set, ac_supply_phase_num) "
            "and direct integer fields (soc_gen_auto_stop/start, soc_black_start)."
        ),
        evidence_status="smali_verified",
    )


# Export schema instance
BLOCK_17400_SCHEMA = ATSEventExtBlock.to_schema()  # type: ignore[attr-defined]
