"""Block 720 (OTA_STATUS) - Firmware Update Status.

Source: docs/blocks/ADDITIONAL_BLOCKS.md (line 320)
Method: parseOTAStatus
Purpose: Monitor firmware update progress

TODO(smali-verify): No detailed field mapping available in APK documentation.
Need to reverse engineer parseOTAStatus method for complete field structure.
"""

from dataclasses import dataclass

from ..protocol.v2.datatypes import UInt8
from .declarative import block_field, block_schema


@block_schema(
    block_id=720,
    name="OTA_STATUS",
    description="Firmware update status",
    min_length=2,
    protocol_version=2000,
    strict=False,
)
@dataclass
class OtaStatusBlock:
    """OTA firmware update status schema (minimal)."""

    # TODO(smali-verify): Extract detailed fields from parseOTAStatus method
    ota_status: int = block_field(
        offset=0,
        type=UInt8(),
        description="OTA update status code",
        required=False,
        default=0,
    )

    ota_progress: int = block_field(
        offset=1,
        type=UInt8(),
        description="OTA update progress percentage",
        required=False,
        default=0,
    )


BLOCK_720_SCHEMA = OtaStatusBlock.to_schema()  # type: ignore[attr-defined]
