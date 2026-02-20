"""Block 17000 (ATS_INFO) - Automatic Transfer Switch Information.

Source: ProtocolParserV2.reference lines 745-877 (atsInfoParse)
Bean: DeviceAtsInfo
Purpose: ATS device identification and software version information

reference-verified structure:
- Offset 0-11: Model name (12 bytes ASCII, using getASCIIStr)
- Offset 12-19: Serial number (8 bytes, using getDeviceSN)
- Offset 21: Software type (1 byte UInt8)
- Offset 22-25: Software version (4 bytes UInt32, using bit32RegByteToNumber)
"""

from dataclasses import dataclass

from ..protocol.datatypes import String, UInt8, UInt32
from .declarative import block_field, block_schema


@block_schema(
    block_id=17000,
    name="ATS_INFO",
    description="Automatic Transfer Switch device information (reference-verified)",
    min_length=26,
    protocol_version=2000,
    strict=False,
    verification_status="verified_reference",
)
@dataclass
class ATSInfoBlock:
    """ATS device information schema (reference-verified)."""

    model: str = block_field(
        offset=0,
        type=String(length=12),
        description="ATS device model name (ASCII)",
        required=True,
        default="",
    )
    serial_number: str = block_field(
        offset=12,
        type=String(length=8),
        description="ATS device serial number",
        required=True,
        default="",
    )
    software_type: int = block_field(
        offset=21,
        type=UInt8(),
        description="Software/firmware type identifier",
        required=True,
        default=0,
    )
    software_version: int = block_field(
        offset=22,
        type=UInt32(),
        description="Software/firmware version number",
        required=True,
        default=0,
    )


# Export schema instance
BLOCK_17000_SCHEMA = ATSInfoBlock.to_schema()  # type: ignore[attr-defined]


