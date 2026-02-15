"""Block 12161 (IOT_ENABLE_INFO) - IOT Module Enable Status.

Source: docs/blocks/ADDITIONAL_BLOCKS.md (line 362)
Method: parseIOTEnableInfo
Bean: IoTCtrlStatus
Purpose: IOT module operational status and control flags

TODO(smali-verify): No detailed field mapping available in APK documentation.
Need to reverse engineer parseIOTEnableInfo method for complete field structure.
Related to Block 11000 (IOT_INFO) ctrl_status field.
"""

from dataclasses import dataclass

from ..protocol.v2.datatypes import UInt8, UInt16
from .declarative import block_field, block_schema


@block_schema(
    block_id=12161,
    name="IOT_ENABLE_INFO",
    description="IOT module enable and control status",
    min_length=4,
    protocol_version=2000,
    strict=False,
)
@dataclass
class IotEnableInfoBlock:
    """IOT enable status schema (minimal)."""

    # TODO(smali-verify): Extract detailed fields from parseIOTEnableInfo method
    # Bean: IoTCtrlStatus (likely contains enable flags for various IOT functions)
    iot_enable: int = block_field(
        offset=0,
        type=UInt8(),
        description="IOT module enable flag",
        required=False,
        default=0,
    )

    iot_mode: int = block_field(
        offset=1,
        type=UInt8(),
        description="IOT operating mode",
        required=False,
        default=0,
    )

    iot_ctrl_status: int = block_field(
        offset=2,
        type=UInt16(),
        description="IOT control status bitfield",
        required=False,
        default=0,
    )


BLOCK_12161_SCHEMA = IotEnableInfoBlock.to_schema()  # type: ignore[attr-defined]
