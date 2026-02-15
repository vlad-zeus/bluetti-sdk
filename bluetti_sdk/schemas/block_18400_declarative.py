"""Block 18400 (EPAD_LIQUID_POINT1) - EPAD Base Liquid Measurement Point 1.

Source: ProtocolParserV2.smali switch case (0x47e0 -> sswitch_7)
Related: ProtocolAddrV2.smali defines EPAD_BASE_LIQUID_POINT1 at 0x47e0
Block Type: UNKNOWN (no dedicated parse method found)
Purpose: EPAD liquid measurement point 1 data (part of multi-point monitoring)

Structure (PROVISIONAL):
- Min length from smali: 100 bytes (0x64)
- Shared switch label with 18500, 18600 (all liquid point blocks)
- Likely contains: measurement data, calibration values, sensor readings
- Part of EPAD liquid measurement system (3 measurement points total)

NOTE: All three EPAD liquid point blocks (18400, 18500, 18600) share the same
switch handler and min length. Field structure is highly provisional without
actual EPAD device or detailed parse method analysis.

TODO(smali-verify): EPAD device with liquid measurement capability required.
No dedicated parse method found - field mapping requires device testing.
"""

from dataclasses import dataclass

from ..protocol.v2.datatypes import UInt8, UInt16
from .declarative import block_field, block_schema


@block_schema(
    block_id=18400,
    name="EPAD_LIQUID_POINT1",
    description="EPAD liquid measurement point 1 (provisional - no parse method)",
    min_length=100,
    protocol_version=2000,
    strict=False,
)
@dataclass
class EPadLiquidPoint1Block:
    """EPAD liquid measurement point 1 schema (provisional baseline).

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


# Export schema instance
BLOCK_18400_SCHEMA = EPadLiquidPoint1Block.to_schema()  # type: ignore[attr-defined]
