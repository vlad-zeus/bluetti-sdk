"""Block 17100 (AT1_BASE_INFO) - AT1 Transfer Switch Base Information.

Source: ProtocolParserV2.reference switch case (0x42cc -> sswitch_b)
Parser: AT1Parser.at1InfoParse (lines 1313-1931)
Bean: AT1BaseInfo.reference
Block Type: parser-backed
Purpose: AT1 transfer switch device identification (baseline)

Structure:
- Min length: 26 bytes (covers offsets 0-25, basic device info)
- Core fields (offsets 0-25): VERIFIED from reference (3 fields proven)
- Extended fields (26+): Nested AT1PhaseInfoItem structures (6 output phase groups)
- Related to AT1_SETTINGS block 17400 and AT1 timer blocks 19365-19485

reference Evidence (All Current Fields Verified):
- Model: offset 0-11, getASCIIStr (lines 1376-1390)
- Serial: offset 12-19, getDeviceSN (lines 1395-1405)
- Software Version: offset 22-25, bit32RegByteToNumber (lines 1410-1428)

Parser Structure (lines 1313-1931):
- Basic device info (0-25): Model, SN, Software Ver ✅
- Bytes 26-71: MYSTERY - Not parsed in at1InfoParse (possibly reserved)
- Bytes 72+: Complex nested structures:
  * 6 output phase groups (Grid, Backup, SmartLoad1-4)
  * Each phase: AT1PhaseInfoItem (7 fields: voltage, current, power, phase_no)
  * Alarm/fault lists: AlarmFaultInfo arrays
  * Total: ~140 fields across 3-4 nesting levels

Note: Previous schema claimed 9 fields, but only 3 have reference evidence. Fields like
grid_voltage, grid_frequency, transfer_status have NO setter calls in parser. These
are likely part of nested AT1PhaseInfoItem structures at offset 72+.

Baseline implementation: 3 verified fields only. Nested structure extraction deferred.
"""

from dataclasses import dataclass

from ..protocol.datatypes import String, UInt32
from .declarative import block_field, block_schema


@block_schema(
    block_id=17100,
    name="AT1_BASE_INFO",
    description="AT1 transfer switch base information (baseline - PARSED block)",
    min_length=26,
    strict=False,
    verification_status="verified_reference",
)
@dataclass
class AT1BaseInfoBlock:
    """AT1 base information schema (reference-verified baseline).

    All 3 fields verified from AT1Parser.at1InfoParse reference bytecode.
    This represents the minimum proven structure (26 bytes). Additional
    fields exist in parser but use nested AT1PhaseInfoItem arrays (deferred).
    """

    model: str = block_field(
        offset=0,
        type=String(length=12),
        description="AT1 device model name (ASCII) (reference: lines 1376-1390)",
        required=False,
        default="",
    )
    serial_number: str = block_field(
        offset=12,
        type=String(length=8),
        description="AT1 device serial number (reference: lines 1395-1405)",
        required=False,
        default="",
    )
    software_version: int = block_field(
        offset=22,
        type=UInt32(),
        description=(
            "Software/firmware version number "
            "[transform: bit32RegByteToNumber] (reference: lines 1410-1428)"
        ),
        required=False,
        default=0,
    )
    # NOTE: Additional fields exist in AT1BaseInfo bean but not included in baseline:
    # - Bytes 26-71: Not parsed in at1InfoParse (mystery/reserved)
    # - Bytes 72+: Complex nested AT1PhaseInfoItem structures:
    #   * outputSL1, outputSL2, outputSL3, outputSL4 (offset 72, 96, 120, 144)
    #   * Each: List<AT1PhaseInfoItem> (voltage, current, power per phase)
    #   * acFreq (offset 168-169)
    #   * errorList, warnList, protectList, warnsOfPhase (offset 170-208+)
    # These require nested dataclass support and separate verification.


# Export schema instance
BLOCK_17100_SCHEMA = AT1BaseInfoBlock.to_schema()  # type: ignore[attr-defined]
