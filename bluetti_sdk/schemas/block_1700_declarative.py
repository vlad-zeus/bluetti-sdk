"""Block 1700 (METER_INFO) - CT Meter Information.

Source: ProtocolParserV2.smali lines 24757-25100 (parseInvMeterInfo)
Bean: InvMeterInfo
Purpose: Monitor grid import/export via CT clamps

Smali-verified structure:
- Offset 0-11: Meter model (12 bytes ASCII)
- Offset 12-19: Meter serial number (8 bytes)
- Offset 20-21: Status and online status (bitfield)
- Offset 22-25: System time (UInt32)
- Offset 26+: Array of 3 phase meter items (12 bytes each, Float32 values):
  - Each item: voltage, current, active_power, reactive_power,
    apparent_power, power_factor (all Float32)
- Offset 98+: Aggregate values (all Float32):
  - Average voltage, line current, unbalance, total power, etc.
  - Total import/export energy (Float32)

Note: Float values use bit32HexSwap + hexToFloat conversion.
This schema provides key fields. Full array parsing requires dynamic support.
"""

from dataclasses import dataclass

from ..protocol.v2.datatypes import String, UInt16, UInt32
from .declarative import block_field, block_schema


@block_schema(
    block_id=1700,
    name="METER_INFO",
    description="CT meter readings for grid monitoring",
    min_length=138,
    protocol_version=2000,
    strict=False,
)
@dataclass
class MeterInfoBlock:
    """CT meter information schema (smali-verified)."""

    model: str = block_field(
        offset=0,
        type=String(length=12),
        description="Meter model (12 bytes ASCII)",
        required=True,
        default="",
    )

    sn: str = block_field(
        offset=12,
        type=String(length=8),
        description="Meter serial number (8 bytes)",
        required=True,
        default="",
    )

    status: int = block_field(
        offset=20,
        type=UInt16(),
        description=(
            "Status bitfield (bits 0-1: status, bit 2: online_status)"
        ),
        required=True,
        default=0,
    )

    sys_time: int = block_field(
        offset=22,
        type=UInt32(),
        description="System timestamp",
        required=False,
        default=0,
    )

    # Phase 0 item (offset 26-37, each field is Float32 = 4 bytes)
    # Note: Float values require bit32HexSwap + hexToFloat conversion
    phase0_voltage_raw: int = block_field(
        offset=26,
        type=UInt32(),
        description="Phase 0 voltage (Float32 raw, needs conversion)",
        required=False,
        default=0,
    )

    phase0_current_raw: int = block_field(
        offset=38,
        type=UInt32(),
        description="Phase 0 current (Float32 raw, needs conversion)",
        required=False,
        default=0,
    )

    phase0_active_power_raw: int = block_field(
        offset=50,
        type=UInt32(),
        description="Phase 0 active power (Float32 raw, needs conversion)",
        unit="W",
        required=False,
        default=0,
    )

    # Aggregate values (offset 98+)
    total_active_power_raw: int = block_field(
        offset=114,
        type=UInt32(),
        description="Total active power (Float32 raw, needs conversion)",
        unit="W",
        required=False,
        default=0,
    )

    frequency_raw: int = block_field(
        offset=130,
        type=UInt32(),
        description="Grid frequency (Float32 raw, needs conversion)",
        unit="Hz",
        required=False,
        default=0,
    )

    total_import_energy_raw: int = block_field(
        offset=134,
        type=UInt32(),
        description=(
            "Total import energy (Float32 raw, needs conversion)"
        ),
        unit="kWh",
        required=False,
        default=0,
    )

    # Note: Full Float32 parsing requires hexToFloat conversion
    # Phase 1 and 2 items at offsets 38 and 50
    # Full aggregate values at offsets 98-137


BLOCK_1700_SCHEMA = MeterInfoBlock.to_schema()  # type: ignore[attr-defined]
