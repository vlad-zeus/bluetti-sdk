"""Block 29770 (BOOT_UPGRADE_SUPPORT) - Bootloader Upgrade Support Information.

VERIFICATION STATUS: Smali-Verified (complete evidence from smali analysis)

Evidence Sources:
- Switch route: 0x744a → :sswitch_7 (ConnectManager.smali:8240, handler at 6122-6130)
- Parser method: bootUpgradeSupportParse (ProtocolParserV2.smali:1242-1343)
- Bean class: BootUpgradeSupport (BootUpgradeSupport.smali:1-275)
- Bean constructor: <init>(II)V with fields isSupport:I, softwareVerTotal:I
- Field extraction logic verified from smali disassembly

Block Type: PARSED (dedicated parser method)
Purpose: Bootloader upgrade capability flags and software version information

Structure (from smali):
- Min length: 4 bytes
- Binary format: Two UInt16 big-endian values
- Parser logic:
  * Bytes 0-1 (UInt16 BE) → parseInt as hex, AND with 1 → isSupport field (boolean flag)
  * Bytes 2-3 (UInt16 BE) → parseInt as hex → softwareVerTotal field (version count)

Field Semantics (from BootUpgradeSupport bean):
- isSupport: Upgrade support flag (LSB only matters, 0=not supported, 1=supported)
- softwareVerTotal: Total count of software components/versions

SECURITY CAUTION: This block contains bootloader upgrade information.
DO NOT attempt to write/modify without:
- Manufacturer authorization and documentation
- Understanding of boot upgrade protocols and risks
- Proper device validation
Incorrect bootloader operations may permanently brick the device.
"""

from dataclasses import dataclass

from ..protocol.v2.datatypes import UInt16
from .declarative import block_field, block_schema


@block_schema(
    block_id=29770,
    name="BOOT_UPGRADE_SUPPORT",
    description="Bootloader upgrade support flags and software version count",
    min_length=4,
    protocol_version=2000,
    strict=False,
    verification_status="smali_verified",
)
@dataclass
class BootUpgradeSupportBlock:
    """Bootloader upgrade support schema (smali-verified).

    Maps to BootUpgradeSupport bean with constructor <init>(II)V.
    Parser: bootUpgradeSupportParse (ProtocolParserV2.smali:1242-1343).

    SECURITY: Bootloader upgrade flags - manufacturer authorization required.
    """

    is_supported: int = block_field(
        offset=0,
        type=UInt16(),
        description=(
            "Upgrade support flag (smali: isSupport field). "
            "Value is parsed from UInt16 and AND-ed with 1. "
            "Interpret as boolean: 0=upgrade not supported, 1=upgrade supported. "
            "Only LSB is meaningful."
        ),
        required=False,
        default=0,
    )

    software_version_total: int = block_field(
        offset=2,
        type=UInt16(),
        description=(
            "Total software component/version count (smali: softwareVerTotal field). "
            "Parsed from UInt16 as raw integer value."
        ),
        required=False,
        default=0,
    )


# Export schema instance
BLOCK_29770_SCHEMA = BootUpgradeSupportBlock.to_schema()  # type: ignore[attr-defined]
