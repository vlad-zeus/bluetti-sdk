"""Factory for generating EPAD liquid measurement point schemas.

All three EPAD liquid point blocks (18400, 18500, 18600) share identical
structure and field definitions. This factory eliminates ~230 lines of
code duplication by generating schemas from a single template.

Source: ProtocolParserV2.smali switch case (sswitch_7)
- 18400 (0x47e0) -> EPAD_BASE_LIQUID_POINT1
- 18500 (0x4844) -> EPAD_BASE_LIQUID_POINT2
- 18600 (0x48a8) -> EPAD_BASE_LIQUID_POINT3

Block Type: parser-backed (EpadParser.baseLiquidPointParse)
"""

from dataclasses import dataclass
from typing import Any

from power_sdk.plugins.bluetti.v2.constants import V2_PROTOCOL_VERSION

from ...protocol.datatypes import UInt8
from ..declarative import block_field, block_schema


def build_epad_liquid_schema(
    block_id: int,
    name: str,
    point_index: int,
    verification_status: str = "smali_verified",
) -> Any:
    """Build an EPAD liquid measurement point schema.

    All three EPAD liquid point blocks share the same parser method
    (EpadParser.baseLiquidPointParse) which returns List<EpadLiquidCalibratePoint>.
    Each item in the list is 2 bytes with structure verified from smali.

    Args:
        block_id: Block ID (18400, 18500, or 18600)
        name: Block name (e.g., "EPAD_LIQUID_POINT1")
        point_index: Measurement point number (1, 2, or 3)
        verification_status: Verification status (default: "smali_verified")

    Returns:
        BlockSchema instance ready for registration

    Example:
        >>> schema = build_epad_liquid_schema(18400, "EPAD_LIQUID_POINT1", 1)
        >>> schema.block_id
        18400
        >>> schema.min_length
        2
        >>> schema.verification_status
        'smali_verified'
    """
    # Create dynamic dataclass with unique name
    class_name = f"EPadLiquidPoint{point_index}Block"

    @block_schema(
        block_id=block_id,
        name=name,
        description=(
            f"EPAD liquid measurement point {point_index} calibration data "
            f"(first item only - list support pending)"
        ),
        min_length=2,
        protocol_version=V2_PROTOCOL_VERSION,
        strict=False,
        verification_status=verification_status,
    )
    @dataclass
    class EPadLiquidPointBlock:
        """EPAD liquid calibration point schema (smali verified).

        Source: EpadParser.baseLiquidPointParse (EpadParser.smali:1602-1789)
        Bean: EpadLiquidCalibratePoint with constructor <init>(II)V
        Event: "EPAD_BASE_INFO_LIQUID_POINT" (ConnectManager.smali:5865)

        Parser returns List<EpadLiquidCalibratePoint> where each item is 2 bytes.
        This schema represents the FIRST calibration point only.

        SDK Limitation: The parser returns a dynamic list, but current schema
        framework only supports parsing the first item. Full list support is
        tracked in SDK enhancement backlog.

        Field structure per item (verified from smali bytecode):
        - Offset 0: volume (UInt8) - Volume measurement value
        - Offset 1: liquid (UInt8) - Liquid level measurement value

        Note: Field names come from bean setters (setVolume/setLiquid) but
        actual semantic meaning may differ. Units unknown without device docs.
        """

        volume: int = block_field(
            offset=0,
            type=UInt8(),
            description=(
                "Volume measurement value for calibration point "
                "(semantic meaning/unit unknown)"
            ),
            required=False,
            default=0,
        )

        liquid: int = block_field(
            offset=1,
            type=UInt8(),
            description=(
                "Liquid level measurement value for calibration point "
                "(semantic meaning/unit unknown)"
            ),
            required=False,
            default=0,
        )

    # Set the class name for better debugging/introspection
    EPadLiquidPointBlock.__name__ = class_name
    EPadLiquidPointBlock.__qualname__ = class_name

    # Return the schema instance
    return EPadLiquidPointBlock.to_schema()  # type: ignore[attr-defined]
