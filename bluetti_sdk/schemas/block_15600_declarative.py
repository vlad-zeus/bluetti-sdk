"""Block 15600 (DC_DC_SETTINGS) - DC-DC Converter Configuration Settings.

Source: ProtocolParserV2.smali switch case (0x3cf0 -> sswitch_12)
Parser: DCDCParser.settingsInfoParse (lines 1780-3176+)
Bean: DCDCSettings.smali (40+ fields)
Block Type: parser-backed
Related: ProtocolAddrV2.smali defines multiple DCDC_* settings registers
Purpose: DC-DC converter voltage/current setpoints and operation mode control

Structure:
- Min length from smali: 36-56 bytes (protocol version dependent)
  - v >= 0x7e2: 56 bytes (0x38)
  - v >= 0x7e1: 36 bytes (0x24)
- Core fields (offsets 0-13): Control flags, voltage/current setpoints
- Extended fields (40+ total): Battery settings, power limits, charging modes, features

Smali Evidence:
- Control bit-field: hexStrToEnableList (lines 1909-1999)
- Voltage/current setpoints: parseInt(16) RAW - NO division (lines 2002-2238)
- Conditional parsing: Size-dependent field presence (multiple if-blocks)

CRITICAL ELECTRICAL SAFETY WARNING:
- This block controls DC-DC converter output voltage and current limits
- Scale factors for voltage/current setpoints are UNKNOWN (raw hex values)
- Incorrect setpoints can damage equipment or create fire/electrical hazards
- DO NOT implement write operations without actual device validation
- All control fields should be treated as READ-ONLY until scale factors verified

Scale Factor Status:
- Control flags (offset 0): Verified (bit-field enable/disable)
- Voltage setpoints (offsets 2-3, 6-7, 10-11): UNKNOWN SCALE - raw hex
- Current setpoints (offsets 4-5, 8-9, 12-13): UNKNOWN SCALE - raw hex
- Block 15500 uses x0.1 for readings, but 15600 may use different scale for setpoints

TODO(smali-verify): MANDATORY for safety - Requires:
- Actual device testing to determine voltage/current/power scale factors
- Safe operating range validation for each control field
- Battery type/capacity encoding documentation
- Complete offset mapping for all 40+ fields
- Protocol version conditional logic documentation
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
