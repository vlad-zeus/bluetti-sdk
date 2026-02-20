"""Block 18600 (EPAD_LIQUID_POINT3) - EPAD Base Liquid Calibration Point 3.

reference evidence (FULLY VERIFIED):
- ConnectManager.reference maps 0x48a8 -> EpadParser.baseLiquidPointParse
- Parser returns List<EpadLiquidCalibratePoint> with 2 bytes per item
- Bean constructor: <init>(II)V with params (liquid, volume)
- Event name: "EPAD_BASE_INFO_LIQUID_POINT" (ConnectManager.reference:5865)

Source references:
- EpadParser.baseLiquidPointParse: EpadParser.reference:1602-1789
- EpadLiquidCalibratePoint bean: EpadLiquidCalibratePoint.reference:102-114
- Switch route: ConnectManager.reference:8229 (0x48a8 -> :sswitch_12)

Structure (reference VERIFIED):
- Min length: 2 bytes per calibration point
- Shared parser with blocks 18400, 18500 (all use same baseLiquidPointParse)
- Contains: volume (UInt8 @ offset 0), liquid (UInt8 @ offset 1)
- Part of EPAD liquid measurement system (3 measurement points total)

NOTE: All three EPAD liquid point blocks (18400, 18500, 18600) use the SAME
parser method and have IDENTICAL 2-byte structure. Only the block ID differs.

SDK Limitation: Parser returns List<T> but schema only supports first item.
"""

from .factories import build_epad_liquid_schema

# Generate schema via factory to eliminate duplication
BLOCK_18600_SCHEMA = build_epad_liquid_schema(
    block_id=18600,
    name="EPAD_LIQUID_POINT3",
    point_index=3,
    verification_status="verified_reference",
)
