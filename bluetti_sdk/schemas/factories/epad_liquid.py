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

from ...constants import V2_PROTOCOL_VERSION
from ...protocol.v2.datatypes import UInt8, UInt16
from ..declarative import block_field, block_schema


def build_epad_liquid_schema(
    block_id: int,
    name: str,
    point_index: int,
    verification_status: str = "partial",
) -> Any:
    """Build an EPAD liquid measurement point schema.

    All three EPAD liquid point blocks share the same 100-byte structure
    with identical field definitions. The only differences are block_id,
    name, and point_index metadata.

    Args:
        block_id: Block ID (18400, 18500, or 18600)
        name: Block name (e.g., "EPAD_LIQUID_POINT1")
        point_index: Measurement point number (1, 2, or 3)
        verification_status: Verification status (default: "partial")

    Returns:
        BlockSchema instance ready for registration

    Example:
        >>> schema = build_epad_liquid_schema(18400, "EPAD_LIQUID_POINT1", 1)
        >>> schema.block_id
        18400
        >>> schema.min_length
        100
        >>> schema.verification_status
        'partial'
    """
    # Create dynamic dataclass with unique name
    class_name = f"EPadLiquidPoint{point_index}Block"

    @block_schema(
        block_id=block_id,
        name=name,
        description=(
            f"EPAD liquid measurement point {point_index} "
            "(provisional - no parse method)"
        ),
        min_length=100,
        protocol_version=V2_PROTOCOL_VERSION,
        strict=False,
        verification_status=verification_status,
    )
    @dataclass
    class EPadLiquidPointBlock:
        """EPAD liquid measurement point schema (provisional baseline).

        This block has no dedicated parse method. Part of EPAD liquid
        measurement system with 3 measurement points (18400/18500/18600).

        Field mapping is highly provisional pending EPAD device testing.
        """

        # Measurement point identification (offsets 0-3)
        point_id: int = block_field(
            offset=0,
            type=UInt8(),
            description="Measurement point identifier (TODO: verify offset)",
            required=False,
            default=0,
        )

        point_status: int = block_field(
            offset=1,
            type=UInt8(),
            description="Point status flags (TODO: verify offset and bit mapping)",
            required=False,
            default=0,
        )

        # Measurement data (offsets 2-11)
        temperature: int = block_field(
            offset=2,
            type=UInt16(),
            unit="0.1°C",
            description="Liquid temperature reading (TODO: verify offset and scale)",
            required=False,
            default=0,
        )

        pressure: int = block_field(
            offset=4,
            type=UInt16(),
            description="Liquid pressure reading (TODO: verify offset and unit)",
            required=False,
            default=0,
        )

        flow_rate: int = block_field(
            offset=6,
            type=UInt16(),
            description="Liquid flow rate (TODO: verify offset and unit)",
            required=False,
            default=0,
        )

        level: int = block_field(
            offset=8,
            type=UInt16(),
            description="Liquid level measurement (TODO: verify offset and unit)",
            required=False,
            default=0,
        )

        # Calibration data (offsets 10+)
        calibration_offset: int = block_field(
            offset=10,
            type=UInt16(),
            description="Calibration offset value (TODO: verify offset)",
            required=False,
            default=0,
        )

        # NOTE: Remaining ~88 bytes likely contain:
        # - Additional sensor readings
        # - Historical data points
        # - Calibration coefficients
        # - Quality/error indicators
        # Requires EPAD liquid measurement device to map accurately

    # Set the class name for better debugging/introspection
    EPadLiquidPointBlock.__name__ = class_name
    EPadLiquidPointBlock.__qualname__ = class_name

    # Return the schema instance
    return EPadLiquidPointBlock.to_schema()  # type: ignore[attr-defined]
