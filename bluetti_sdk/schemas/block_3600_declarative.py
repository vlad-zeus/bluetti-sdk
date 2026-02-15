"""Block 3600 (CURR_YEAR_ENERGY) - Current Year Energy Statistics.

Source: ProtocolParserV2.smali lines 10784-11000 (parseCurrYearEnergy)
Bean: InvCurrentYearEnergy
Purpose: Year-to-date energy statistics with monthly and daily breakdown

Smali-verified structure:
- Offset 1: Energy type (1 byte)
- Offset 2-3: Year (UInt16)
- Offset 4-7: Total year energy (UInt32, scale 0.1 kWh)
- Offset 8+: 12 monthly energies (4 bytes each, UInt32, scale 0.1 kWh)
- Offset 56 (0x38) to 118 (0x76): 31 daily energies (2 bytes each, UInt16)

Note: This schema provides core fields and first 3 months.
Full monthly/daily arrays require dynamic structure support.
"""

from dataclasses import dataclass

from ..protocol.v2.datatypes import UInt8, UInt16, UInt32
from ..protocol.v2.transforms import scale
from .declarative import block_field, block_schema


@block_schema(
    block_id=3600,
    name="CURR_YEAR_ENERGY",
    description="Current year energy statistics with monthly breakdown",
    min_length=56,
    protocol_version=2000,
    strict=False,
)
@dataclass
class CurrYearEnergyBlock:
    """Current year energy statistics schema (smali-verified)."""

    energy_type: int = block_field(
        offset=1,
        type=UInt8(),
        description="Energy type identifier",
        required=True,
        default=0,
    )

    year: int = block_field(
        offset=2,
        type=UInt16(),
        description="Current year",
        required=True,
        default=0,
    )

    total_year_energy: float = block_field(
        offset=4,
        type=UInt32(),
        transform=[scale(0.1)],
        description="Total year energy (year-to-date)",
        unit="kWh",
        required=True,
        default=0.0,
    )

    # Monthly energy array (12 entries, showing first 3)
    month0_energy: float = block_field(
        offset=8,
        type=UInt32(),
        transform=[scale(0.1)],
        description="Month 0 (January) energy",
        unit="kWh",
        required=False,
        default=0.0,
    )

    month1_energy: float = block_field(
        offset=12,
        type=UInt32(),
        transform=[scale(0.1)],
        description="Month 1 (February) energy",
        unit="kWh",
        required=False,
        default=0.0,
    )

    month2_energy: float = block_field(
        offset=16,
        type=UInt32(),
        transform=[scale(0.1)],
        description="Month 2 (March) energy",
        unit="kWh",
        required=False,
        default=0.0,
    )

    # Note: Months 3-11 follow same pattern at offsets 20, 24, 28, ...

    # Daily energy array starts at offset 56 (31 days * 2 bytes each, UInt16)
    # Full daily parsing requires dynamic structure support


BLOCK_3600_SCHEMA = CurrYearEnergyBlock.to_schema()  # type: ignore[attr-defined]
