"""Block 40127 (HOME_STORAGE_SETTINGS) - Home Storage Mode Settings.

Source: ProtocolParserV2.smali lines 13955-14700 (parseHomeStorageSettings)
Bean: HomeStorageSettingsBean
Purpose: Home energy storage system configuration

Smali-verified structure (partial):
- Offsets 0-1: Reserved/flags (UInt16)
- Offsets 2-3: Setting enable flags 1 (UInt16, bit-packed control flags)
- Offsets 4-5: Grid power limit L1 (UInt16, W)
- Offsets 6-7: Grid power limit L2 (UInt16, W)
- Offsets 8-9: Grid power limit L3 (UInt16, W)
- Offsets 10-11: Auto test enable (UInt16, bit-packed flags)
- Offsets 12-13: Grid undervoltage 1 value (UInt16, V*10)
- Offsets 14-15: Grid undervoltage 1 time (UInt16, ms)
- Offsets 16-17: Grid undervoltage 2 value (UInt16, V*10)
- Offsets 18-19: Grid undervoltage 2 time (UInt16, ms)
- Offsets 20-21: Grid overvoltage 1 value (UInt16, V*10)
- Offsets 22-23: Grid overvoltage 1 time (UInt16, ms)
- Offsets 24+: Additional grid protection and TOU settings (30+ fields)

Note: HomeStorageSettingsBean has 38+ constructor parameters.
This schema provides first 12 fields as baseline (offsets 0-23).
Full field mapping requires comprehensive smali analysis of all setters.

**CAUTION**: This block controls critical grid-tied inverter settings.
Incorrect configuration may violate grid codes or damage equipment.
Only modify with proper understanding of grid compliance requirements.
"""

from dataclasses import dataclass

from ..protocol.v2.datatypes import UInt16
from .declarative import block_field, block_schema


@block_schema(
    block_id=40127,
    name="HOME_STORAGE_SETTINGS",
    description="Home storage mode configuration (partial smali-verified)",
    min_length=24,
    protocol_version=2000,
    strict=False,
)
@dataclass
class HomeStorageSettingsBlock:
    """Home storage settings schema (partial smali-verified baseline)."""

    # Global enable flags (offset 2-3)
    setting_enable_1: int = block_field(
        offset=2,
        type=UInt16(),
        description=(
            "Setting enable flags 1 (bit-packed control flags for "
            "various home storage features)"
        ),
        required=True,
        default=0,
    )

    # Grid power limits (offsets 4-9)
    grid_power_l1: int = block_field(
        offset=4,
        type=UInt16(),
        description="Grid power limit L1 (phase 1)",
        unit="W",
        required=True,
        default=0,
    )

    grid_power_l2: int = block_field(
        offset=6,
        type=UInt16(),
        description="Grid power limit L2 (phase 2)",
        unit="W",
        required=True,
        default=0,
    )

    grid_power_l3: int = block_field(
        offset=8,
        type=UInt16(),
        description="Grid power limit L3 (phase 3)",
        unit="W",
        required=True,
        default=0,
    )

    # Auto test enable (offset 10-11)
    auto_test_enable: int = block_field(
        offset=10,
        type=UInt16(),
        description="Auto test enable flags (bit-packed)",
        required=False,
        default=0,
    )

    # Grid protection settings (offsets 12-23)
    grid_uv1_value: int = block_field(
        offset=12,
        type=UInt16(),
        description="Grid undervoltage 1 threshold (V, scaled *10)",
        unit="V",
        required=False,
        default=0,
    )

    grid_uv1_time: int = block_field(
        offset=14,
        type=UInt16(),
        description="Grid undervoltage 1 trip time",
        unit="ms",
        required=False,
        default=0,
    )

    grid_uv2_value: int = block_field(
        offset=16,
        type=UInt16(),
        description="Grid undervoltage 2 threshold (V, scaled *10)",
        unit="V",
        required=False,
        default=0,
    )

    grid_uv2_time: int = block_field(
        offset=18,
        type=UInt16(),
        description="Grid undervoltage 2 trip time",
        unit="ms",
        required=False,
        default=0,
    )

    grid_ov1_value: int = block_field(
        offset=20,
        type=UInt16(),
        description="Grid overvoltage 1 threshold (V, scaled *10)",
        unit="V",
        required=False,
        default=0,
    )

    grid_ov1_time: int = block_field(
        offset=22,
        type=UInt16(),
        description="Grid overvoltage 1 trip time",
        unit="ms",
        required=False,
        default=0,
    )

    # Note: Additional 30+ fields at offsets 24+ include:
    # - Grid OV2 value/time
    # - Grid frequency limits (over/under)
    # - Power factor settings
    # - Anti-islanding settings
    # - TOU (time-of-use) rate schedules
    # - Battery reserve levels
    # - Self-consumption mode settings
    # - Grid sell-back limits
    #
    # Full implementation requires complete HomeStorageSettingsBean analysis.
    # See parseHomeStorageSettings (lines 13955-14700) for all setter calls.


BLOCK_40127_SCHEMA = HomeStorageSettingsBlock.to_schema()  # type: ignore[attr-defined]
