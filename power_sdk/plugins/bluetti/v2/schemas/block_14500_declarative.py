"""Block 14500 (SMART_PLUG_INFO) - Smart Plug Device Information.

Source: ConnectManager.smali + SmartPlugParser.smali
Block Type: PARSED (SmartPlugParser.baseInfoParse)
Purpose: Smart plug device baseline identification and version/count fields

VERIFICATION STATUS: Smali-Verified
- Switch route: 0x38a4 -> :sswitch_24 (ConnectManager.smali)
- Parser method: SmartPlugParser.baseInfoParse
- Bean class: SmartPlugInfoBean
- Verified schema field mapping:
  * bytes 0-11  -> model (ASCII, setModel)
  * bytes 12-19 -> sn (DeviceSN, setSn)
  * bytes 20-23 -> softwareVer (getMcuSoftwareVer, setSoftwareVer)
  * bytes 24-25 -> nums (UInt16 hex parse, setNums)

Note:
- SmartPlugParser parses additional fields beyond byte 25
  (power/voltage/current/frequency, status bits, faults, alarms, day stats).
- This schema intentionally models only the verified baseline subset above.
"""

from dataclasses import dataclass

from ..protocol.datatypes import String, UInt16, UInt32
from .declarative import block_field, block_schema


@block_schema(
    block_id=14500,
    name="SMART_PLUG_INFO",
    description="Smart plug info baseline (smali-verified)",
    min_length=26,
    protocol_version=2000,
    strict=False,
    verification_status="smali_verified",
)
@dataclass
class SmartPlugInfoBlock:
    """Smart plug information schema (smali-verified baseline).

    Maps directly to SmartPlugParser.baseInfoParse for bytes 0..25.
    """

    model: str = block_field(
        offset=0,
        type=String(length=12),
        description="Smart plug model name (ASCII)",
        required=False,
        default="",
    )
    serial_number: str = block_field(
        offset=12,
        type=String(length=8),
        description="Smart plug serial number",
        required=False,
        default="",
    )
    software_version: int = block_field(
        offset=20,
        type=UInt32(),
        description="Software version from getMcuSoftwareVer (bytes 20-23)",
        required=False,
        default=0,
    )

    plug_count: int = block_field(
        offset=24,
        type=UInt16(),
        description="Number of smart plug channels/items (bytes 24-25, setNums)",
        required=False,
        default=0,
    )


# Export schema instance
BLOCK_14500_SCHEMA = SmartPlugInfoBlock.to_schema()  # type: ignore[attr-defined]
