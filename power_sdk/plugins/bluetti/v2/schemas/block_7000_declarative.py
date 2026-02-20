"""Block 7000 (PACK_SETTINGS) - Battery Pack Configuration.

Source: docs/blocks/ADDITIONAL_BLOCKS.md (lines 164-177)
Method: parsePackSettingsInfo
Bean: PackSettingsInfo

Purpose: Battery pack configuration settings.
"""

from dataclasses import dataclass

from ..protocol.datatypes import UInt8, UInt16
from .declarative import block_field, block_schema


@block_schema(
    block_id=7000,
    name="PACK_SETTINGS",
    description="Battery pack configuration settings",
    min_length=12,
    protocol_version=2000,
    strict=False,
    verification_status="verified_reference",
)
@dataclass
class PackSettingsBlock:
    """Battery pack configuration schema."""

    pack_id: int = block_field(
        offset=0,
        type=UInt8(),
        description="Battery pack ID",
        required=True,
        default=0,
    )

    pack_parallel_number: int = block_field(
        offset=1,
        type=UInt16(),
        description="Number of packs in parallel",
        required=True,
        default=0,
    )

    start_heating_enable: int = block_field(
        offset=3,
        type=UInt8(),
        description="Battery heating enable",
        required=False,
        default=0,
    )

    # TODO(verify): Gap between offset 3 and 11
    bms_comm_interface_type: int = block_field(
        offset=11,
        type=UInt8(),
        description="BMS communication interface type",
        required=False,
        default=0,
    )


BLOCK_7000_SCHEMA = PackSettingsBlock.to_schema()  # type: ignore[attr-defined]


