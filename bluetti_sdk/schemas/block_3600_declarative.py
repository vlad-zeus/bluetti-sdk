"""Block 3600 (CURR_YEAR_ENERGY) - Current Year Energy Statistics.

Source: docs/blocks/ADDITIONAL_BLOCKS.md (line 344)
Method: parseCurrYearEnergy
Purpose: Year-to-date energy statistics

TODO(smali-verify): No detailed field mapping available in APK documentation.
Need to reverse engineer parseCurrYearEnergy method for complete field structure.
Similar structure to Block 3500 but for current year instead of lifetime.
"""

from dataclasses import dataclass

from ..protocol.v2.datatypes import UInt32
from ..protocol.v2.transforms import scale
from .declarative import block_field, block_schema


@block_schema(
    block_id=3600,
    name="CURR_YEAR_ENERGY",
    description="Current year energy statistics (year-to-date)",
    min_length=16,
    protocol_version=2000,
    strict=False,
)
@dataclass
class CurrYearEnergyBlock:
    """Current year energy statistics schema (minimal)."""

    # TODO(smali-verify): Extract detailed fields from parseCurrYearEnergy method
    # Similar to Block 3500 but for current year period
    year_pv_energy: float = block_field(
        offset=0,
        type=UInt32(),
        transform=[scale(0.1)],
        description="PV generation energy (current year)",
        unit="kWh",
        required=False,
        default=0.0,
    )

    year_charge_energy: float = block_field(
        offset=4,
        type=UInt32(),
        transform=[scale(0.1)],
        description="Battery charge energy (current year)",
        unit="kWh",
        required=False,
        default=0.0,
    )

    year_discharge_energy: float = block_field(
        offset=8,
        type=UInt32(),
        transform=[scale(0.1)],
        description="Battery discharge energy (current year)",
        unit="kWh",
        required=False,
        default=0.0,
    )

    year_grid_energy: float = block_field(
        offset=12,
        type=UInt32(),
        transform=[scale(0.1)],
        description="Grid import/export energy (current year)",
        unit="kWh",
        required=False,
        default=0.0,
    )


BLOCK_3600_SCHEMA = CurrYearEnergyBlock.to_schema()  # type: ignore[attr-defined]
