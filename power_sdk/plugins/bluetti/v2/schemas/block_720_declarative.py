"""Block 720 (OTA_STATUS) - Firmware Update Status.

Source: ProtocolParserV2.reference lines 28228-28430 (parseOTAStatus)
Bean: OTAStatus
Purpose: Monitor firmware update progress for multiple MCU types

reference-verified structure:
- Offset 0: OTA group ID (1 byte)
- Offset 2+: Array of 16 OTA file statuses (6 bytes each):
  - Offset +0: OTA status code
  - Offset +1: OTA file step
  - Offset +2: MCU type
  - Offset +3: Depth level
  - Offset +4: Progress percentage (0-100)
  - Offset +5: Error code

Note: This schema provides the first file status. Full array parsing
requires dynamic structure support or higher-level parsing.
"""

from dataclasses import dataclass

from ..protocol.datatypes import UInt8
from .declarative import block_field, block_schema


@block_schema(
    block_id=720,
    name="OTA_STATUS",
    description="Firmware update status with file progress tracking",
    min_length=8,
    protocol_version=2000,
    strict=False,
    verification_status="smali_verified",
)
@dataclass
class OtaStatusBlock:
    """OTA firmware update status schema (reference-verified)."""

    ota_group: int = block_field(
        offset=0,
        type=UInt8(),
        description="OTA group identifier",
        required=True,
        default=0,
    )

    # First file status (offset 2-7)
    file0_ota_status: int = block_field(
        offset=2,
        type=UInt8(),
        description="File 0: OTA status code",
        required=True,
        default=0,
    )

    file0_ota_step: int = block_field(
        offset=3,
        type=UInt8(),
        description="File 0: OTA file step",
        required=True,
        default=0,
    )

    file0_mcu_type: int = block_field(
        offset=4,
        type=UInt8(),
        description="File 0: MCU type identifier",
        required=True,
        default=0,
    )

    file0_depth: int = block_field(
        offset=5,
        type=UInt8(),
        description="File 0: Update depth level",
        required=True,
        default=0,
    )

    file0_progress: int = block_field(
        offset=6,
        type=UInt8(),
        description="File 0: Progress percentage (0-100)",
        required=True,
        default=0,
    )

    file0_error_code: int = block_field(
        offset=7,
        type=UInt8(),
        description="File 0: Error code (0=no error)",
        required=True,
        default=0,
    )

    # Note: Files 1-15 follow the same pattern at offsets 8, 14, 20, ...
    # Full array parsing requires dynamic structure support


BLOCK_720_SCHEMA = OtaStatusBlock.to_schema()  # type: ignore[attr-defined]

