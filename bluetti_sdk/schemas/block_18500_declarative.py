"""Block 18500 (EPAD_LIQUID_POINT2) - EPAD Base Liquid Measurement Point 2.

Source: ProtocolParserV2.smali switch case (0x4844 -> sswitch_7)
Related: ProtocolAddrV2.smali defines EPAD_BASE_LIQUID_POINT2 at 0x4844
Block Type: parser-backed (EpadParser.baseLiquidPointParse)
Purpose: EPAD liquid measurement point 2 data (part of multi-point monitoring)

Structure (PROVISIONAL):
- Min length from smali: 100 bytes (0x64)
- Shared switch label with 18400, 18600 (all liquid point blocks)
- Likely contains: measurement data, calibration values, sensor readings
- Part of EPAD liquid measurement system (3 measurement points total)

NOTE: All three EPAD liquid point blocks (18400, 18500, 18600) share the same
switch handler and min length. Field structure is highly provisional without
actual EPAD device or detailed parse method analysis.

TODO(smali-verify): EPAD device with liquid measurement capability required.
Parser path is confirmed; business semantics still require device testing.
"""

from .factories import build_epad_liquid_schema

# Generate schema via factory to eliminate duplication
BLOCK_18500_SCHEMA = build_epad_liquid_schema(
    block_id=18500,
    name="EPAD_LIQUID_POINT2",
    point_index=2,
)
