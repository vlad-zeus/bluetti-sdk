"""Block 17100 (AT1_BASE_INFO) - AT1 Transfer Switch Base Information.

Source: ProtocolParserV2.smali switch case (0x42cc -> sswitch_b)
Related: Block 17000 (ATS_INFO) provides basic ATS identification
Block Type: EVENT (no dedicated parse method)
Purpose: AT1 transfer switch extended device information and status

Structure (PROVISIONAL):
- Min length from smali: 127 bytes (const 0x7f)
- Likely contains: detailed status, grid monitoring, switching logic state
- Related to AT1_SETTINGS (17400) and AT1 timer blocks (19365-19485)

Note: This is a provisional baseline implementation. Full field mapping requires:
- Actual AT1 device for testing
- Event payload capture and analysis
- Bean structure verification (AT1Info/AT1BaseInfo class)
- Comparison with ATS_INFO (17000) to identify additional fields

TODO(smali-verify): Complete field mapping when AT1 device available
"""

from dataclasses import dataclass

from ..protocol.v2.datatypes import String, UInt8, UInt16, UInt32
from .declarative import block_field, block_schema


@block_schema(
    block_id=17100,
    name="AT1_BASE_INFO",
    description="AT1 transfer switch base information (provisional - EVENT block)",
    min_length=127,
    protocol_version=2000,
    strict=False,
)
@dataclass
class AT1BaseInfoBlock:
    """AT1 base information schema (provisional baseline).

    This block follows EVENT pattern without dedicated parse method.
    Field mapping is provisional pending actual device testing.

    Extended from ATS_INFO (17000) with additional AT1-specific fields.
    """

    model: str = block_field(
        offset=0,
        type=String(length=12),
        description="AT1 device model name (ASCII)",
        required=False,
        default="",
    )
    serial_number: str = block_field(
        offset=12,
        type=String(length=8),
        description="AT1 device serial number",
        required=False,
        default="",
    )
    software_type: int = block_field(
        offset=21,
        type=UInt8(),
        description="Software/firmware type identifier",
        required=False,
        default=0,
    )
    software_version: int = block_field(
        offset=22,
        type=UInt32(),
        description="Software/firmware version number",
        required=False,
        default=0,
    )
    grid_voltage: int = block_field(
        offset=26,
        type=UInt16(),
        unit="V",
        description="Grid voltage monitoring (TODO: verify offset and scale)",
        required=False,
        default=0,
    )
    grid_frequency: int = block_field(
        offset=28,
        type=UInt16(),
        unit="Hz",
        description="Grid frequency monitoring (TODO: verify offset and scale)",
        required=False,
        default=0,
    )
    transfer_status: int = block_field(
        offset=30,
        type=UInt8(),
        description="Transfer switch status (TODO: verify enum values)",
        required=False,
        default=0,
    )
    transfer_mode: int = block_field(
        offset=31,
        type=UInt8(),
        description="Transfer operation mode (TODO: verify enum values)",
        required=False,
        default=0,
    )
    status_flags: int = block_field(
        offset=32,
        type=UInt16(),
        description="Extended status/error flags (TODO: verify bit mapping)",
        required=False,
        default=0,
    )


# Export schema instance
BLOCK_17100_SCHEMA = AT1BaseInfoBlock.to_schema()  # type: ignore[attr-defined]
