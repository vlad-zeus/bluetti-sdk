"""Block 2400 (CERT_SETTINGS) - Grid Certification Settings.

Source: docs/blocks/ADDITIONAL_BLOCKS.md (lines 144-161)
Method: parseCertSettings
Bean: DeviceCertSettings

Purpose: Grid compliance and certification parameters for different regions/standards.
"""

from dataclasses import dataclass

from ..protocol.v2.datatypes import UInt8, UInt16
from .declarative import block_field, block_schema


@block_schema(
    block_id=2400,
    name="CERT_SETTINGS",
    description="Grid compliance and certification parameters",
    min_length=10,
    protocol_version=2000,
    strict=False,
    verification_status="smali_verified",
)
@dataclass
class CertSettingsBlock:
    """Grid certification settings schema."""

    adv_enable: int = block_field(
        offset=0,
        type=UInt8(),
        description="Advanced certification enable",
        required=False,
        default=0,
    )

    grid_uv2_value: int = block_field(
        offset=1,
        type=UInt16(),
        description="Grid undervoltage 2 threshold",
        required=False,
        default=0,
    )

    grid_uv2_time: int = block_field(
        offset=3,
        type=UInt16(),
        description="Grid undervoltage 2 time threshold",
        unit="ms",
        required=False,
        default=0,
    )

    power_factor: int = block_field(
        offset=5,
        type=UInt16(),
        description="Power factor setting",
        required=False,
        default=0,
    )

    grid_cert_division: int = block_field(
        offset=7,
        type=UInt16(),
        description="Grid certification division/region code",
        required=False,
        default=0,
    )

    vvar_and_volt_watt_resp_mode: int = block_field(
        offset=9,
        type=UInt8(),
        description="Var/voltage and watt response mode",
        required=False,
        default=0,
    )


BLOCK_2400_SCHEMA = CertSettingsBlock.to_schema()  # type: ignore[attr-defined]
