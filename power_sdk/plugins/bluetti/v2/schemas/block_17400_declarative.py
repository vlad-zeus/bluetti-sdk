"""Block 17400 (AT1_SETTINGS) - AT1 Transfer Switch Extended Settings.

Source: ProtocolParserV2.reference switch case (0x43f8 -> sswitch_a)
Parser: AT1Parser.at1SettingsParse (lines 1933-3662)
Bean: AT1BaseSettings (20 components: 13 top-level + 7 nested AT1BaseConfigItem)
Block Type: parser-backed
Evidence: docs/re/17400-EVIDENCE.md (complete 147-field nested structure analysis)
Purpose: AT1 automatic transfer switch configuration (COMPLEX NESTED STRUCTURE)

Byte Offset Convention (data_index = byte_offset):
Each List<String> element in the Java parser = 1 hex-string byte value.
Therefore: byte_offset = data_index (1:1 mapping).
Fields at bytes 174+ are beyond min_length=96; marked required=False.

Structure:
- Min length: 96 bytes (0x60)
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
- Simple end-fields (bytes 176-181): reference_PROVEN offsets and transforms
- Nested config groups (config_grid, config_sl1): max_current PROVEN
- hexStrToEnableList fields: DEFERRED (transform not in framework)

BLOCKERS for verified_reference upgrade:
1. Transform: hexStrToEnableList() - CLEARED (2026-02-17): hex_enable_list transform
   implemented. Scalar index fields (chg/feed_to_grid_enable, black_start_*, etc.)
   now added. delayEnable1-3 remain deferred (full List<Integer>, not a single index).
   FieldGroup/NestedGroupSpec nested framework: CLEARED (2026-02-17).
2. Device: AT1ProtectItem/AT1SOCThresholdItem sub-bean semantics unverified.
   Full device validation required before upgrade (safety-critical block).

COMPLETION PASS (2026-02-17) - Evidence Re-Scan Results:
Evidence re-scan found 0 additional proven fields beyond hex_enable_list fields.
After hex_enable_list transform added (2026-02-17), still deferred:
- delay_enable_1-3 (bytes 6-11): full List<Integer> output (not a single index)
- forceEnable, timerEnable, protectList, socSetList: complex list/sub-parser logic
- Hardcoded defaults (not read from data): powerOLPL1-3, powerULPL1-3, names, reserved
Total proven sub-fields: 30 (7 original + 10 hex_enable_list unlock + 6 force_enable
+ 7 new fields from analysis audit 2026-02-17).
Status stays partial pending device validation.

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

Fields ADDED (2026-02-17) using hex_enable_list transform:
- top_level_enables.chg_from_grid_enable (bytes 0-1, index [3], reference: 2012-2129)
- top_level_enables.feed_to_grid_enable (bytes 2-3, index [4], reference: 2051-2142)
- startup_flags.black_start_enable (bytes 174-175, index [2], reference: 3426-3478)
- startup_flags.black_start_mode (bytes 174-175, index [3], reference: 3480-3493)
- startup_flags.generator_auto_start_enable
  (bytes 174-175, index [4], reference: 3495-3508)
- startup_flags.off_grid_power_priority (bytes 174-175, index [5], reference: 3510-3523)
- config_grid.type (bytes 18-19, index [0], reference: 2472-2480)
- config_grid.linkage_enable (bytes 32-33, index [0], reference: 2504-2510)
- config_sl1.type (bytes 18-19, index [1], reference: 2624-2632)
- config_sl1.linkage_enable (bytes 32-33, index [1], reference: 2654-2663)

Fields ADDED (2026-02-17) — force_enable (analysis audit corrected offsets):
- config_grid.force_enable_0/1/2 (bytes 12-13, reference: 2258-2483)
- config_sl1.force_enable_0/1/2 (bytes 2-3, reference: 2081-2635)

Still deferred (full List<Integer>, no element-level reference evidence):
- delay_enable_1 (bytes 6-7, reference: 2145-2179) — usage not shown in evidence
- delay_enable_2 top-level list (elements [3-7] not shown used anywhere)
- delay_enable_3 top-level list (elements [3-7] not shown used anywhere)
- timer_enable (bytes 24-31): complex sub-parser (protectEnableParse logic)

Deferred nested sub-fields (protectList, socSetList per config item):
- AT1ProtectItem (14 fields per item, up to 10 per config item)
- AT1SOCThresholdItem (8 fields per item, 6 per config item)
- All require complex sub-parser logic beyond current FieldGroup model

analysis AUDIT CORRECTIONS (2026-02-17):
Independent reference verification (Agent B + Agent C) found 6 wrong byte offsets
in the prior schema. All corrected with exact reference evidence:
- config_grid.type: offset 18 → 20 (data[0x14]+data[0x15], reference lines 2398-2472)
- config_grid.linkage_enable: offset 32 → 22
  (data[0x16]+data[0x17], reference 2433-2494)
- config_grid.force_enable_0/1/2: offset 8 → 12
  (data[0x0c]+data[0x0d], reference 2258-2483)
- config_sl1.type: offset 18 → 20 (same list, index 1, reference 2621-2624)
- config_sl1.linkage_enable: offset 32 → 22 (same list, index 1, reference 2652-2655)
- config_sl1.force_enable_0/1/2: offset 10 → 2
  (data[0x02]+data[0x03], reference 2081-2635)
New proven fields added (7):
- config_sl2.max_current: offset 88, UInt16 (reference 2869-2906)
- config_sl3.max_current: offset 90, UInt16 (reference 3027-3064)
- config_sl4.max_current: offset 92, UInt16 (reference 3192-3229)
- config_pcs1.type: offset 18, UInt16, hex_enable_list:0:0 (reference 2393-3272)
- config_pcs1.max_current: offset 95, UInt8 single byte (reference 3287-3304)
- config_pcs2.type: offset 18, UInt16, hex_enable_list:0:1 (reference 2393-3356)
- config_pcs2.max_current: offset 94, UInt8 single byte (reference 3366-3383)
"""

