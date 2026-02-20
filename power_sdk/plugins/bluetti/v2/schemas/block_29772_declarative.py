"""Block 29772 (BOOT_SOFTWARE_INFO) - Bootloader Software Component Information.

VERIFICATION STATUS: reference-Verified (complete item structure proven)

Evidence Sources:
- Switch route: 0x744c → :sswitch_6
  (ConnectManager.reference:8241, handler at 6103-6118)
- Parser method: bootSoftwareInfoParse (ProtocolParserV2.reference:1088-1240)
- Bean class: BootSoftwareItem (BootSoftwareItem.reference:1-282)
- Bean constructor: <init>(JI)V with fields softwareVer:J, softwareType:I
- Item size: 10 bytes per item (const 0xa at line 1111)
- Field extraction logic verified from reference disassembly

Block Type: PARSED (dedicated parser method)
Purpose: Bootloader software component inventory with version information
Returns: List<BootSoftwareItem> (dynamic list of 10-byte items)

Item Structure (from reference, 10 bytes per item):
- Bytes 0-1 (UInt16 BE): softwareType - parsed as hex integer
- Bytes 2-5 (4 bytes): softwareVer - converted via bit32RegByteToNumber to long
- Bytes 6-9 (4 bytes): NOT USED by parser (padding/reserved, purpose unknown)

Parser Logic (ProtocolParserV2.reference:1111-1226):
1. Calculate item count: dataBytes.size() / 10
2. For each item at offset i*10:
   - Concatenate bytes[0]+bytes[1] as hex string, parseInt → softwareType (int)
   - Extract bytes[2:6] (4 bytes), bit32RegByteToNumber → softwareVer (long)
   - Construct BootSoftwareItem(softwareVer, softwareType)
   - Skip bytes[6:10] (not used)
3. Return List<BootSoftwareItem>

SDK Limitation (NOT a verification gap):
- Schema represents FIRST ITEM ONLY (single-item baseline)
- Full dynamic array parsing requires SDK enhancement
- Item structure is FULLY verified from reference

SECURITY CAUTION: Bootloader software component data
- Manufacturer authorization required for write operations
- Requires proper device validation and documentation
"""

from dataclasses import dataclass

from ..protocol.datatypes import UInt8, UInt16, UInt32
from .declarative import block_field, block_schema


@block_schema(
    block_id=29772,
    name="BOOT_SOFTWARE_INFO",
    description="Bootloader software component inventory (first item)",
    min_length=10,
    protocol_version=2000,
    strict=False,
    verification_status="smali_verified",
)
@dataclass
class BootSoftwareInfoBlock:
    """Bootloader software component info schema (reference-verified item structure).

    Maps to BootSoftwareItem bean with constructor <init>(JI)V.
    Parser: bootSoftwareInfoParse (ProtocolParserV2.reference:1088-1240).
    Returns List<BootSoftwareItem> - schema represents first item only.

    SECURITY: Bootloader software data - manufacturer authorization required.
    """

    # First component item (10 bytes, fully verified from reference)
    software_type: int = block_field(
        offset=0,
        type=UInt16(),
        description=(
            "Software component type identifier (reference: softwareType field). "
            "Bytes 0-1 concatenated as hex string, parsed to int. "
            "Maps to bean constructor parameter 2 (int)."
        ),
        required=False,
        default=0,
    )

    software_version: int = block_field(
        offset=2,
        type=UInt32(),
        description=(
            "Software component version (reference: softwareVer field). "
            "Bytes 2-5 converted via bit32RegByteToNumber to long value. "
            "Maps to bean constructor parameter 1 (long). "
            "Note: UInt32 used as proxy for long in schema."
        ),
        required=False,
        default=0,
    )

    unused_byte_0: int = block_field(
        offset=6,
        type=UInt8(),
        description=(
            "Unused byte (parser skips bytes 6-9). "
            "Part of 10-byte item structure but NOT extracted to bean. "
            "Purpose unknown - possibly padding or reserved."
        ),
        required=False,
        default=0,
    )

    unused_byte_1: int = block_field(
        offset=7,
        type=UInt8(),
        description="Unused byte (see unused_byte_0)",
        required=False,
        default=0,
    )

    unused_byte_2: int = block_field(
        offset=8,
        type=UInt8(),
        description="Unused byte (see unused_byte_0)",
        required=False,
        default=0,
    )

    unused_byte_3: int = block_field(
        offset=9,
        type=UInt8(),
        description="Unused byte (see unused_byte_0)",
        required=False,
        default=0,
    )

    # NOTE: Additional 10-byte items may follow in actual multi-component payloads.
    # Full List<BootSoftwareItem> parsing requires SDK dynamic array support.
    # This schema covers FIRST ITEM ONLY (single-item baseline).


# Export schema instance
BLOCK_29772_SCHEMA = BootSoftwareInfoBlock.to_schema()  # type: ignore[attr-defined]

