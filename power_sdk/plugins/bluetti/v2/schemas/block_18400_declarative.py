"""Block 18400 (EPAD_LIQUID_POINT1) - EPAD Base Liquid Calibration Point 1.

reference evidence (FULLY VERIFIED):
- ConnectManager.reference maps 0x47e0 -> EpadParser.baseLiquidPointParse
- Parser returns List<EpadLiquidCalibratePoint> with 2 bytes per item
- Bean constructor: <init>(II)V with params (liquid, volume)
- Event name: "EPAD_BASE_INFO_LIQUID_POINT" (ConnectManager.reference:5865)

Source references:
- EpadParser.baseLiquidPointParse: EpadParser.reference:1602-1789
- EpadLiquidCalibratePoint bean: EpadLiquidCalibratePoint.reference:102-114
- Switch route: ConnectManager.reference:8227 (0x47e0 -> :sswitch_14)

Structure (reference VERIFIED):
- Min length: 2 bytes per calibration point
- Shared parser with blocks 18500, 18600 (all use same baseLiquidPointParse)
- Contains: volume (UInt8 @ offset 0), liquid (UInt8 @ offset 1)
- Part of EPAD liquid measurement system (3 measurement points total)

NOTE: All three EPAD liquid point blocks (18400, 18500, 18600) use the SAME
parser method and have IDENTICAL 2-byte structure. Only the block ID differs.

SDK Limitation: Parser returns List<T> but schema only supports first item.
"""

from .factories import build_epad_liquid_schema

# Generate schema via factory to eliminate duplication
BLOCK_18400_SCHEMA = build_epad_liquid_schema(
    block_id=18400,
    name="EPAD_LIQUID_POINT1",
    point_index=1,
    verification_status="smali_verified",
)

