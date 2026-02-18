"""Block 6300 (PACK_BMU_READ) - Battery Management Unit Information.

Source: ProtocolParserV2.smali lines 28435-28850 (parsePackBMUInfo)
Bean: PackBMUInfo (contains List<PackBMUItem>)
Purpose: BMU-level battery pack structure and identification

Smali-verified offset formulas (bmu_cnt parameter required):
For each BMU index i (0 to bmu_cnt-1):
- Serial Number: offset = i * 8, length = 8 bytes
- Fault data: offset = bmu_cnt * 8 + i * 4, length = 4 bytes
- NTC count: offset = bmu_cnt * 12 + i * 2 (1 byte)
- Cell count: offset = bmu_cnt * 12 + i * 2 + 1 (1 byte)
- Model type: offset = bmu_cnt * 14 + adjusted_i (1 byte)
  where adjusted_i = (i % 2 == 0) ? i + 1 : i - 1
- Software version (if protocol >= 0x7DA/2010):
  offset = bmu_cnt * 14 + 2 * ((bmu_cnt+1) // 2) + i * 4, length = 4 bytes

Model type values: 1=B700, 2=B300K, 3=B300S, 4=B300, other=""

Implementation note:
Full multi-BMU parsing requires dynamic offset calculation based on bmu_cnt.
This schema provides fields for single BMU baseline (bmu_cnt=1).
For multi-BMU systems, use higher-level parser that iterates based on bmu_cnt.
"""

from dataclasses import dataclass

from power_sdk.protocol.v2.datatypes import String, UInt8, UInt32
from .declarative import block_field, block_schema


@block_schema(
    block_id=6300,
    name="PACK_BMU_READ",
    description="Battery Management Unit structure (smali-verified, single BMU)",
    min_length=25,
    protocol_version=2000,
    strict=False,
    verification_status="smali_verified",
)
@dataclass
class PackBmuReadBlock:
    """BMU information schema (smali-verified for single BMU)."""

    # === BMU 0 Base Information (bmu_cnt=1) ===
    bmu0_serial_number: str = block_field(
        offset=0,
        type=String(length=8),
        description="BMU 0 device serial number (8 bytes ASCII)",
        required=True,
        default="",
    )

    # Fault data offset: bmu_cnt * 8 + bmu_index * 4
    # For single BMU (bmu_cnt=1, index=0): offset = 1*8 + 0*4 = 8
    bmu0_fault_data: int = block_field(
        offset=8,
        type=UInt32(),
        description=(
            "BMU 0 fault/warning bitfield "
            "(mode 1, BmuWarnNames, prefix P, code 0x71)"
        ),
        required=True,
        default=0,
    )

    # NTC and Cell counts: bmu_cnt * 12 + bmu_index * 2
    # For single BMU: offset = 1*12 + 0*2 = 12
    bmu0_ntc_count: int = block_field(
        offset=12,
        type=UInt8(),
        description="BMU 0 NTC temperature sensor count",
        required=True,
        default=0,
    )

    bmu0_cell_count: int = block_field(
        offset=13,
        type=UInt8(),
        description="BMU 0 cell count",
        required=True,
        default=0,
    )

    # Model type: bmu_cnt * 14 + adjusted_index
    # For single BMU (index=0, even): adjusted = 0 + 1 = 1
    # offset = 1*14 + 1 = 15
    bmu0_model_type: int = block_field(
        offset=15,
        type=UInt8(),
        description="BMU 0 model type (1=B700, 2=B300K, 3=B300S, 4=B300)",
        required=True,
        default=0,
    )

    # Software version (if protocol >= 0x7DA/2010)
    # offset = bmu_cnt * 14 + 2 * ((bmu_cnt+1)//2) + bmu_index * 4
    # For single BMU: offset = 1*14 + 2*((1+1)//2) + 0*4 = 14 + 2*1 = 16
    bmu0_software_version: int = block_field(
        offset=16,
        type=UInt32(),
        description="BMU 0 firmware version (if protocol >= 2010)",
        required=False,
        default=0,
        min_protocol_version=2010,
    )

    # === Multi-BMU Support ===
    # Note: For bmu_cnt > 1, BMU indices 1, 2, ... follow dynamic formulas.
    # Example for BMU 1 (if bmu_cnt=2):
    # - Serial: offset 8
    # - Fault: offset 2*8 + 1*4 = 20
    # - NTC/Cell: offset 2*12 + 1*2 = 26, 27
    # - Model: offset 2*14 + 0 = 28 (odd index, adjusted = 1-1 = 0)
    # - Software: offset 2*14 + 2*((2+1)//2) + 1*4 = 28 + 4 + 4 = 36
    #
    # Full implementation requires iteration based on actual bmu_cnt value
    # from Block 6100 offset 109 or passed as parameter.


BLOCK_6300_SCHEMA = PackBmuReadBlock.to_schema()  # type: ignore[attr-defined]