from dataclasses import dataclass

from ..protocol.datatypes import UInt8, UInt16
from ..protocol.schema import Field
from .declarative import block_schema, nested_group


@block_schema(
    block_id=17400,
    name="ATS_EVENT_EXT",
    description="AT1 transfer switch extended settings (nested framework, partial)",
    min_length=96,  # config_pcs1.max_current at offset 95 (UInt8) → end=96
    protocol_version=2000,
    strict=False,
    verification_status="partial",
)
@dataclass
class ATSEventExtBlock:
    """AT1 settings - nested schema (evidence-accurate, device test pending).

    Parser: AT1Parser.at1SettingsParse (lines 1933-3662)
    Bean: AT1BaseSettings with 7x AT1BaseConfigItem nested objects

    10 FieldGroups total (8 original + 2 new after hex_enable_list unlock):
    - top_level_enables: chg_from_grid_enable, feed_to_grid_enable
    - startup_flags: black_start_*, generator_auto_start_enable, off_grid_power_priority
    - config_grid through config_pcs2: AT1BaseConfigItem sub-objects
    - simple_end_fields: volt_level_set, soc thresholds (bytes 176-181)

    30 proven sub-fields total:
    7 original + 10 hex_enable_list unlock + 6 force_enable + 7 analysis audit.
    delayEnable1 (bytes 6-7) and timer_enable remain deferred (full list, no
    proven element-level usage; timerEnable uses complex protectEnableParse).

    STATUS: Uses nested framework; verification_status stays "partial"
    until device validation gate is cleared.

    SAFETY: CRITICAL - Controls AT1 automatic transfer switch.
    Do NOT write to this block without full device verification.
    """

    # ------------------------------------------------------------------
    # Top-level AT1BaseSettings enable flags (hex_enable_list transform)
    # Unlocked 2026-02-17 after hex_enable_list transform added to framework.
    # ------------------------------------------------------------------

    # chgFromGridEnable (bytes 0-1) and feedToGridEnable (bytes 2-3)
    # Both use hexStrToEnableList(data[N]+data[N+1], chunkMode=0)[index]
    # chgFromGridEnable: reference AT1Parser lines 2012-2129, index [3]
    # feedToGridEnable:  reference AT1Parser lines 2051-2142, index [4]
    top_level_enables = nested_group(
        "top_level_enables",
        sub_fields=[
            Field(
                name="chg_from_grid_enable",
                offset=0,
                type=UInt16(),
                required=False,
                transform=("hex_enable_list:0:3",),
                description=(
                    "Charge from grid enable [hexStrToEnableList()[3]] "
                    "(reference: AT1Parser lines 2012-2129, data[0-1])"
                ),
            ),
            Field(
                name="feed_to_grid_enable",
                offset=2,
                type=UInt16(),
                required=False,
                transform=("hex_enable_list:0:4",),
                description=(
                    "Feed to grid enable [hexStrToEnableList()[4]] "
                    "(reference: AT1Parser lines 2051-2142, data[2-3])"
                ),
            ),
        ],
        required=False,
        description=(
            "Top-level AT1BaseSettings charge/feed enable flags. "
            "hexStrToEnableList(data[N]+data[N+1], chunkMode=0)[idx]. "
            "Confirmed AT1Parser.reference lines 2012-2142. "
            "delayEnable1-3 (bytes 6-11, full List<Integer>) remain deferred."
        ),
        evidence_status="verified_reference",
    )

    # blackStartEnable, blackStartMode, generatorAutoStartEnable, offGridPowerPriority
    # All use hexStrToEnableList(data[174]+data[175], chunkMode=0)[2,3,4,5]
    # Confirmed AT1Parser.reference lines 3426-3523 (indices observed: list.get(2-5))
    startup_flags = nested_group(
        "startup_flags",
        sub_fields=[
            Field(
                name="black_start_enable",
                offset=174,
                type=UInt16(),
                required=False,
                transform=("hex_enable_list:0:2",),
                description=(
                    "Black start enable [hexStrToEnableList()[2]] "
                    "(reference: AT1Parser lines 3426-3478, data[174-175])"
                ),
            ),
            Field(
                name="black_start_mode",
                offset=174,
                type=UInt16(),
                required=False,
                transform=("hex_enable_list:0:3",),
                description=(
                    "Black start mode [hexStrToEnableList()[3]] "
                    "(reference: AT1Parser lines 3480-3493, data[174-175])"
                ),
            ),
            Field(
                name="generator_auto_start_enable",
                offset=174,
                type=UInt16(),
                required=False,
                transform=("hex_enable_list:0:4",),
                description=(
                    "Generator auto-start enable [hexStrToEnableList()[4]] "
                    "(reference: AT1Parser lines 3495-3508, data[174-175])"
                ),
            ),
            Field(
                name="off_grid_power_priority",
                offset=174,
                type=UInt16(),
                required=False,
                transform=("hex_enable_list:0:5",),
                description=(
                    "Off-grid power priority [hexStrToEnableList()[5]] "
                    "(reference: AT1Parser lines 3510-3523, data[174-175])"
                ),
            ),
        ],
        required=False,
        description=(
            "AT1BaseSettings startup/grid flags at bytes 174-175. "
            "All 4 fields: hexStrToEnableList(data[174]+data[175], mode=0)[2,3,4,5]. "
            "Confirmed AT1Parser.reference lines 3426-3523 (list.get(2-5) calls)."
        ),
        evidence_status="verified_reference",
    )

    # ------------------------------------------------------------------
    # Nested groups: AT1BaseConfigItem objects (reference: lines 2466-3424)
    # Each group uses absolute byte offsets for its sub-fields.
    # Fields within min_length=96 bytes are conditionally required=False
    # since exact presence depends on packet variant.
    # ------------------------------------------------------------------

    # configGrid (AT1Porn.GRID) - reference: AT1Parser lines 2466-2613
    # max_current: data[84-85] → byte 84, UInt16 (PROVEN, reference: line 2578)
    # field type: data[20-21] → byte 20, hexStrToEnableList()[0] (reference: 2398-2472)
    # linkage_enable: data[22-23] → byte 22,
    # hexStrToEnableList()[0] (reference: 2433-2494)
    # force_enable[0-2]: data[12-13] [0,1,2] (reference: 2258-2483)
    # NOTE: force_enable source is hexStrToEnableList(data[12]+data[13]).take(3)
    # NOT from delayEnable2 (bytes 8-9). Prior evidence was wrong; corrected by
    # analysis audit (Agent B confirmed, Agent C independently verified 2026-02-17).
    config_grid = nested_group(
        "config_grid",
        sub_fields=[
            Field(
                name="type",
                offset=20,
                type=UInt16(),
                required=False,
                transform=("hex_enable_list:0:0",),
                description=(
                    "Grid config type [hexStrToEnableList()[0]] "
                    "(reference: AT1Parser lines 2398-2472, data[20-21])"
                ),
            ),
            Field(
                name="linkage_enable",
                offset=22,
                type=UInt16(),
                required=False,
                transform=("hex_enable_list:0:0",),
                description=(
                    "Grid linkage enable [hexStrToEnableList()[0]] "
                    "(reference: AT1Parser lines 2433-2494, data[22-23])"
                ),
            ),
            Field(
                name="force_enable_0",
                offset=12,
                type=UInt16(),
                required=False,
                transform=("hex_enable_list:0:0",),
                description=(
                    "Grid forceEnable[0] [hexStrToEnableList(data[12-13]).take(3)[0]] "
                    "(reference: AT1Parser lines 2258-2483, data[12-13])"
                ),
            ),
            Field(
                name="force_enable_1",
                offset=12,
                type=UInt16(),
                required=False,
                transform=("hex_enable_list:0:1",),
                description=(
                    "Grid forceEnable[1] [hexStrToEnableList(data[12-13]).take(3)[1]] "
                    "(reference: AT1Parser lines 2258-2483, data[12-13])"
                ),
            ),
            Field(
                name="force_enable_2",
                offset=12,
                type=UInt16(),
                required=False,
                transform=("hex_enable_list:0:2",),
                description=(
                    "Grid forceEnable[2] [hexStrToEnableList(data[12-13]).take(3)[2]] "
                    "(reference: AT1Parser lines 2258-2483, data[12-13])"
                ),
            ),
            Field(
                name="max_current",
                offset=84,
                type=UInt16(),
                required=False,
                description=(
                    "Grid max current limit [parse hex] "
                    "(reference: line 2578, data[84-85])"
                ),
            ),
        ],
        required=False,
        description=(
            "AT1 grid config item (configGrid, AT1Porn.GRID). "
            "reference: AT1Parser lines 2466-2613. "
            "6 proven: type(off=20)/linkage_enable(off=22)"
            "/force_enable_0/1/2(off=12)/max_current. "
            "Offset corrections: type 18→20, linkage_enable 32→22, "
            "force_enable 8→12. "
            "Deferred: timerEnable, protectList, socSetList."
        ),
        evidence_status="partial",
    )

    # configSL1 (AT1Porn.SMART_LOAD_1) - reference: AT1Parser lines 2616-2779
    # max_current: data[86-87] → byte 86, UInt16 (PROVEN, reference: lines 2744-2746)
    # field type: data[20-21] → byte 20, hexStrToEnableList()[1] (reference: 2621-2624)
    # linkage_enable: data[22-23] → byte 22,
    # hexStrToEnableList()[1] (reference: 2652-2655)
    # force_enable[0-2]: data[2-3] [0,1,2] via v4 (reference: 2081-2635)
    # NOTE: force_enable comes from hexStrToEnableList(data[2]+data[3]).take(3)[0-2]
    # via register v4 preserved from line 2081 (feedToGridEnable list) to line 2635.
    # NOT from delayEnable3 (bytes 10-11). Prior evidence was wrong; corrected by
    # analysis audit (Agent B confirmed, Agent C independently verified 2026-02-17).
    config_sl1 = nested_group(
        "config_sl1",
        sub_fields=[
            Field(
                name="type",
                offset=20,
                type=UInt16(),
                required=False,
                transform=("hex_enable_list:0:1",),
                description=(
                    "SL1 config type [hexStrToEnableList()[1]] "
                    "(reference: AT1Parser lines 2621-2624, data[20-21])"
                ),
            ),
            Field(
                name="linkage_enable",
                offset=22,
                type=UInt16(),
                required=False,
                transform=("hex_enable_list:0:1",),
                description=(
                    "SL1 linkage enable [hexStrToEnableList()[1]] "
                    "(reference: AT1Parser lines 2652-2655, data[22-23])"
                ),
            ),
            Field(
                name="force_enable_0",
                offset=2,
                type=UInt16(),
                required=False,
                transform=("hex_enable_list:0:0",),
                description=(
                    "SL1 forceEnable[0] [hexStrToEnableList(data[2-3]).take(3)[0]] "
                    "(reference: AT1Parser lines 2081-2635, data[2-3])"
                ),
            ),
            Field(
                name="force_enable_1",
                offset=2,
                type=UInt16(),
                required=False,
                transform=("hex_enable_list:0:1",),
                description=(
                    "SL1 forceEnable[1] [hexStrToEnableList(data[2-3]).take(3)[1]] "
                    "(reference: AT1Parser lines 2081-2635, data[2-3])"
                ),
            ),
            Field(
                name="force_enable_2",
                offset=2,
                type=UInt16(),
                required=False,
                transform=("hex_enable_list:0:2",),
                description=(
                    "SL1 forceEnable[2] [hexStrToEnableList(data[2-3]).take(3)[2]] "
                    "(reference: AT1Parser lines 2081-2635, data[2-3])"
                ),
            ),
            Field(
                name="max_current",
                offset=86,
                type=UInt16(),
                required=False,
                description=(
                    "SL1 max current limit [parse hex] "
                    "(reference: lines 2744-2746, data[86-87])"
                ),
            ),
        ],
        required=False,
        description=(
            "AT1 smart load 1 config item (configSL1, AT1Porn.SMART_LOAD_1). "
            "reference: AT1Parser lines 2616-2779. "
            "6 proven: type(off=20)/linkage_enable(off=22)"
            "/force_enable_0/1/2(off=2)/max_current. "
            "Offset corrections: type 18→20, linkage_enable 32→22, "
            "force_enable 10→2. "
            "Deferred: timerEnable, protectList, socSetList."
        ),
        evidence_status="partial",
    )

    # configSL2 (AT1Porn.SMART_LOAD_2) - reference: AT1Parser lines 2782-2939
    # max_current: data[0x58]+data[0x59] = bytes 88-89, UInt16
    #   (PROVEN, reference: 2869-2906)
    config_sl2 = nested_group(
        "config_sl2",
        sub_fields=[
            Field(
                name="max_current",
                offset=88,
                type=UInt16(),
                required=False,
                description=(
                    "SL2 max current limit [parseInt(data[88-89], 16)] "
                    "(reference: AT1Parser lines 2869-2906, data[0x58]+data[0x59])"
                ),
            ),
        ],
        required=False,
        description=(
            "AT1 smart load 2 config item (configSL2, AT1Porn.SMART_LOAD_2). "
            "reference: AT1Parser lines 2782-2939. "
            "1 proven: max_current at byte 88 (analysis audit confirmed 2026-02-17)."
        ),
        evidence_status="partial",
    )

    # configSL3 (AT1Porn.SMART_LOAD_3) - reference: AT1Parser lines 2942-3097
    # max_current: data[0x5a]+data[0x5b] = bytes 90-91, UInt16
    #   (PROVEN, reference: 3027-3064)
    config_sl3 = nested_group(
        "config_sl3",
        sub_fields=[
            Field(
                name="max_current",
                offset=90,
                type=UInt16(),
                required=False,
                description=(
                    "SL3 max current limit [parseInt(data[90-91], 16)] "
                    "(reference: AT1Parser lines 3027-3064, data[0x5a]+data[0x5b])"
                ),
            ),
        ],
        required=False,
        description=(
            "AT1 smart load 3 config item (configSL3, AT1Porn.SMART_LOAD_3). "
            "reference: AT1Parser lines 2942-3097. "
            "1 proven: max_current at byte 90 (analysis audit confirmed 2026-02-17)."
        ),
        evidence_status="partial",
    )

    # configSL4 (AT1Porn.SMART_LOAD_4) - reference: AT1Parser lines 3100-3264
    # max_current: data[0x5c]+data[0x5d] = bytes 92-93, UInt16
    #   (PROVEN, reference: 3192-3229)
    config_sl4 = nested_group(
        "config_sl4",
        sub_fields=[
            Field(
                name="max_current",
                offset=92,
                type=UInt16(),
                required=False,
                description=(
                    "SL4 max current limit [parseInt(data[92-93], 16)] "
                    "(reference: AT1Parser lines 3192-3229, data[0x5c]+data[0x5d])"
                ),
            ),
        ],
        required=False,
        description=(
            "AT1 smart load 4 config item (configSL4, AT1Porn.SMART_LOAD_4). "
            "reference: AT1Parser lines 3100-3264. "
            "1 proven: max_current at byte 92 (analysis audit confirmed 2026-02-17)."
        ),
        evidence_status="partial",
    )

    # configPCS1 (AT1Porn.PCS_1) - reference: AT1Parser lines 3267-3345
    # field "type": hexStrToEnableList(data[18]+data[19]).get(0) → offset 18, UInt16
    #   Source list (v46) computed at reference line 2393-2527, used at line 3272.
    # field "max_current": data[0x5f] = byte 95, SINGLE BYTE (UInt8), parseInt only
    #   CRITICAL: UInt8, NOT UInt16. Parser reads one hex byte, not two.
    #   (reference: AT1Parser lines 3287-3304)
    config_pcs1 = nested_group(
        "config_pcs1",
        sub_fields=[
            Field(
                name="type",
                offset=18,
                type=UInt16(),
                required=False,
                transform=("hex_enable_list:0:0",),
                description=(
                    "PCS1 config type [hexStrToEnableList(data[18-19]).get(0)] "
                    "(reference: AT1Parser lines 2393-3272, data[18-19])"
                ),
            ),
            Field(
                name="max_current",
                offset=95,
                type=UInt8(),
                required=False,
                description=(
                    "PCS1 max current limit [parseInt(data[95], 16), single byte] "
                    "(reference: AT1Parser lines 3287-3304, data[0x5f])"
                ),
            ),
        ],
        required=False,
        description=(
            "AT1 PCS1 config item (configPCS1, AT1Porn.PCS_1). "
            "reference: AT1Parser lines 3267-3345. "
            "2 proven: type(off=18)/max_current(off=95, UInt8 single byte). "
            "Note: max_current is UInt8 (single byte parse), NOT UInt16."
        ),
        evidence_status="partial",
    )

    # configPCS2 (AT1Porn.PCS_2) - reference: AT1Parser lines 3348-3424
    # field "type": hexStrToEnableList(data[18]+data[19]).get(1) → offset 18, UInt16
    #   Same source list (v46) as PCS1, index [1] (reference: AT1Parser 3353-3356).
    # field "max_current": data[0x5e] = byte 94, SINGLE BYTE (UInt8), parseInt only
    #   (reference: AT1Parser lines 3366-3383)
    config_pcs2 = nested_group(
        "config_pcs2",
        sub_fields=[
            Field(
                name="type",
                offset=18,
                type=UInt16(),
                required=False,
                transform=("hex_enable_list:0:1",),
                description=(
                    "PCS2 config type [hexStrToEnableList(data[18-19]).get(1)] "
                    "(reference: AT1Parser lines 2393-3356, data[18-19])"
                ),
            ),
            Field(
                name="max_current",
                offset=94,
                type=UInt8(),
                required=False,
                description=(
                    "PCS2 max current limit [parseInt(data[94], 16), single byte] "
                    "(reference: AT1Parser lines 3366-3383, data[0x5e])"
                ),
            ),
        ],
        required=False,
        description=(
            "AT1 PCS2 config item (configPCS2, AT1Porn.PCS_2). "
            "reference: AT1Parser lines 3348-3424. "
            "2 proven: type(off=18)/max_current(off=94, UInt8 single byte). "
            "Note: max_current is UInt8 (single byte parse), NOT UInt16."
        ),
        evidence_status="partial",
    )

    # ------------------------------------------------------------------
    # Simple integer fields at bytes 176-181 (beyond min_length=96)
    # Source: AT1Parser.reference lines 3525-3645 (ALL PROVEN)
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
                    "(reference: lines 3525-3567, data[176-177])"
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
                    "(reference: lines 3569-3578, data[176-177])"
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
                    "(reference: lines 3580-3605, data[178])"
                ),
            ),
            Field(
                name="soc_gen_auto_start",
                offset=179,
                type=UInt8(),
                required=False,
                description=(
                    "Generator auto-start SOC threshold [parse hex] "
                    "(reference: lines 3607-3626, data[179])"
                ),
            ),
            Field(
                name="soc_black_start",
                offset=181,
                type=UInt8(),
                required=False,
                description=(
                    "Black start SOC threshold [parse hex] "
                    "(reference: lines 3628-3645, data[181])"
                ),
            ),
        ],
        required=False,
        description=(
            "Proven simple integer fields at bytes 176-181 "
            "(beyond min_length=96, required=False). "
            "Source: AT1Parser.reference lines 3525-3645 (verified_reference). "
            "Contains bit-extracted fields (volt_level_set, ac_supply_phase_num) "
            "and direct integer fields (soc_gen_auto_stop/start, soc_black_start)."
        ),
        evidence_status="verified_reference",
    )


# Export schema instance
BLOCK_17400_SCHEMA = ATSEventExtBlock.to_schema()  # type: ignore[attr-defined]
