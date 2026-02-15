"""Block 3500 (TOTAL_ENERGY_INFO) - Total Energy Statistics.

Source: docs/blocks/ADDITIONAL_BLOCKS.md (line 338)
Method: parseTotalEnergyInfo
Purpose: Lifetime energy totals (cumulative)

TODO(smali-verify): No detailed field mapping available in APK documentation.
Need to reverse engineer parseTotalEnergyInfo method for complete field structure.
Based on Block 100 energy fields, likely contains UInt32 fields with scale(0.1).
"""

from dataclasses import dataclass

from ..protocol.v2.datatypes import UInt32
from ..protocol.v2.transforms import scale
from .declarative import block_field, block_schema


@block_schema(
    block_id=3500,
    name="TOTAL_ENERGY_INFO",
    description="Lifetime energy statistics (cumulative totals)",
    min_length=16,
    protocol_version=2000,
    strict=False,
)
@dataclass
class TotalEnergyInfoBlock:
    """Total energy statistics schema (minimal)."""

    # TODO(smali-verify): Extract detailed fields from parseTotalEnergyInfo method
    # Following pattern from Block 100 energy fields (offset 108-116)
    total_pv_energy: float = block_field(
        offset=0,
        type=UInt32(),
        transform=[scale(0.1)],
        description="Total PV generation energy (lifetime)",
        unit="kWh",
        required=False,
        default=0.0,
    )

    total_charge_energy: float = block_field(
        offset=4,
        type=UInt32(),
        transform=[scale(0.1)],
        description="Total battery charge energy (lifetime)",
        unit="kWh",
        required=False,
        default=0.0,
    )

    total_discharge_energy: float = block_field(
        offset=8,
        type=UInt32(),
        transform=[scale(0.1)],
        description="Total battery discharge energy (lifetime)",
        unit="kWh",
        required=False,
        default=0.0,
    )

    total_grid_energy: float = block_field(
        offset=12,
        type=UInt32(),
        transform=[scale(0.1)],
        description="Total grid import/export energy (lifetime)",
        unit="kWh",
        required=False,
        default=0.0,
    )


BLOCK_3500_SCHEMA = TotalEnergyInfoBlock.to_schema()  # type: ignore[attr-defined]
