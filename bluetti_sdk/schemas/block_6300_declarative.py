"""Block 6300 (PACK_BMU_READ) - Battery Management Unit Information.

Source: docs/blocks/BLOCK_6300_PACK_BMU_READ.md
Method: parsePackBMUInfo / parsePackSubPackInfo
Bean: PackBMUInfo (contains List<PackBMUItem> and fault info)
Purpose: BMU-level battery pack structure and identification

This block provides BMU (Battery Management Unit) information for multi-battery systems.
Each BMU manages a subset of cells and temperature sensors.

Data Structure:
- Serial numbers for each BMU (8 bytes per BMU)
- Fault/warning data (4 bytes per BMU)
- Cell and NTC counts per BMU
- Model type identification (B700, B300K, B300S, B300)
- Software version (if protocol >= 2010)

Integration:
- Block 6000 (PACK_MAIN_INFO): Provides BMU count
- Block 6100 (PACK_ITEM_INFO): Uses BMU cell/NTC indices for detailed data
- Block 6300 (PACK_BMU_READ): Provides BMU structure information

Format Notes:
- Read length: 25 bytes (0x19)
- Variable size based on bmu_cnt (typically obtained from Block 6100 offset 109)
- Cell and NTC indices are cumulative across BMUs
- Model type uses alternating index logic (even/odd BMU indices)

TODO(smali-verify): Complete BMU parsing requires dynamic length based on bmu_cnt.
This minimal schema provides basic structure without full array parsing.
"""

from dataclasses import dataclass

from ..protocol.v2.datatypes import String, UInt8, UInt32
from .declarative import block_field, block_schema


@block_schema(
    block_id=6300,
    name="PACK_BMU_READ",
    description="Battery Management Unit structure and identification",
    min_length=25,
    protocol_version=2000,
    strict=False,
)
@dataclass
class PackBmuReadBlock:
    """BMU information schema (minimal for single BMU)."""

    # === BMU 0 Base Information ===
    bmu0_serial_number: str = block_field(
        offset=0,
        type=String(length=8),
        description="BMU 0 device serial number (8 bytes ASCII)",
        required=False,
        default="",
    )

    # TODO(smali-verify): Full implementation requires parsing based on bmu_cnt
    # Fault data offset: bmuCnt * 8 + bmuIndex * 4
    # For single BMU (bmuCnt=1): offset = 1*8 + 0*4 = 8
    bmu0_fault_data: int = block_field(
        offset=8,
        type=UInt32(),
        description=(
            "BMU 0 fault/warning bitfield "
            "(mode 1, BmuWarnNames, prefix P, code 0x71)"
        ),
        required=False,
        default=0,
    )

    # Cell and NTC counts
    # For single BMU (bmuCnt=1): offset = 1*12 + 0*2 = 12
    bmu0_ntc_count: int = block_field(
        offset=12,
        type=UInt8(),
        description="BMU 0 NTC temperature sensor count",
        required=False,
        default=0,
    )

    bmu0_cell_count: int = block_field(
        offset=13,
        type=UInt8(),
        description="BMU 0 cell count",
        required=False,
        default=0,
    )

    # Model type
    # For single BMU (bmuCnt=1): offset = 1*14 + 1 = 15 (odd index)
    bmu0_model_type: int = block_field(
        offset=15,
        type=UInt8(),
        description="BMU 0 model type (1=B700, 2=B300K, 3=B300S, 4=B300)",
        required=False,
        default=0,
    )

    # Software version (if protocol >= 2010)
    # TODO(smali-verify): Offset calculation depends on bmu_cnt and protocol version
    bmu0_software_version: int = block_field(
        offset=16,
        type=UInt32(),
        description="BMU 0 firmware version (if protocol >= 2010)",
        required=False,
        default=0,
        min_protocol_version=2010,
    )

    # NOTE:
    # Multi-BMU entries are intentionally excluded from this schema because
    # offsets overlap with single-BMU fields and require dynamic parsing based
    # on bmu_cnt. See TODO(smali-verify) above.


BLOCK_6300_SCHEMA = PackBmuReadBlock.to_schema()  # type: ignore[attr-defined]
