"""Block 15600 (DC_DC_SETTINGS) - DC-DC Converter Configuration Settings.

Source: ProtocolParserV2.smali switch case (0x3cf0 -> sswitch_12)
Parser: DCDCParser.settingsInfoParse (lines 1780-3195)
Bean: DCDCSettings.smali (46 fields fully mapped)
Block Type: parser-backed
Evidence: docs/re/15600-EVIDENCE.md (complete field-level analysis)
Purpose: DC-DC converter voltage/current setpoints and operation mode control

Structure:
- Min length from smali: 36 bytes (baseline)
- Protocol version gates:
  - size <= 4 words: Baseline control fields only (dcCtrl through voltSetDC1)
  - size <= 26 words: Adds charging modes and battery settings
  - size <= 54 words: Adds system control and recharger power fields
  - size > 54 words: Full feature set (up to 99 words / 198 bytes)
- Total fields: 46 (34 PROVEN, 12 PARTIAL - see evidence doc)

Verification Status:
- Overall: partial (3 CRITICAL blockers prevent smali_verified upgrade)
- PROVEN: 34/46 fields (74%) - offsets, types, transforms verified from smali
- PARTIAL: 12/46 fields (26%) - voltage/current/power scales UNKNOWN

CRITICAL ELECTRICAL SAFETY WARNING:
- This block controls DC-DC converter output voltage and current limits
- Scale factors for voltage/current setpoints are UNKNOWN (raw hex values)
- Incorrect setpoints can damage equipment or create fire/electrical hazards
- DO NOT implement write operations without actual device validation
- All control fields should be treated as READ-ONLY until scale factors verified

CRITICAL FINDING: Read vs Write Scale Discrepancy
- Block 15500 (DCDCInfo - readings): parseInt(16) ÷ 10.0f
  → PROVEN scale: x0.1V, x0.1A
- Block 15600 (DCDCSettings - setpoints): parseInt(16) RAW
  → NO DIVISION → scale: UNKNOWN

Bytecode Evidence:
- Block 15500 baseInfoParse: Contains 3x div-float operations (lines 265, 308, 351)
- Block 15600 settingsInfoParse: ZERO div-float operations in entire parser (3195 lines)
- grep confirmation: "div-float" found in Block 15500, NOT found in Block 15600

Safety Impact:
- If write scale is x1V and user writes 245 (expecting 24.5V),
  output = 245V → EQUIPMENT DAMAGE
- If write scale is x0.1V and user writes 24,
  output = 2.4V → INCORRECT VOLTAGE
- Cannot determine correct scale without device testing

BLOCKERS for smali_verified upgrade:
1. Voltage setpoints (voltSetDC1-3): Scale UNKNOWN - SAFETY CRITICAL
2. Current setpoints (outputCurrentDC1-3): Scale UNKNOWN - SAFETY CRITICAL
3. Power/battery fields: Units unverified (likely W/mAh but not proven)

Device Validation Required:
- See docs/re/15600-EVIDENCE.md for complete 5-test validation plan
- Minimum mandatory: Tests 1-2 (voltage + current scale factors, ~4 hours)
- Complete validation: All 5 tests (~6 hours total)

Recommended Action: DO NOT implement write operations until device tests complete.
"""

from dataclasses import dataclass

from ..protocol.v2.datatypes import UInt16
from .declarative import block_field, block_schema


@block_schema(
    block_id=15600,
    name="DC_DC_SETTINGS",
    description="DC-DC converter configuration (provisional - no parse method)",
    min_length=36,
    protocol_version=2000,
    strict=False,
    verification_status="partial",
)
@dataclass
class DCDCSettingsBlock:
    """DC-DC converter settings schema (provisional baseline).

    This block has no documented parse method. Field mapping is
    provisional pending device testing and bean structure analysis.

    SECURITY WARNING: Voltage/current control - verify safe operating limits.
    """

    dc_ctrl: int = block_field(
        offset=0,
        type=UInt16(),
        description=(
            "DC-DC enable control [bit 0, transform: hexStrToEnableList] "
            "(smali: lines 1909-1958)"
        ),
        required=False,
        default=0,
    )
    silent_mode_ctrl: int = block_field(
        offset=0,
        type=UInt16(),
        description=(
            "Silent mode enable [bit 1, transform: hexStrToEnableList] "
            "(smali: lines 1961-1971)"
        ),
        required=False,
        default=0,
    )
    factory_set: int = block_field(
        offset=0,
        type=UInt16(),
        description=(
            "Factory settings flag [bit 2, transform: hexStrToEnableList] "
            "(smali: lines 1974-1984)"
        ),
        required=False,
        default=0,
    )
    self_adaption_enable: int = block_field(
        offset=0,
        type=UInt16(),
        description=(
            "Self-adaption enable [bit 3, transform: hexStrToEnableList] "
            "(smali: lines 1987-1999)"
        ),
        required=False,
        default=0,
    )
    volt_set_dc1: int = block_field(
        offset=2,
        type=UInt16(),
        unit="UNKNOWN",
        description=(
            "DC1 voltage setpoint [SAFETY CRITICAL: Scale unknown, raw hex] "
            "(smali: lines 2002-2036)"
        ),
        required=False,
        default=0,
    )
    output_current_dc1: int = block_field(
        offset=4,
        type=UInt16(),
        unit="UNKNOWN",
        description=(
            "DC1 output current limit [SAFETY CRITICAL: Scale unknown, "
            "conditional: size>4] (smali: lines 2039-2086)"
        ),
        required=False,
        default=0,
    )
    volt_set_dc2: int = block_field(
        offset=6,
        type=UInt16(),
        unit="UNKNOWN",
        description=(
            "DC2 voltage setpoint [SAFETY CRITICAL: Scale unknown, raw hex] "
            "(smali: lines 2089-2123)"
        ),
        required=False,
        default=0,
    )
    # TODO: Add outputCurrentDC2 (offset 8-9, smali: lines 2127-2162)
    # TODO: Add voltSetDC3 (offset 10-11, smali: lines 2167-2201)
    # TODO: Add outputCurrentDC3 (offset 12-13, smali: lines 2204-2238)
    # TODO: Add voltSet2DC3 (offset 22-23, smali: lines 2240-2277)
    # TODO: Add setEvent1 list field (offset TBD, smali: line 2328)
    # TODO: Add chgModeDC1/2/3/4 (offsets TBD, smali: lines 2370-2391)
    # TODO: Add battery settings (capacity, type, modelType - lines 2424-2460)
    # TODO: Add powerDC1-5 (offsets TBD, smali: lines 2489-2605)
    # TODO: Add dcTotalPowerSet (offset TBD, smali: line 2634)
    # TODO: Add feature flags (genCheckEnable, genType, etc. - lines 2684-2748)
    # TODO: Add mode settings (reverseChgMode, sysPowerCtrl, etc. - lines 2767-2815)
    # TODO: Add recharger power settings (rechargerPowerDC1-5 - lines 2854-3010)
    # TODO: Add advanced settings (voltSetMode, pscModelNumber, etc. - lines 3051-3176)
    # Total: 33+ additional fields requiring offset mapping and safety validation


# Export schema instance
BLOCK_15600_SCHEMA = DCDCSettingsBlock.to_schema()  # type: ignore[attr-defined]
