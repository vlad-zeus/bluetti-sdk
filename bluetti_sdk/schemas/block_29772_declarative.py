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
  * Bytes 2-7: Component value (6 bytes processed via bit32RegByteToNumber)
  * Creates item with (long_value, 6_bytes_data, int_address)
- Variable length block (processes in 10-byte chunks)

CAUTION: This block contains boot software component information.
DO NOT use for write control without:
- Proper device validation and authorization
- Understanding of boot component structure
- Manufacturer documentation for software updates
Incorrect boot software operations may brick the device or void warranty.

TODO(smali-verify): Baseline implementation provides first item (10 bytes).
Full dynamic array support requires multi-item parsing implementation.
Bean field names and exact value semantics need deeper analysis.
"""

from dataclasses import dataclass

from ..protocol.v2.datatypes import UInt8, UInt16
from .declarative import block_field, block_schema


@block_schema(
    block_id=29772,
    name="BOOT_SOFTWARE_INFO",
    description="Boot software component info (smali-verified parse method)",
    min_length=10,
    protocol_version=2000,
    strict=False,
    verification_status="inferred",
)
@dataclass
class BootSoftwareInfoBlock:
    """Boot software info schema (smali-verified, first item baseline).

    This block has dedicated bootSoftwareInfoParse method.
    Returns list of 10-byte items (component address + value data).

    CAUTION: Boot software control - requires manufacturer authorization.
    """

    # First component item (10 bytes)
    component_address: int = block_field(
        offset=0,
        type=UInt16(),
        description=(
            "First component address (bytes 0-1 combined as hex) "
            "(TODO: verify exact address mapping)"
        ),
        required=False,
        default=0,
    )

    component_value_byte0: int = block_field(
        offset=2,
        type=UInt8(),
        description="Component value data byte 0 (TODO: verify semantic)",
        required=False,
        default=0,
    )

    component_value_byte1: int = block_field(
        offset=3,
        type=UInt8(),
        description="Component value data byte 1 (TODO: verify semantic)",
        required=False,
        default=0,
    )

    component_value_byte2: int = block_field(
        offset=4,
        type=UInt8(),
        description="Component value data byte 2 (TODO: verify semantic)",
        required=False,
        default=0,
    )

    component_value_byte3: int = block_field(
        offset=5,
        type=UInt8(),
        description="Component value data byte 3 (TODO: verify semantic)",
        required=False,
        default=0,
    )

    component_value_byte4: int = block_field(
        offset=6,
        type=UInt8(),
        description="Component value data byte 4 (TODO: verify semantic)",
        required=False,
        default=0,
    )

    component_value_byte5: int = block_field(
        offset=7,
        type=UInt8(),
        description="Component value data byte 5 (TODO: verify semantic)",
        required=False,
        default=0,
    )

    # NOTE: Additional 10-byte component items may follow in actual payloads.
    # Full List<BootSoftwareItem> structure requires dynamic array support.
    # This baseline schema covers first component item only.


# Export schema instance
BLOCK_29772_SCHEMA = BootSoftwareInfoBlock.to_schema()  # type: ignore[attr-defined]
