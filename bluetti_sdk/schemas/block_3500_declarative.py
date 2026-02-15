"""Block 3500 (TOTAL_ENERGY_INFO) - Total Energy Statistics.

Source: ProtocolParserV2.smali lines 32107-32300 (parseTotalEnergyInfo)
Bean: InvEnergyStatistics
Purpose: Lifetime energy totals with yearly breakdown

Smali-verified structure:
- Offset 1: Energy type (1 byte)
- Offset 2-5: Total energy (UInt32, scale 0.1 kWh)
- Offset 6+: List of 15 yearly energies (6 bytes each):
  - Bytes +0,+1: Year (UInt16)
  - Bytes +2 to +5: Energy value (UInt32, scale 0.1 kWh)

Note: This schema provides total energy and year fields for first 3 entries.
Full array parsing of 15 years requires dynamic structure support.
"""

from dataclasses import dataclass

from ..protocol.v2.datatypes import UInt8, UInt16, UInt32
from ..protocol.v2.transforms import scale
from .declarative import block_field, block_schema


@block_schema(
    block_id=3500,
    name="TOTAL_ENERGY_INFO",
    description="Lifetime energy statistics with yearly breakdown",
    min_length=96,
    protocol_version=2000,
    strict=False,
)
@dataclass
class TotalEnergyInfoBlock:
    """Total energy statistics schema (smali-verified)."""

    energy_type: int = block_field(
        offset=1,
        type=UInt8(),
        description="Energy type identifier",
        required=True,
        default=0,
    )

    total_energy: float = block_field(
        offset=2,
        type=UInt32(),
        transform=[scale(0.1)],
        description="Total lifetime energy",
        unit="kWh",
        required=True,
        default=0.0,
    )

    # Year energy array (15 entries, showing first 3)
    year0_year: int = block_field(
        offset=6,
        type=UInt16(),
        description="Year 0: Year value",
        required=False,
        default=0,
    )

    year0_energy: float = block_field(
        offset=8,
        type=UInt32(),
        transform=[scale(0.1)],
        description="Year 0: Energy value",
        unit="kWh",
        required=False,
        default=0.0,
    )

    year1_year: int = block_field(
        offset=12,
        type=UInt16(),
        description="Year 1: Year value",
        required=False,
        default=0,
    )

    year1_energy: float = block_field(
        offset=14,
        type=UInt32(),
        transform=[scale(0.1)],
        description="Year 1: Energy value",
        unit="kWh",
        required=False,
        default=0.0,
    )

    year2_year: int = block_field(
        offset=18,
        type=UInt16(),
        description="Year 2: Year value",
        required=False,
        default=0,
    )

    year2_energy: float = block_field(
        offset=20,
        type=UInt32(),
        transform=[scale(0.1)],
        description="Year 2: Energy value",
        unit="kWh",
        required=False,
        default=0.0,
    )

    # Note: Years 3-14 follow same pattern at offsets 24, 30, 36, ...


BLOCK_3500_SCHEMA = TotalEnergyInfoBlock.to_schema()  # type: ignore[attr-defined]
