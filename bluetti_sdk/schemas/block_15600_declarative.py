"""Block 15600 (DC_DC_SETTINGS) - DC-DC Converter Configuration Settings.

Source: ProtocolParserV2.smali switch case (0x3cf0 -> sswitch_12)
Related: ProtocolAddrV2.smali defines multiple DCDC_* settings registers
Block Type: parser-backed (DCDCParser.settingsInfoParse)
Purpose: DC-DC converter voltage/current limits and operation mode settings

Structure (PROVISIONAL):
- Min length from smali: 36-56 bytes (protocol version dependent)
  - v >= 0x7e2: 56 bytes (0x38)
  - v >= 0x7e1: 36 bytes (0x24)
- Likely contains: voltage set points, current limits, mode control

Security: CRITICAL - Controls DC-DC converter output parameters. Incorrect
voltage or current settings may damage connected equipment or create
electrical hazards. Only modify with proper understanding of system limits
and load requirements.

TODO(smali-verify): Complete field mapping requires:
- Reverse engineering of DCDCSettings bean structure
- Analysis of related DCDC_* control registers (0x3cf0-0x3d12)
- Actual device testing to verify voltage/current ranges
"""

from dataclasses import dataclass

from ..protocol.v2.datatypes import UInt8, UInt16
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

    enable_flags: int = block_field(
        offset=0,
        type=UInt16(),
        description="DC-DC enable/mode control flags (TODO: verify bit mapping)",
        required=False,
        default=0,
    )
    output_voltage_set: int = block_field(
        offset=2,
        type=UInt16(),
        unit="V",
        description="Output voltage setpoint (TODO: verify offset and scale)",
        required=False,
        default=0,
    )
    output_current_limit: int = block_field(
        offset=4,
        type=UInt16(),
        unit="A",
        description="Output current limit (TODO: verify offset and scale)",
        required=False,
        default=0,
    )
    dc_mode: int = block_field(
        offset=6,
        type=UInt8(),
        description="DC-DC operation mode (TODO: verify enum values)",
        required=False,
        default=0,
    )


# Export schema instance
BLOCK_15600_SCHEMA = DCDCSettingsBlock.to_schema()  # type: ignore[attr-defined]
