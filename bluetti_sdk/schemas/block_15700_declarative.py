"""Block 15700 (DC_HUB_INFO) - DC Hub Device Information.

Source: ProtocolParserV2.smali lines 3590+ (dcHubInfoParse)
Bean: DeviceDcHubInfo
Block Type: PARSED (dedicated parse method)
Purpose: DC expansion hub monitoring - all DC output ports status

Structure (smali-verified):
- Min length from smali: 50 bytes (0x32)
- Parse method: dcHub InfoParse at line 3590
- Bean fields include:
  * Model, Serial Number
  * DC Input: power, voltage, current
  * DC Output: power, voltage, current
  * Cigarette Lighter 1/2: output power, voltage, status
  * USB-A: output power, voltage, status
  * Type-C 1/2: output power, voltage, status
  * Anderson: output power, voltage, status

Field mapping is PROVISIONAL pending detailed smali parse method analysis.
Complete offset extraction requires full dcHubInfoParse disassembly.

TODO(smali-verify): Extract exact field offsets from dcHubInfoParse method body.
Requires analyzing setter call sequence and byte array access patterns.
"""

from dataclasses import dataclass

from ..protocol.v2.datatypes import String, UInt8, UInt16
from .declarative import block_field, block_schema


@block_schema(
    block_id=15700,
    name="DC_HUB_INFO",
    description="DC Hub device monitoring (partial smali-verified)",
    min_length=50,
    protocol_version=2000,
    strict=False,
    verification_status="inferred",
)
@dataclass
class DCHubInfoBlock:
    """DC Hub information schema (baseline from bean structure).

    This block has dedicated dcHubInfoParse method.
    Field offsets are provisional based on typical DC hub patterns.
    """

    # Device identification (offsets 0-19)
    model: str = block_field(
        offset=0,
        type=String(length=12),
        description="DC Hub model identifier (TODO: verify offset)",
        required=False,
        default="",
    )

    serial_number: str = block_field(
        offset=12,
        type=String(length=8),
        description="DC Hub serial number (TODO: verify offset)",
        required=False,
        default="",
    )

    # DC Input monitoring (offsets 20-27)
    dc_input_power: int = block_field(
        offset=20,
        type=UInt16(),
        unit="W",
        description="DC input power (TODO: verify offset)",
        required=False,
        default=0,
    )

    dc_input_voltage: int = block_field(
        offset=22,
        type=UInt16(),
        unit="0.1V",
        description="DC input voltage (TODO: verify offset and scale)",
        required=False,
        default=0,
    )

    dc_input_current: int = block_field(
        offset=24,
        type=UInt16(),
        unit="0.1A",
        description="DC input current (TODO: verify offset and scale)",
        required=False,
        default=0,
    )

    # DC Output monitoring (offsets 26-33)
    dc_output_power: int = block_field(
        offset=26,
        type=UInt16(),
        unit="W",
        description="DC output total power (TODO: verify offset)",
        required=False,
        default=0,
    )

    dc_output_voltage: int = block_field(
        offset=28,
        type=UInt16(),
        unit="0.1V",
        description="DC output voltage (TODO: verify offset and scale)",
        required=False,
        default=0,
    )

    dc_output_current: int = block_field(
        offset=30,
        type=UInt16(),
        unit="0.1A",
        description="DC output current (TODO: verify offset and scale)",
        required=False,
        default=0,
    )

    # Port status flags (offsets 32+)
    cigarette_lighter_1_status: int = block_field(
        offset=32,
        type=UInt8(),
        description="Cigarette lighter port 1 enable status (TODO: verify offset)",
        required=False,
        default=0,
    )

    cigarette_lighter_2_status: int = block_field(
        offset=33,
        type=UInt8(),
        description="Cigarette lighter port 2 enable status (TODO: verify offset)",
        required=False,
        default=0,
    )

    usb_a_status: int = block_field(
        offset=34,
        type=UInt8(),
        description="USB-A port enable status (TODO: verify offset)",
        required=False,
        default=0,
    )

    type_c_1_status: int = block_field(
        offset=35,
        type=UInt8(),
        description="Type-C port 1 enable status (TODO: verify offset)",
        required=False,
        default=0,
    )

    type_c_2_status: int = block_field(
        offset=36,
        type=UInt8(),
        description="Type-C port 2 enable status (TODO: verify offset)",
        required=False,
        default=0,
    )

    anderson_status: int = block_field(
        offset=37,
        type=UInt8(),
        description="Anderson connector enable status (TODO: verify offset)",
        required=False,
        default=0,
    )


# Export schema instance
BLOCK_15700_SCHEMA = DCHubInfoBlock.to_schema()  # type: ignore[attr-defined]
