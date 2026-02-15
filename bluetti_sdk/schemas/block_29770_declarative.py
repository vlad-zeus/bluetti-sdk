"""Block 29770 (BOOT_UPGRADE_SUPPORT) - Boot Upgrade Support Information.

Source: ProtocolParserV2.smali (bootUpgradeSupportParse method)
Bean: Lnet/poweroak/bluetticloud/ui/connectv2/bean/BootUpgradeSupport
Block Type: PARSED (dedicated parse method exists)
Purpose: Boot loader upgrade capability and version information

Structure (smali-verified):
- Min length from smali: 2 bytes (0x2)
- Parse method: bootUpgradeSupportParse()
- Extracts 2 integer values from hex byte pairs:
  * Indices 0-1: First upgrade support value
  * Indices 2-3: Second upgrade support value

CAUTION: This block contains boot loader upgrade support information.
DO NOT use for write control without:
- Proper device validation and authorization
- Understanding of boot upgrade protocols
- Manufacturer documentation for upgrade procedures
Incorrect boot upgrade operations may brick the device or void warranty.

VERIFICATION STATUS: Partial
- Parse method: bootUpgradeSupportParse confirmed at ProtocolParserV2.smali:1242
- Bean: BootUpgradeSupport confirmed
- Structure: 2-byte payload, hex-parsed integers confirmed
- DEFERRED: Full field semantics require deeper smali disassembly
  (bean constructor analysis)
- Full smali_verified upgrade pending comprehensive RE session
"""

from dataclasses import dataclass

from ..protocol.v2.datatypes import UInt8
from .declarative import block_field, block_schema


@block_schema(
    block_id=29770,
    name="BOOT_UPGRADE_SUPPORT",
    description=(
        "Boot upgrade support information (parse method confirmed, semantics partial)"
    ),
    min_length=2,
    protocol_version=2000,
    strict=False,
    verification_status="partial",
)
@dataclass
class BootUpgradeSupportBlock:
    """Boot upgrade support schema (smali-verified structure).

    This block has dedicated bootUpgradeSupportParse method.
    Extracts 2 integer values from 2-byte payload via hex parsing.

    CAUTION: Boot upgrade control - requires manufacturer authorization.
    """

    upgrade_support_value1: int = block_field(
        offset=0,
        type=UInt8(),
        description=(
            "First upgrade support value (hex parsed from bytes 0-1) "
            "(TODO: verify exact semantic)"
        ),
        required=False,
        default=0,
    )

    upgrade_support_value2: int = block_field(
        offset=1,
        type=UInt8(),
        description=(
            "Second upgrade support value (hex parsed from bytes 2-3) "
            "(TODO: verify exact semantic)"
        ),
        required=False,
        default=0,
    )


# Export schema instance
BLOCK_29770_SCHEMA = BootUpgradeSupportBlock.to_schema()  # type: ignore[attr-defined]
