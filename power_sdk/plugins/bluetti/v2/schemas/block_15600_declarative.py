"""Block 15600 (DC_DC_SETTINGS) - DC-DC Converter Configuration Settings.

Source: ProtocolParserV2.reference switch case (0x3cf0 -> sswitch_12)
Parser: DCDCParser.settingsInfoParse (lines 1780-3195)
Bean: DCDCSettings.reference
Block Type: parser-backed
Evidence: docs/re/15600-EVIDENCE.md (complete field-level analysis)
Purpose: DC-DC converter voltage/current setpoints and operation mode control

Structure:
- Min length from reference: 36 bytes (baseline)
- Protocol version gates:
  - size <= 4 words: Baseline control fields only (dcCtrl through voltSetDC1)
  - size <= 26 words: Adds charging modes and battery settings
  - size <= 54 words: Adds system control and recharger power fields
  - size > 54 words: Full feature set (up to 99 words / 198 bytes)

Verification Status:
- Overall: partial (narrow device gate remains for outputCurrentDC1/DC2)
- PROVEN scale factors: voltSetDC1/2/3 and outputCurrentDC3 use x0.1
- UNKNOWN scale factors: outputCurrentDC1/DC2 (no direct caller evidence)

CRITICAL ELECTRICAL SAFETY WARNING:
- This block controls DC-DC converter output voltage and current limits
- Scale factors are mixed:
  * PROVEN: voltSetDC1/2/3 and outputCurrentDC3 use x0.1
  * UNKNOWN: outputCurrentDC1/DC2
- Incorrect setpoints can damage equipment or create fire/electrical hazards
- DO NOT implement write operations without actual device validation

BLOCKERS for verified_reference upgrade:
1. outputCurrentDC1/DC2 scale UNKNOWN - SAFETY CRITICAL
2. Power/battery field semantics and units still need full closure
"""

from dataclasses import dataclass

from ..protocol.datatypes import UInt16
from ..protocol.transforms import hex_enable_list, scale
from .declarative import block_field, block_schema


@block_schema(
    block_id=15600,
    name="DC_DC_SETTINGS",
    description="DC-DC converter configuration (partial verification, safety-gated)",
    min_length=36,
    strict=False,
    verification_status="partial",
)
@dataclass
class DCDCSettingsBlock:
    """DC-DC converter settings schema (partial, evidence-accurate baseline).

    Parser path is confirmed (DCDCParser.settingsInfoParse). Only proven scale
    factors are applied in schema transforms.

    SECURITY WARNING: output_current_dc1/output_current_dc2 scales remain unknown.
    """

    dc_ctrl: int = block_field(
        offset=0,
        type=UInt16(),
        transform=[hex_enable_list(mode=0, index=0)],
        description=(
            "DC-DC enable control [element 0, hexStrToEnableList mode=0] "
            "(reference: lines 1909-1958)"
        ),
        required=False,
        default=0,
    )
    silent_mode_ctrl: int = block_field(
        offset=0,
        type=UInt16(),
        transform=[hex_enable_list(mode=0, index=1)],
        description=(
            "Silent mode enable [element 1, hexStrToEnableList mode=0] "
            "(reference: lines 1961-1971)"
        ),
        required=False,
        default=0,
    )
    factory_set: int = block_field(
        offset=0,
        type=UInt16(),
        transform=[hex_enable_list(mode=0, index=2)],
        description=(
            "Factory settings flag [element 2, hexStrToEnableList mode=0] "
            "(reference: lines 1974-1984)"
        ),
        required=False,
        default=0,
    )
    self_adaption_enable: int = block_field(
        offset=0,
        type=UInt16(),
        transform=[hex_enable_list(mode=0, index=3)],
        description=(
            "Self-adaption enable [element 3, hexStrToEnableList mode=0] "
            "(reference: lines 1987-1999)"
        ),
        required=False,
        default=0,
    )
    volt_set_dc1: float = block_field(
        offset=2,
        type=UInt16(),
        unit="V",
        transform=[scale(0.1)],
        description=(
            "DC1 voltage setpoint (PROVEN x0.1V from caller reference evidence) "
            "(settingsInfoParse lines 2002-2036)"
        ),
        required=False,
        default=0.0,
    )
    output_current_dc1: int = block_field(
        offset=4,
        type=UInt16(),
        unit="UNKNOWN",
        description=(
            "DC1 output current limit [SAFETY CRITICAL: Scale unknown, "
            "conditional: size>4] (reference: lines 2039-2086)"
        ),
        required=False,
        default=0,
    )
    volt_set_dc2: float = block_field(
        offset=6,
        type=UInt16(),
        unit="V",
        transform=[scale(0.1)],
        description=(
            "DC2 voltage setpoint (PROVEN x0.1V from caller reference evidence) "
            "(reference: lines 2089-2123)"
        ),
        required=False,
        default=0.0,
    )
    volt_set_dc3: float = block_field(
        offset=10,
        type=UInt16(),
        unit="V",
        transform=[scale(0.1)],
        description=(
            "DC3 voltage setpoint (PROVEN x0.1V from caller reference evidence) "
            "(reference: lines 2167-2201)"
        ),
        required=False,
        default=0.0,
    )
    output_current_dc3: float = block_field(
        offset=12,
        type=UInt16(),
        unit="A",
        transform=[scale(0.1)],
        description=(
            "DC3 output current limit (PROVEN x0.1A from caller reference evidence) "
            "(reference: lines 2204-2238)"
        ),
        required=False,
        default=0.0,
    )
    # TODO: Add outputCurrentDC2 (offset 8-9, scale UNKNOWN - evidence gap)
    # TODO: Add voltSet2DC3 (offset 22-23, reference: lines 2240-2277)
    # TODO: Add setEvent1 list field (offset TBD, reference: line 2328)
    # TODO: Add chgModeDC1/2/3/4 (offsets TBD, reference: lines 2370-2391)
    # TODO: Add battery settings (capacity, type, modelType - lines 2424-2460)
    # TODO: Add powerDC1-5 (offsets TBD, reference: lines 2489-2605)
    # TODO: Add dcTotalPowerSet (offset TBD, reference: line 2634)
    # TODO: Add feature flags (genCheckEnable, genType, etc. - lines 2684-2748)
    # TODO: Add additional mode settings (reverseChgMode, sysPowerCtrl, etc.)
    # TODO: Add recharger power settings (rechargerPowerDC1-5 - lines 2854-3010)
    # TODO: Add advanced settings (voltSetMode, pscModelNumber, etc. - lines 3051-3176)


# Export schema instance
BLOCK_15600_SCHEMA = DCDCSettingsBlock.to_schema()  # type: ignore[attr-defined]
