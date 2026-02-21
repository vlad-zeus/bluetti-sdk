"""Block 1700 (METER_INFO) - CT Meter Information.

Source: ProtocolParserV2.reference lines 24757-25100 (parseInvMeterInfo)
Bean: InvMeterInfo
Purpose: Monitor grid import/export via CT clamps

NOTE: Float32 Encoding
All metering fields at offsets 26+ are stored as IEEE 754 Float32 bit patterns
(UInt32 raw integers). The reference uses bit32HexSwap + hexToFloat conversion:
    actual_value = struct.unpack('>f', struct.pack('>I', raw_uint32))[0]
These fields are intentionally kept as UInt32 (int) and suffixed with _raw_bits
to make the encoding explicit. Do NOT interpret them as numeric values directly.

reference-verified structure:
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

from ..protocol.datatypes import String, UInt16, UInt32
from .declarative import block_field, block_schema


@block_schema(
    block_id=1700,
    name="METER_INFO",
    description="CT meter readings for grid monitoring",
    min_length=138,
    strict=False,
    verification_status="partial",
)
@dataclass
class MeterInfoBlock:
    """CT meter information schema (partially verified).

    Float32 metering fields are stored as raw IEEE 754 bit patterns (UInt32).
    Apply struct.unpack('>f', struct.pack('>I', value)) to convert to float.
    """

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
        description=("Status bitfield (bits 0-1: status, bit 2: online_status)"),
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
    # Raw IEEE 754 bit patterns — apply struct.unpack('>f', struct.pack('>I', value))
    phase0_voltage_raw_bits: int = block_field(
        offset=26,
        type=UInt32(),
        description=(
            "Phase 0 voltage — Raw IEEE 754 Float32 bits — apply "
            "struct.unpack('>f', struct.pack('>I', value)) for actual voltage"
        ),
        required=False,
        default=0,
    )

    phase0_current_raw_bits: int = block_field(
        offset=30,
        type=UInt32(),
        description=(
            "Phase 0 current — Raw IEEE 754 Float32 bits — apply "
            "struct.unpack('>f', struct.pack('>I', value)) for actual current"
        ),
        required=False,
        default=0,
    )

    phase0_active_power_raw_bits: int = block_field(
        offset=34,
        type=UInt32(),
        description=(
            "Phase 0 active power — Raw IEEE 754 Float32 bits — apply "
            "struct.unpack('>f', struct.pack('>I', value)) for actual power"
        ),
        unit="W",
        required=False,
        default=0,
    )

    # Aggregate values (offset 98+)
    total_active_power_raw_bits: int = block_field(
        offset=114,
        type=UInt32(),
        description=(
            "Total active power — Raw IEEE 754 Float32 bits — apply "
            "struct.unpack('>f', struct.pack('>I', value)) for actual power"
        ),
        unit="W",
        required=False,
        default=0,
    )

    frequency_raw_bits: int = block_field(
        offset=130,
        type=UInt32(),
        description=(
            "Grid frequency — Raw IEEE 754 Float32 bits — apply "
            "struct.unpack('>f', struct.pack('>I', value)) for actual frequency"
        ),
        unit="Hz",
        required=False,
        default=0,
    )

    total_import_energy_raw_bits: int = block_field(
        offset=134,
        type=UInt32(),
        description=(
            "Total import energy — Raw IEEE 754 Float32 bits — apply "
            "struct.unpack('>f', struct.pack('>I', value)) for actual energy"
        ),
        unit="kWh",
        required=False,
        default=0,
    )

    # Note: Full Float32 parsing requires hexToFloat conversion
    # Phase 0 item: offsets 26-49 (voltage=26, current=30, active_power=34, ...)
    # Phase 1 item: offsets 50-73; Phase 2 item: offsets 74-97
    # Full aggregate values at offsets 98-137


BLOCK_1700_SCHEMA = MeterInfoBlock.to_schema()  # type: ignore[attr-defined]
