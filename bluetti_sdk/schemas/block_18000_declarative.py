"""Block 18000 (EPAD_INFO) - Energy Pad Base Information.

Source: ProtocolParserV2.smali switch case (0x4650 -> sswitch_9)
Related: ProtocolAddrV2.smali defines EPAD_BASE_INFO at 0x4650
Block Type: EVENT (no dedicated parse method)
Purpose: Energy Pad (EPAD) device comprehensive status monitoring

Structure (PROVISIONAL):
- Min length from smali: 2019 bytes (0x7e3) - LARGE payload
- Special conditional check: if (v1 >= 0x7e3)
- Likely contains: extensive device diagnostics, multi-port monitoring, history data
- EPAD appears to be a complex expansion device with many monitored parameters

NOTE: This is an exceptionally large block (2KB+), suggesting it contains
historical data, event logs, or extensive multi-channel monitoring.
Field mapping requires actual EPAD device for reverse engineering.

TODO(smali-verify): EPAD device required for complete mapping.
Large payload suggests array structures or historical data logs.
Baseline schema provides minimal field coverage.
"""

from dataclasses import dataclass

from ..protocol.v2.datatypes import String, UInt8, UInt16, UInt32
from .declarative import block_field, block_schema


@block_schema(
    block_id=18000,
    name="EPAD_INFO",
    description="Energy Pad base information (provisional - EVENT block, 2KB payload)",
    min_length=2019,
    protocol_version=2000,
    strict=False,
)
@dataclass
class EPadInfoBlock:
    """Energy Pad information schema (minimal baseline).

    This block follows EVENT pattern without dedicated parse method.
    Exceptionally large payload (2019 bytes) indicates complex data structure.

    WARNING: Field offsets are highly speculative due to no parse method.
    Requires actual EPAD device testing for accurate mapping.
    """

    # Device identification (offsets 0-23)
    model: str = block_field(
        offset=0,
        type=String(length=12),
        description="EPAD model identifier (TODO: verify offset)",
        required=False,
        default="",
    )

    serial_number: str = block_field(
        offset=12,
        type=String(length=12),
        description="EPAD serial number (TODO: verify offset and length)",
        required=False,
        default="",
    )

    software_version: str = block_field(
        offset=24,
        type=String(length=8),
        description="Firmware version (TODO: verify offset and length)",
        required=False,
        default="",
    )

    # Status and operational data (offsets 32+)
    device_status: int = block_field(
        offset=32,
        type=UInt16(),
        description="Device status flags (TODO: verify offset and bit mapping)",
        required=False,
        default=0,
    )

    operating_mode: int = block_field(
        offset=34,
        type=UInt8(),
        description="Operating mode selector (TODO: verify offset)",
        required=False,
        default=0,
    )

    total_power: int = block_field(
        offset=36,
        type=UInt32(),
        unit="W",
        description="Total power throughput (TODO: verify offset)",
        required=False,
        default=0,
    )

    total_energy: int = block_field(
        offset=40,
        type=UInt32(),
        unit="Wh",
        description="Total energy transferred (TODO: verify offset)",
        required=False,
        default=0,
    )

    # Port/channel monitoring (offsets 44+)
    channel_count: int = block_field(
        offset=44,
        type=UInt8(),
        description="Number of active channels (TODO: verify offset)",
        required=False,
        default=0,
    )

    error_code: int = block_field(
        offset=45,
        type=UInt16(),
        description="Current error/fault code (TODO: verify offset)",
        required=False,
        default=0,
    )

    # NOTE: Remaining ~1970 bytes likely contain:
    # - Historical data arrays
    # - Per-channel detailed monitoring
    # - Event logs or fault history
    # - Extended configuration data
    # Requires EPAD device testing to map accurately


# Export schema instance
BLOCK_18000_SCHEMA = EPadInfoBlock.to_schema()  # type: ignore[attr-defined]
