"""Block 1700 (METER_INFO) - CT Meter Information.

Source: docs/blocks/ADDITIONAL_BLOCKS.md (line 326)
Method: parseInvMeterInfo
Purpose: Monitor grid import/export via CT clamps

TODO(smali-verify): No detailed field mapping available in APK documentation.
Need to reverse engineer parseInvMeterInfo method for complete field structure.
"""

from dataclasses import dataclass

from ..protocol.v2.datatypes import Int16
from .declarative import block_field, block_schema


@block_schema(
    block_id=1700,
    name="METER_INFO",
    description="CT meter readings for grid monitoring",
    min_length=4,
    protocol_version=2000,
    strict=False,
)
@dataclass
class MeterInfoBlock:
    """CT meter information schema (minimal)."""

    # TODO(smali-verify): Extract detailed fields from parseInvMeterInfo method
    # Typical meter fields include: grid_power, grid_current, grid_voltage, etc.
    meter_power: int = block_field(
        offset=0,
        type=Int16(),
        description="CT meter power reading (negative=export, positive=import)",
        unit="W",
        required=False,
        default=0,
    )

    meter_current: int = block_field(
        offset=2,
        type=Int16(),
        description="CT meter current reading",
        unit="A",
        required=False,
        default=0,
    )


BLOCK_1700_SCHEMA = MeterInfoBlock.to_schema()  # type: ignore[attr-defined]
