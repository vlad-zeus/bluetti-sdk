"""Block 2200 (INV_ADV_SETTINGS) - Inverter Advanced Settings.

Source: docs/blocks/ADDITIONAL_BLOCKS.md (lines 119-141)
Method: parseInvAdvSettings
Bean: InvAdvancedSettings

Purpose: Advanced inverter configuration including grid parameters and limits.

SECURITY: Password-protected advanced settings. This block controls:
- Grid connection parameters and voltage/frequency limits
- Factory reset capability
- Grid feedback and impedance settings
- Advanced power management thresholds

CAUTION: Incorrect advanced settings may:
- Violate grid code compliance requirements
- Cause unstable grid synchronization or equipment damage
- Result in safety hazard or warranty void

Only modify with manufacturer authorization and proper grid engineering knowledge.
"""

from dataclasses import dataclass

from ..protocol.v2.datatypes import String, UInt8, UInt16
from ..protocol.v2.transforms import scale
from .declarative import block_field, block_schema


@block_schema(
    block_id=2200,
    name="INV_ADV_SETTINGS",
    description="Advanced inverter configuration and limits",
    min_length=27,
    protocol_version=2000,
    strict=False,
    verification_status="smali_verified",
)
@dataclass
class InvAdvSettingsBlock:
    """Inverter advanced settings schema."""

    adv_login_password: str = block_field(
        offset=0,
        type=String(length=8),
        description="Advanced settings password (8 bytes)",
        required=False,
        default="",
    )

    factory_reset: int = block_field(
        offset=8,
        type=UInt8(),
        description="Factory reset flag",
        required=False,
        default=0,
    )

    ctrl_grid: int = block_field(
        offset=9,
        type=UInt8(),
        description="Grid connection control",
        required=False,
        default=0,
    )

    # TODO(smali-verify): Gap between offset 9 and 11
    ctrl_feedback: int = block_field(
        offset=11,
        type=UInt8(),
        description="Grid feedback enable",
        required=False,
        default=0,
    )

    # TODO(smali-verify): Gap between offset 11 and 13
    inv_voltage: float = block_field(
        offset=13,
        type=UInt16(),
        transform=[scale(0.1)],
        description="Inverter output voltage",
        unit="V",
        required=False,
        default=0.0,
    )

    inv_freq: float = block_field(
        offset=15,
        type=UInt16(),
        transform=[scale(0.01)],
        description="Inverter output frequency",
        unit="Hz",
        required=False,
        default=0.0,
    )

    chg_max_voltage: float = block_field(
        offset=17,
        type=UInt16(),
        transform=[scale(0.1)],
        description="Max charging voltage",
        unit="V",
        required=False,
        default=0.0,
    )

    pv_chg_max_current: float = block_field(
        offset=19,
        type=UInt16(),
        transform=[scale(0.1)],
        description="PV max charging current",
        unit="A",
        required=False,
        default=0.0,
    )

    grid_max_power: int = block_field(
        offset=21,
        type=UInt16(),
        description="Grid max power",
        unit="W",
        required=False,
        default=0,
    )

    grid_max_current: float = block_field(
        offset=23,
        type=UInt16(),
        transform=[scale(0.1)],
        description="Grid max current",
        unit="A",
        required=False,
        default=0.0,
    )

    feedback_max_power: int = block_field(
        offset=25,
        type=UInt16(),
        description="Max feedback power to grid",
        unit="W",
        required=False,
        default=0,
    )


BLOCK_2200_SCHEMA = InvAdvSettingsBlock.to_schema()  # type: ignore[attr-defined]
