"""Block 15750 (DC_HUB_SETTINGS) - DC Hub Configuration Settings.

Source: ProtocolParserV2.smali lines 5224-5356 (dcHubSettingsParse)
Bean: DCHUBSettings
Purpose: DC Hub enable/disable and voltage configuration

Smali-verified structure:
- Offset 0-1: Enable flags (bit-packed: dcEnable at bit 0,
              switchRecoveryEnable at bit 1)
- Offset 0: DC voltage setting (raw UInt8 value)

Related blocks:
- 0x3D54 (15700): DC Hub info
"""

from dataclasses import dataclass

from ..protocol.v2.datatypes import UInt8, UInt16
from .declarative import block_field, block_schema


@block_schema(
    block_id=15750,
    name="DC_HUB_SETTINGS",
    description="DC Hub configuration settings (smali-verified)",
    min_length=2,
    protocol_version=2000,
    strict=False,
    verification_status="inferred",
)
@dataclass
class DCHubSettingsBlock:
    """DC Hub settings schema (smali-verified).

    Field extraction:
    - dc_enable: Extract bit 0 from enable_flags using hexStrToEnableList
    - switch_recovery_enable: Extract bit 1 from enable_flags using hexStrToEnableList
    - dc_voltage_set: Raw UInt8 value from offset 0
    """

    enable_flags: int = block_field(
        offset=0,
        type=UInt16(),
        description=(
            "Bit-packed enable flags "
            "(bit 0: dcEnable, bit 1: switchRecoveryEnable)"
        ),
        required=True,
        default=0,
    )
    dc_voltage_set: int = block_field(
        offset=0,
        type=UInt8(),
        description="DC voltage setting (raw value)",
        required=True,
        default=0,
    )


# Export schema instance
BLOCK_15750_SCHEMA = DCHubSettingsBlock.to_schema()  # type: ignore[attr-defined]
