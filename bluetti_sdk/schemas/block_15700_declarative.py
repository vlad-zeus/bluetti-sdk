"""Block 15700 (DC_HUB_INFO) - DC Hub Device Information.

Source: ProtocolParserV2.smali lines 3590+ (dcHubInfoParse)
Bean: DeviceDcHubInfo
Block Type: PARSED (dedicated parse method)
Purpose: DC expansion hub monitoring - all DC output ports status

Structure (smali-verified):
- Min length from smali parse path: 68 bytes (0x44, highest index 0x43)
- Parse method: dcHub InfoParse at line 3590
- Bean fields include:
  * Model, Serial Number
  * DC Input: power, voltage, current
  * DC Output: power, voltage, current
  * Cigarette Lighter 1/2: output power, voltage, status
  * USB-A: output power, voltage, status
  * Type-C 1/2: output power, voltage, status
  * Anderson: output power, voltage, status

VERIFICATION STATUS: Partial
- Parse method: dcHubInfoParse confirmed at ProtocolParserV2.smali:3590
- Bean: DeviceDcHubInfo confirmed
- Structure: byte-level parsing sequence confirmed from method body
- Scalar offsets for model/SN/DC in/out and per-port power/volt are mapped from
  explicit `List.get(index)` calls in the method
- DEFERRED: remaining output object semantics beyond scalar fields
"""

from dataclasses import dataclass

from ..protocol.v2.datatypes import String, UInt16
from .declarative import block_field, block_schema


@block_schema(
    block_id=15700,
    name="DC_HUB_INFO",
    description=(
        "DC Hub device monitoring (parse method confirmed, key offsets verified)"
    ),
    min_length=68,
    protocol_version=2000,
    strict=False,
    verification_status="partial",
)
@dataclass
class DCHubInfoBlock:
    """DC Hub information schema (baseline from bean structure).

    This block has dedicated dcHubInfoParse method.
    Offsets below are derived from explicit List.get(index) usage in smali.
    """

    # Device identification (offsets 0-19)
    model: str = block_field(
        offset=0,
        type=String(length=12),
        description="DC Hub model identifier (bytes 0-11, ASCII)",
        required=False,
        default="",
    )

    serial_number: str = block_field(
        offset=12,
        type=String(length=8),
        description="DC Hub serial number (bytes 12-19)",
        required=False,
        default="",
    )

    # DC Input monitoring (offsets 20-27)
    dc_input_power: int = block_field(
        offset=20,
        type=UInt16(),
        unit="W",
        description="DC input power (bytes 20-21)",
        required=False,
        default=0,
    )

    dc_input_voltage: int = block_field(
        offset=22,
        type=UInt16(),
        unit="raw",
        description="DC input voltage raw value (bytes 22-23)",
        required=False,
        default=0,
    )

    dc_input_current: int = block_field(
        offset=24,
        type=UInt16(),
        unit="raw",
        description="DC input current raw value (bytes 24-25)",
        required=False,
        default=0,
    )

    # DC Output monitoring
    dc_output_power: int = block_field(
        offset=26,
        type=UInt16(),
        unit="W",
        description="DC output total power (bytes 26-27)",
        required=False,
        default=0,
    )

    dc_output_voltage: int = block_field(
        offset=28,
        type=UInt16(),
        unit="raw",
        description="DC output voltage raw value (bytes 28-29)",
        required=False,
        default=0,
    )

    dc_output_current: int = block_field(
        offset=30,
        type=UInt16(),
        unit="raw",
        description="DC output current raw value (bytes 30-31)",
        required=False,
        default=0,
    )

    # Per-port scalar monitoring from parse method
    cigarette_lighter_1_power: int = block_field(
        offset=32,
        type=UInt16(),
        unit="W",
        description="Cigarette lighter 1 power (bytes 32-33)",
        required=False,
        default=0,
    )

    cigarette_lighter_1_voltage: int = block_field(
        offset=34,
        type=UInt16(),
        unit="raw",
        description="Cigarette lighter 1 voltage raw value (bytes 34-35)",
        required=False,
        default=0,
    )

    cigarette_lighter_2_power: int = block_field(
        offset=38,
        type=UInt16(),
        unit="W",
        description="Cigarette lighter 2 power (bytes 38-39)",
        required=False,
        default=0,
    )

    cigarette_lighter_2_voltage: int = block_field(
        offset=40,
        type=UInt16(),
        unit="raw",
        description="Cigarette lighter 2 voltage raw value (bytes 40-41)",
        required=False,
        default=0,
    )

    usb_a_power: int = block_field(
        offset=44,
        type=UInt16(),
        unit="W",
        description="USB-A output power (bytes 44-45)",
        required=False,
        default=0,
    )

    usb_a_voltage: int = block_field(
        offset=46,
        type=UInt16(),
        unit="raw",
        description="USB-A output voltage raw value (bytes 46-47)",
        required=False,
        default=0,
    )

    type_c_1_power: int = block_field(
        offset=50,
        type=UInt16(),
        unit="W",
        description="Type-C 1 output power (bytes 50-51)",
        required=False,
        default=0,
    )

    type_c_1_voltage: int = block_field(
        offset=52,
        type=UInt16(),
        unit="raw",
        description="Type-C 1 output voltage raw value (bytes 52-53)",
        required=False,
        default=0,
    )

    type_c_2_power: int = block_field(
        offset=56,
        type=UInt16(),
        unit="W",
        description="Type-C 2 output power (bytes 56-57)",
        required=False,
        default=0,
    )

    type_c_2_voltage: int = block_field(
        offset=58,
        type=UInt16(),
        unit="raw",
        description="Type-C 2 output voltage raw value (bytes 58-59)",
        required=False,
        default=0,
    )

    anderson_power: int = block_field(
        offset=62,
        type=UInt16(),
        unit="W",
        description="Anderson output power (bytes 62-63)",
        required=False,
        default=0,
    )

    anderson_voltage: int = block_field(
        offset=64,
        type=UInt16(),
        unit="raw",
        description="Anderson output voltage raw value (bytes 64-65)",
        required=False,
        default=0,
    )


# Export schema instance
BLOCK_15700_SCHEMA = DCHubInfoBlock.to_schema()  # type: ignore[attr-defined]
