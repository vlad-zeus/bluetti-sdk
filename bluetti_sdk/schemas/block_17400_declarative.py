"""Block 17400 (ATS_EVENT_EXT) - AT1 Transfer Switch Extended Settings.

Source: ProtocolParserV2.smali switch case (0x43f8 -> sswitch_a)
Related: ProtocolAddrV2.smali defines AT1_SETTINGS_1 at 0x43f8
Block Type: EVENT (no dedicated parse method)
Purpose: AT1 transfer switch advanced configuration settings

Structure (PROVISIONAL):
- Min length from smali: 91 bytes (0x5b)
- Likely contains: grid enable flags, transfer mode, voltage/frequency limits
- Related to Block 17000 (ATS_INFO) and 17100 (AT1_BASE_INFO)

CAUTION: This block controls AT1 automatic transfer switch settings. Incorrect
configuration may:
- Result in improper grid/generator switching behavior
- Violate electrical code requirements for transfer switches
- Cause power interruption or equipment damage
- Lead to unsafe backfeed conditions if not properly configured

Only modify with proper understanding of transfer switch operation and local codes.

TODO(smali-verify): Complete field mapping when AT1 device available.
Requires reverse engineering of AT1Settings bean or actual device testing.
"""

from dataclasses import dataclass

from ..protocol.v2.datatypes import UInt8, UInt16
from .declarative import block_field, block_schema


@block_schema(
    block_id=17400,
    name="ATS_EVENT_EXT",
    description="AT1 transfer switch extended settings (provisional - EVENT block)",
    min_length=91,
    protocol_version=2000,
    strict=False,
)
@dataclass
class ATSEventExtBlock:
    """AT1 transfer switch extended settings schema (provisional baseline).

    This block follows EVENT pattern without dedicated parse method.
    Field mapping is provisional pending actual AT1 device testing.

    CAUTION: Transfer switch control - verify electrical code compliance.
    """

    grid_enable_flags: int = block_field(
        offset=0,
        type=UInt16(),
        description="Grid input enable/control flags (TODO: verify bit mapping)",
        required=False,
        default=0,
    )

    transfer_mode: int = block_field(
        offset=2,
        type=UInt8(),
        description="Transfer mode selector (TODO: verify mode enum)",
        required=False,
        default=0,
    )

    grid_voltage_low_limit: int = block_field(
        offset=4,
        type=UInt16(),
        unit="0.1V",
        description="Grid undervoltage transfer threshold (TODO: verify offset)",
        required=False,
        default=0,
    )

    grid_voltage_high_limit: int = block_field(
        offset=6,
        type=UInt16(),
        unit="0.1V",
        description="Grid overvoltage transfer threshold (TODO: verify offset)",
        required=False,
        default=0,
    )

    grid_frequency_low_limit: int = block_field(
        offset=8,
        type=UInt16(),
        unit="0.01Hz",
        description="Grid underfrequency transfer threshold (TODO: verify offset)",
        required=False,
        default=0,
    )

    grid_frequency_high_limit: int = block_field(
        offset=10,
        type=UInt16(),
        unit="0.01Hz",
        description="Grid overfrequency transfer threshold (TODO: verify offset)",
        required=False,
        default=0,
    )

    transfer_delay_time: int = block_field(
        offset=12,
        type=UInt16(),
        unit="ms",
        description="Transfer delay time (TODO: verify offset)",
        required=False,
        default=0,
    )

    reconnect_delay_time: int = block_field(
        offset=14,
        type=UInt16(),
        unit="ms",
        description="Reconnect delay after grid restore (TODO: verify offset)",
        required=False,
        default=0,
    )

    priority_mode: int = block_field(
        offset=16,
        type=UInt8(),
        description="Source priority mode (grid/battery) (TODO: verify offset)",
        required=False,
        default=0,
    )

    auto_restart_enable: int = block_field(
        offset=17,
        type=UInt8(),
        description="Auto restart after grid restore (TODO: verify offset)",
        required=False,
        default=0,
    )

    max_transfer_current: int = block_field(
        offset=18,
        type=UInt16(),
        unit="0.1A",
        description="Maximum transfer current limit (TODO: verify offset)",
        required=False,
        default=0,
    )


# Export schema instance
BLOCK_17400_SCHEMA = ATSEventExtBlock.to_schema()  # type: ignore[attr-defined]
