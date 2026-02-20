"""Block 15750 (DC_HUB_SETTINGS) - DC Hub Configuration Settings.

Source: ProtocolParserV2.reference lines 5224-5356 (dcHubSettingsParse)
Bean: DCHUBSettings
Purpose: DC Hub enable/disable and voltage configuration

PROVISIONAL — offset conflict unresolved:
  Both enable_flags (UInt16, 2 bytes) and dc_voltage_set (UInt8, 1 byte) are
  declared at offset 0. A UInt16 and a UInt8 at the same offset are mutually
  exclusive interpretations of the same memory location. The reference source
  is ambiguous: dcHubSettingsParse appears to extract these via different code
  paths, but whether offset 0 encodes a combined bitfield (UInt16) with the
  lower byte doubling as the voltage setting, or whether they are separate
  register-file entries, is unclear without a live device capture.

  Do NOT treat this schema as "fully verified". Do NOT rely on dc_voltage_set
  for production use until a live capture confirms the actual byte layout.

Related blocks:
- 0x3D54 (15700): DC Hub info
"""

from dataclasses import dataclass

from ..protocol.datatypes import UInt8, UInt16
from .declarative import block_field, block_schema


@block_schema(
    block_id=15750,
    name="DC_HUB_SETTINGS",
    description=(
        "DC Hub configuration settings (PROVISIONAL — offset 0 layout ambiguous)"
    ),
    min_length=2,
    protocol_version=2000,
    strict=False,
    verification_status="partial",
)
@dataclass
class DCHubSettingsBlock:
    """DC Hub settings schema (PROVISIONAL — offset 0 layout unresolved).

    Field extraction:
    - dc_enable: Extract bit 0 from enable_flags using hexStrToEnableList
    - switch_recovery_enable: Extract bit 1 from enable_flags using hexStrToEnableList
    - dc_voltage_set: Raw UInt8 value from offset 0

    WARNING: enable_flags (UInt16) and dc_voltage_set (UInt8) share offset=0.
    Their co-existence at the same offset is ambiguous in the reference source.
    Pending live device capture to determine actual register layout.
    """

    # PROVISIONAL: UInt16 at offset 0 — may conflict with dc_voltage_set below
    enable_flags: int = block_field(
        offset=0,
        type=UInt16(),
        description=(
            "Bit-packed enable flags (bit 0: dcEnable, bit 1: switchRecoveryEnable)"
            " — PROVISIONAL, offset conflicts with dc_voltage_set"
        ),
        required=True,
        default=0,
    )
    # PROVISIONAL: UInt8 at offset 0 — may overlap with enable_flags above
    dc_voltage_set: int = block_field(
        offset=0,
        type=UInt8(),
        description=(
            "DC voltage setting (raw value)"
            " — PROVISIONAL, offset conflicts with enable_flags"
        ),
        required=True,
        default=0,
    )


# Export schema instance
BLOCK_15750_SCHEMA = DCHubSettingsBlock.to_schema()  # type: ignore[attr-defined]
