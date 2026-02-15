"""Block 19100 (COMM_DELAY_SETTINGS) - Grid Charge Delay Settings.

Source: ProtocolParserV2.smali lines 2287-2700 (commDelaySettingsParse)
Bean: List<DeviceDelayItem>
Purpose: Grid charge time delay configuration

Smali-verified structure:
- Offsets 0-7: Enable list (8 bytes, bit-packed)
  Each 2-byte hex string contains 4 enable flags (2 bits per flag)
  Total: 16 delay settings supported
- Offsets 8-15: Action list (8 bytes, bit-packed)
  Each 2-byte hex string contains 4 action flags (2 bits per flag)
  Total: 16 action settings supported
- Offsets 16+: Delay item data (structure varies by delay count)

Note: Full delay item parsing requires dynamic structure support.
This schema provides enable/action bit-packed fields for baseline implementation.
"""

from dataclasses import dataclass

from ..protocol.v2.datatypes import UInt16
from .declarative import block_field, block_schema


@block_schema(
    block_id=19100,
    name="COMM_DELAY_SETTINGS",
    description="Grid charge delay configuration (smali-verified)",
    min_length=16,
    protocol_version=2000,
    strict=False,
)
@dataclass
class CommDelaySettingsBlock:
    """Grid charge delay settings schema (smali-verified)."""

    # Enable list (offsets 0-7, bit-packed)
    enable_flags_01: int = block_field(
        offset=0,
        type=UInt16(),
        description=(
            "Enable flags for delays 0-3 (bit-packed: 2 bits per delay)"
        ),
        required=True,
        default=0,
    )

    enable_flags_02: int = block_field(
        offset=2,
        type=UInt16(),
        description=(
            "Enable flags for delays 4-7 (bit-packed: 2 bits per delay)"
        ),
        required=True,
        default=0,
    )

    enable_flags_03: int = block_field(
        offset=4,
        type=UInt16(),
        description=(
            "Enable flags for delays 8-11 (bit-packed: 2 bits per delay)"
        ),
        required=True,
        default=0,
    )

    enable_flags_04: int = block_field(
        offset=6,
        type=UInt16(),
        description=(
            "Enable flags for delays 12-15 (bit-packed: 2 bits per delay)"
        ),
        required=True,
        default=0,
    )

    # Action list (offsets 8-15, bit-packed)
    action_flags_01: int = block_field(
        offset=8,
        type=UInt16(),
        description=(
            "Action flags for delays 0-3 (bit-packed: 2 bits per action)"
        ),
        required=True,
        default=0,
    )

    action_flags_02: int = block_field(
        offset=10,
        type=UInt16(),
        description=(
            "Action flags for delays 4-7 (bit-packed: 2 bits per action)"
        ),
        required=True,
        default=0,
    )

    action_flags_03: int = block_field(
        offset=12,
        type=UInt16(),
        description=(
            "Action flags for delays 8-11 (bit-packed: 2 bits per action)"
        ),
        required=True,
        default=0,
    )

    action_flags_04: int = block_field(
        offset=14,
        type=UInt16(),
        description=(
            "Action flags for delays 12-15 (bit-packed: 2 bits per action)"
        ),
        required=True,
        default=0,
    )

    # Note: Delay item data at offsets 16+ requires dynamic parsing
    # based on enabled delay count. Not implemented in static schema.
    # Application layer should parse using commDelaySettingsParse logic.


BLOCK_19100_SCHEMA = CommDelaySettingsBlock.to_schema()  # type: ignore[attr-defined]
