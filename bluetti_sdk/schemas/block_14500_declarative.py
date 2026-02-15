"""Block 14500 (SMART_PLUG_INFO) - Smart Plug Device Information.

Source: ProtocolParserV2.smali switch case (0x38a4 -> sswitch_15)
Block Type: EVENT (no dedicated parse method)
Purpose: Smart plug device identification and status

Structure (PROVISIONAL):
- Min length from smali: 26-28 bytes (protocol version dependent)
- Common accessory info pattern: model + SN + status fields

Note: This is a provisional baseline implementation. Full field mapping requires:
- Actual smart plug device for testing
- Event payload capture and analysis
- Bean structure verification (SmartPlugInfo class)

TODO(smali-verify): Complete field mapping when smart plug device available
"""

from dataclasses import dataclass

from ..protocol.v2.datatypes import String, UInt8, UInt16
from .declarative import block_field, block_schema


@block_schema(
    block_id=14500,
    name="SMART_PLUG_INFO",
    description="Smart plug device information (provisional - EVENT block)",
    min_length=26,
    protocol_version=2000,
    strict=False,
    verification_status="inferred",
)
@dataclass
class SmartPlugInfoBlock:
    """Smart plug information schema (provisional baseline).

    This block follows EVENT pattern without dedicated parse method.
    Field mapping is provisional pending actual device testing.
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
    status: int = block_field(
        offset=20,
        type=UInt16(),
        description="Device status flags (TODO: verify bit mapping)",
        required=False,
        default=0,
    )
    power: int = block_field(
        offset=22,
        type=UInt16(),
        unit="W",
        description="Current power output (TODO: verify scale)",
        required=False,
        default=0,
    )
    enable: int = block_field(
        offset=24,
        type=UInt8(),
        description="Plug enable status (TODO: verify)",
        required=False,
        default=0,
    )


# Export schema instance
BLOCK_14500_SCHEMA = SmartPlugInfoBlock.to_schema()  # type: ignore[attr-defined]
