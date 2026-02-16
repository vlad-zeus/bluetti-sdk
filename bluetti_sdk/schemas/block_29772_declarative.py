"""Block 29772 (BOOT_SOFTWARE_INFO) - Boot Software Component Information.

Source: ProtocolParserV2.smali (bootSoftwareInfoParse method)
Bean: List<Lnet/poweroak/bluetticloud/ui/connectv2/bean/BootSoftwareItem>
Block Type: PARSED (dedicated parse method exists)
Purpose: Boot loader software component inventory and version information

Structure (smali-verified):
- Parse method: bootSoftwareInfoParse()
- Returns List<BootSoftwareItem>
- Each item processes 10 bytes:
  * Bytes 0-1: Component address (combined as hex)
  * Bytes 2-5: Component value (processed via bit32RegByteToNumber)
  * Bytes 6-9: Reserved/unknown for baseline schema
  * Creates item with (long_value, int_address)
- Variable length block (processes in 10-byte chunks)

CAUTION: This block contains boot software component information.
DO NOT use for write control without:
- Proper device validation and authorization
- Understanding of boot component structure
- Manufacturer documentation for software updates
Incorrect boot software operations may brick the device or void warranty.

VERIFICATION STATUS: Partial
- Parse method: bootSoftwareInfoParse confirmed at ProtocolParserV2.smali:1088
- Bean: List<BootSoftwareItem> confirmed
- Structure: 10-byte items (2-byte address + 6-byte value data) confirmed
- Baseline: First component item verified
- DEFERRED: Multi-item array parsing, full field semantics, bean constructor
  analysis
- Full smali_verified upgrade pending comprehensive RE session with dynamic
  array support
"""

from dataclasses import dataclass

from ..protocol.v2.datatypes import UInt8, UInt16, UInt32
from .declarative import block_field, block_schema


@block_schema(
    block_id=29772,
    name="BOOT_SOFTWARE_INFO",
    description=(
        "Boot software component info (parse method confirmed, baseline verified)"
    ),
    min_length=10,
    protocol_version=2000,
    strict=False,
    verification_status="partial",
)
@dataclass
class BootSoftwareInfoBlock:
    """Boot software info schema (smali-verified, first item baseline).

    This block has dedicated bootSoftwareInfoParse method.
    Returns list of 10-byte items (component address + value data).

    CAUTION: Boot software control - requires manufacturer authorization.
    """

    # First component item (10 bytes baseline)
    component_address: int = block_field(
        offset=0,
        type=UInt16(),
        description=(
            "First component address from bytes 0-1 (hex parsed integer)"
        ),
        required=False,
        default=0,
    )

    component_value_raw: int = block_field(
        offset=2,
        type=UInt32(),
        description=(
            "Component value built from bytes 2-5 via bit32RegByteToNumber"
        ),
        required=False,
        default=0,
    )

    reserved_byte_0: int = block_field(
        offset=6,
        type=UInt8(),
        description="Reserved/unknown byte 0 (item bytes 6-9 baseline area)",
        required=False,
        default=0,
    )

    reserved_byte_1: int = block_field(
        offset=7,
        type=UInt8(),
        description="Reserved/unknown byte 1 (item bytes 6-9 baseline area)",
        required=False,
        default=0,
    )

    reserved_byte_2: int = block_field(
        offset=8,
        type=UInt8(),
        description="Reserved/unknown byte 2 (item bytes 6-9 baseline area)",
        required=False,
        default=0,
    )

    reserved_byte_3: int = block_field(
        offset=9,
        type=UInt8(),
        description="Reserved/unknown byte 3 (item bytes 6-9 baseline area)",
        required=False,
        default=0,
    )

    # NOTE: Additional 10-byte component items may follow in actual payloads.
    # Full List<BootSoftwareItem> structure requires dynamic array support.
    # This baseline schema covers first component item only.


# Export schema instance
BLOCK_29772_SCHEMA = BootSoftwareInfoBlock.to_schema()  # type: ignore[attr-defined]
