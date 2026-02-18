"""Block 19000 (SOC_SETTINGS) - SOC Threshold Settings.

Source: docs/blocks/ADDITIONAL_BLOCKS.md (lines 227-263)
Method: commSOCSettingsParse
Bean: List<DeviceSOCThresholdItem>

Purpose: Battery state-of-charge thresholds for grid charge and UPS modes.

Format: Each 2-byte register encodes 2 SOC threshold items (on/off pair).

Byte Layout per Register:
    Byte 0 (low):  [bit7: off_enable][bits6-0: off_soc]
    Byte 1 (high): [bit7: on_enable][bits6-0: on_soc]

Calculation:
    word = (high_byte << 8) | low_byte
    off_soc = word & 0x7F
    off_enable = (word >> 7) & 0x01
    on_soc = (word >> 8) & 0x7F
    on_enable = (word >> 15) & 0x01

Note: Application code must unpack these bitfields.
"""

from dataclasses import dataclass

from power_sdk.protocol.v2.datatypes import UInt16
from .declarative import block_field, block_schema


@block_schema(
    block_id=19000,
    name="SOC_SETTINGS",
    description="Battery SOC threshold settings (bit-packed)",
    min_length=6,
    protocol_version=2000,
    strict=False,
    verification_status="smali_verified",
)
@dataclass
class SocSettingsBlock:
    """SOC threshold settings schema (bit-packed format)."""

    grid_charge_threshold: int = block_field(
        offset=0,
        type=UInt16(),
        description=(
            "Grid charge threshold pair (bit-packed: "
            "bits0-6=off_soc, bit7=off_enable, "
            "bits8-14=on_soc, bit15=on_enable)"
        ),
        required=True,
        default=0,
    )

    ups_mode_threshold: int = block_field(
        offset=2,
        type=UInt16(),
        description=(
            "UPS mode threshold pair (bit-packed: "
            "bits0-6=off_soc, bit7=off_enable, "
            "bits8-14=on_soc, bit15=on_enable)"
        ),
        required=True,
        default=0,
    )

    battery_protect_threshold: int = block_field(
        offset=4,
        type=UInt16(),
        description=(
            "Battery protect threshold pair (bit-packed: "
            "bits0-6=off_soc, bit7=off_enable, "
            "bits8-14=on_soc, bit15=on_enable)"
        ),
        required=False,
        default=0,
    )

    # Parse method supports variable number of threshold pairs (2 bytes each).
    # Baseline schema includes first six pairs used by known profiles.
    threshold_pair_3: int = block_field(
        offset=6,
        type=UInt16(),
        description="Additional threshold pair 3 (bit-packed)",
        required=False,
        default=0,
    )

    threshold_pair_4: int = block_field(
        offset=8,
        type=UInt16(),
        description="Additional threshold pair 4 (bit-packed)",
        required=False,
        default=0,
    )

    threshold_pair_5: int = block_field(
        offset=10,
        type=UInt16(),
        description="Additional threshold pair 5 (bit-packed)",
        required=False,
        default=0,
    )


BLOCK_19000_SCHEMA = SocSettingsBlock.to_schema()  # type: ignore[attr-defined]
