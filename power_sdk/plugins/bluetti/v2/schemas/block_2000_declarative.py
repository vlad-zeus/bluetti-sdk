"""Block 2000 (INV_BASE_SETTINGS) - Inverter Base Settings.

Source: docs/blocks/ADDITIONAL_BLOCKS.md (lines 89-115)
Method: parseInvBaseSettings
Bean: InvBaseSettings

Purpose: Core inverter control settings including working mode, charging, and eco mode.

CAUTION: This block controls critical inverter operating parameters. Incorrect
working mode, grid charging, or eco mode settings may:
- Violate grid connection requirements or safety standards
- Cause equipment damage or unstable operation
- Lead to inefficient energy management or battery degradation

Only modify with proper understanding of inverter operation and grid regulations.
"""

from dataclasses import dataclass

from ..protocol.datatypes import UInt8, UInt16
from .declarative import block_field, block_schema


@block_schema(
    block_id=2000,
    name="INV_BASE_SETTINGS",
    description="Core inverter control settings",
    min_length=35,
    protocol_version=2000,
    strict=False,
    verification_status="smali_verified",
)
@dataclass
class InvBaseSettingsBlock:
    """Inverter base settings schema."""

    inv_address: int = block_field(
        offset=0,
        type=UInt8(),
        description="Inverter modbus address",
        required=False,
        default=0,
    )

    working_mode: int = block_field(
        offset=1,
        type=UInt8(),
        description="Operating mode selector",
        required=True,
        default=0,
    )

    # TODO(smali-verify): Gap between offset 1 and 5
    ctrl_led: int = block_field(
        offset=5,
        type=UInt8(),
        description="LED control enable",
        required=False,
        default=0,
    )

    # TODO(smali-verify): Gap between offset 5 and 7
    ctrl_grid_chg: int = block_field(
        offset=7,
        type=UInt8(),
        description="Grid charging enable",
        required=False,
        default=0,
    )

    # TODO(smali-verify): Gap between offset 7 and 9
    ctrl_pv: int = block_field(
        offset=9,
        type=UInt8(),
        description="PV input enable",
        required=False,
        default=0,
    )

    # TODO(smali-verify): Gap between offset 9 and 11
    ctrl_inverter: int = block_field(
        offset=11,
        type=UInt8(),
        description="Inverter enable",
        required=False,
        default=0,
    )

    # TODO(smali-verify): Gap between offset 11 and 13
    ctrl_ac: int = block_field(
        offset=13,
        type=UInt8(),
        description="AC output enable",
        required=False,
        default=0,
    )

    # TODO(smali-verify): Gap between offset 13 and 15
    ctrl_dc: int = block_field(
        offset=15,
        type=UInt8(),
        description="DC output enable",
        required=False,
        default=0,
    )

    # TODO(smali-verify): Gap between offset 15 and 19
    dc_eco_ctrl: int = block_field(
        offset=19,
        type=UInt8(),
        description="DC ECO mode enable",
        required=False,
        default=0,
    )

    # TODO(smali-verify): Gap between offset 19 and 21
    dc_eco_off_time: int = block_field(
        offset=21,
        type=UInt16(),
        description="DC ECO off delay",
        unit="min",
        required=False,
        default=0,
    )

    dc_eco_power: int = block_field(
        offset=23,
        type=UInt16(),
        description="DC ECO power threshold",
        unit="W",
        required=False,
        default=0,
    )

    ac_eco_ctrl: int = block_field(
        offset=25,
        type=UInt8(),
        description="AC ECO mode enable",
        required=False,
        default=0,
    )

    # TODO(smali-verify): Gap between offset 25 and 27
    ac_eco_off_time: int = block_field(
        offset=27,
        type=UInt16(),
        description="AC ECO off delay",
        unit="min",
        required=False,
        default=0,
    )

    ac_eco_power: int = block_field(
        offset=29,
        type=UInt16(),
        description="AC ECO power threshold",
        unit="W",
        required=False,
        default=0,
    )

    charging_mode: int = block_field(
        offset=31,
        type=UInt8(),
        description="Charging mode selector",
        required=False,
        default=0,
    )

    # TODO(smali-verify): Gap between offset 31 and 33
    power_lifting_mode: int = block_field(
        offset=33,
        type=UInt8(),
        description="Power lifting mode selector",
        required=False,
        default=0,
    )


BLOCK_2000_SCHEMA = InvBaseSettingsBlock.to_schema()  # type: ignore[attr-defined]
