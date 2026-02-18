"""Block 11000 (IOT_INFO) - IOT Module Base Information.

Source: docs/blocks/ADDITIONAL_BLOCKS.md (lines 180-200)
Method: parseIOTInfo
Bean: DeviceIotInfo

Purpose: IOT module identification and version information.
"""

from dataclasses import dataclass

from power_sdk.protocol.v2.datatypes import String, UInt16, UInt32
from .declarative import block_field, block_schema


@block_schema(
    block_id=11000,
    name="IOT_INFO",
    description="IOT module identification and version information",
    min_length=38,
    protocol_version=2000,
    strict=False,
    verification_status="smali_verified",
)
@dataclass
class IotInfoBlock:
    """IOT module base information schema."""

    iot_model: str = block_field(
        offset=0,
        type=String(length=12),
        description="IOT model string (ASCII, 12 bytes)",
        required=True,
        default="",
    )

    iot_sn: str = block_field(
        offset=12,
        type=String(length=8),
        description="IOT serial number (8 bytes)",
        required=True,
        default="",
    )

    safety_code: str = block_field(
        offset=20,
        type=String(length=8),
        description="Safety code (8-byte number as string)",
        required=False,
        default="",
    )

    iot_software_ver: int = block_field(
        offset=28,
        type=UInt32(),
        description="IOT firmware version (32-bit)",
        required=True,
        default=0,
    )

    rf_ver: int = block_field(
        offset=32,
        type=UInt32(),
        description="RF module version (32-bit)",
        required=False,
        default=0,
    )

    ctrl_status: int = block_field(
        offset=36,
        type=UInt16(),
        description="IOT control status (bitfield)",
        required=False,
        default=0,
    )


BLOCK_11000_SCHEMA = IotInfoBlock.to_schema()  # type: ignore[attr-defined]
