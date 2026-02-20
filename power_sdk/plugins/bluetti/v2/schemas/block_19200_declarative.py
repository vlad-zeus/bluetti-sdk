"""Block 19200 (SCHEDULED_BACKUP) - Scheduled Backup Power Settings.

Source: ProtocolParserV2.reference lines 31605-31900 (parseScheduledBackup)
Bean: DeviceScheduledBackup
Purpose: Configure scheduled backup power operation

reference-verified structure:
- Offsets 0-1: Enable/config flags (UInt16, bit 0-1 enable, bits 2+ reserved)
- Offsets 2-3: Mode configuration (UInt16)
- Offsets 4+: Array of 4 backup schedules (8 bytes each):
  - Each schedule (i * 8 bytes, where i = 0-3):
    - Offset +0 to +1: Type/enable (UInt16, 4-bit field per schedule)
    - Offset +2 to +5: Start time (UInt32 timestamp, bit32 format)
    - Offset +6 to +9: End time (UInt32 timestamp, bit32 format)

Note: This schema provides first 2 schedules as baseline.
Full 4-schedule parsing requires dynamic array support.
"""

from dataclasses import dataclass

from ..protocol.datatypes import UInt16, UInt32
from .declarative import block_field, block_schema


@block_schema(
    block_id=19200,
    name="SCHEDULED_BACKUP",
    description="Scheduled backup power configuration (reference-verified)",
    min_length=38,
    protocol_version=2000,
    strict=False,
    verification_status="verified_reference",
)
@dataclass
class ScheduledBackupBlock:
    """Scheduled backup settings schema (reference-verified)."""

    # Global enable/config (offsets 0-3)
    enable_flags: int = block_field(
        offset=0,
        type=UInt16(),
        description="Enable flags (bit 0-1: backup enable, bits 2+: reserved)",
        required=True,
        default=0,
    )

    mode_config: int = block_field(
        offset=2,
        type=UInt16(),
        description=(
            "Packed per-schedule type/enable flags "
            "(4 bits per schedule for 4 schedules)"
        ),
        required=True,
        default=0,
    )

    # Schedule 0 (offsets 6-13)
    schedule0_start_time: int = block_field(
        offset=6,
        type=UInt32(),
        description="Schedule 0: Start time (bit32 timestamp)",
        required=False,
        default=0,
    )

    schedule0_end_time: int = block_field(
        offset=10,
        type=UInt32(),
        description="Schedule 0: End time (bit32 timestamp)",
        required=False,
        default=0,
    )

    # Schedule 1 (offsets 14-21)
    schedule1_start_time: int = block_field(
        offset=14,
        type=UInt32(),
        description="Schedule 1: Start time (bit32 timestamp)",
        required=False,
        default=0,
    )

    schedule1_end_time: int = block_field(
        offset=18,
        type=UInt32(),
        description="Schedule 1: End time (bit32 timestamp)",
        required=False,
        default=0,
    )

    # Schedule 2 (offsets 22-29)
    schedule2_start_time: int = block_field(
        offset=22,
        type=UInt32(),
        description="Schedule 2: Start time (bit32 timestamp)",
        required=False,
        default=0,
    )

    schedule2_end_time: int = block_field(
        offset=26,
        type=UInt32(),
        description="Schedule 2: End time (bit32 timestamp)",
        required=False,
        default=0,
    )

    # Schedule 3 (offsets 30-37)
    schedule3_start_time: int = block_field(
        offset=30,
        type=UInt32(),
        description="Schedule 3: Start time (bit32 timestamp)",
        required=False,
        default=0,
    )

    schedule3_end_time: int = block_field(
        offset=34,
        type=UInt32(),
        description="Schedule 3: End time (bit32 timestamp)",
        required=False,
        default=0,
    )

    # Note: Type/enable field at offset 4-5 encodes 4-bit enable per schedule
    # using bit shifts (schedule_i_type = (value >> (i*4)) & 0xF)
    # Application layer should decode using parseScheduledBackup logic


BLOCK_19200_SCHEMA = ScheduledBackupBlock.to_schema()  # type: ignore[attr-defined]
