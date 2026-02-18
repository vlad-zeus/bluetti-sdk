"""Block 6100 - PACK_ITEM_INFO Declarative Schema

Declarative version of Block 6100 using the declarative schema API.
Individual battery pack detailed information including cell voltages and temperatures.

Usage:
    # Get generated BlockSchema
    schema = PackItemInfoBlock.to_schema()

    # Register with parser
    parser.register_schema(schema)

    # Parse block
    parsed = parser.parse_block(6100, data)

    # Type-safe access (IDE autocomplete works!)
    pack_id = parsed.values['pack_id']
    voltage = parsed.values['voltage']
"""

from dataclasses import dataclass

from power_sdk.protocol.v2.datatypes import String, UInt8, UInt16
from power_sdk.protocol.v2.transforms import minus, scale
from .declarative import block_field, block_schema


@block_schema(
    block_id=6100,
    name="PACK_ITEM_INFO",
    description="Battery pack detailed info (cell voltages, temps, protection)",
    min_length=160,  # Core fixed fields
    protocol_version=2000,
    schema_version="1.0.0",
    strict=False,  # Allow variable-length arrays
    verification_status="smali_verified",
)
@dataclass
class PackItemInfoBlock:
    """Individual battery pack detailed information for Elite V2 devices.

    Contains pack identification, electrical parameters, protection status,
    and cell-level data (voltages, temperatures).

    Note: This schema includes fixed fields only.
    Variable-length arrays (cell voltages, temps, BMU info) require
    additional parsing based on count fields.
    """

    # === Pack Identification (1-21) ===
    pack_id: int = block_field(
        offset=1,
        type=UInt8(),
        required=True,
        description="Pack ID number",
        default=0,
    )

    pack_type: str = block_field(
        offset=2,
        type=String(length=12),
        required=True,
        description="Pack type string (ASCII)",
        default="",
    )

    pack_sn: str = block_field(
        offset=14,
        type=String(length=8),
        required=True,
        description="Pack serial number",
        default="",
    )

    # === Electrical Parameters (22-27) ===
    voltage: float = block_field(
        offset=22,
        type=UInt16(),
        transform=[scale(0.01)],
        unit="V",
        required=True,
        description="Pack voltage",
        default=0.0,
    )

    current: float = block_field(
        offset=24,
        type=UInt16(),
        transform=[scale(0.1)],
        unit="A",
        required=True,
        description="Pack current",
        default=0.0,
    )

    # === State Information (27-31) ===
    pack_soc: int = block_field(
        offset=27,
        type=UInt8(),
        unit="%",
        required=True,
        description="Pack state of charge",
        default=0,
    )

    pack_soh: int = block_field(
        offset=29,
        type=UInt8(),
        unit="%",
        required=True,
        description="Pack state of health",
        default=100,
    )

    average_temp: int = block_field(
        offset=30,
        type=UInt16(),
        transform=[minus(40)],
        unit="°C",
        required=True,
        description="Average temperature",
        default=0,
    )

    # === Status Information (49-59) ===
    running_status: int = block_field(
        offset=49,
        type=UInt8(),
        required=False,
        description="Running status code",
        default=0,
    )

    charging_status: int = block_field(
        offset=51,
        type=UInt8(),
        required=False,
        description="Charging status code",
        default=0,
    )

    pack_cap_online: int = block_field(
        offset=59,
        type=UInt8(),
        required=False,
        description="Pack capacity online",
        default=0,
    )

    # === Cell and Sensor Counts (105-109) ===
    total_cell_cnt: int = block_field(
        offset=105,
        type=UInt8(),
        required=True,
        description="Total cell count",
        default=0,
    )

    ntc_cell_cnt: int = block_field(
        offset=107,
        type=UInt8(),
        required=True,
        description="NTC temperature sensor count",
        default=0,
    )

    bmu_cnt: int = block_field(
        offset=109,
        type=UInt8(),
        required=True,
        description="BMU (Battery Management Unit) count",
        default=0,
    )

    # === BMU Information (110-143) ===
    bmu_fault_bit: int = block_field(
        offset=110,
        type=UInt16(),
        required=False,
        description="BMU fault bits (bitmap)",
        default=0,
    )

    bmu_type: int = block_field(
        offset=143,
        type=UInt8(),
        required=False,
        description="BMU type identifier",
        default=0,
    )

    # === Protection/Alarm Status (88-139) ===
    # Note: These are multi-byte bitmaps, parsed separately
    # pack_protect (88-89): Pack charge protection (2 bytes)
    # pack_protect (90-91): Pack discharge protection (2 bytes)
    # pack_sys_err (92-99): Pack system error (6 bytes)
    # pack_high_volt_alarm (100-101): Pack high voltage alarm (2 bytes)
    # pack_protect2 (128-131): Pack protection status 2 (4 bytes)
    # pack_dcdc_alarm (134-135): Pack DC-DC converter alarm (2 bytes)

    dcdc_protect: int = block_field(
        offset=138,
        type=UInt16(),
        required=False,
        description="DC-DC converter protection status",
        default=0,
    )

    # === Firmware Information (156-159) ===
    fm_ver_diff: int = block_field(
        offset=156,
        type=UInt8(),
        required=False,
        description="Firmware version difference",
        default=0,
    )

    mcu_status: int = block_field(
        offset=157,
        type=UInt8(),
        required=False,
        description="MCU status",
        default=0,
    )

    pack_type_diff: int = block_field(
        offset=158,
        type=UInt8(),
        required=False,
        description="Pack type difference",
        default=0,
    )

    software_number: int = block_field(
        offset=159,
        type=UInt8(),
        required=False,
        description="Software number/count",
        default=0,
    )

    # Note: Variable-length arrays starting at offset 160+:
    # - software_list (variable, depends on software_number)
    # - fm_list (variable, offset depends on software_number)
    # - Cell voltages (parsed via PackSubPackInfo, variable length)
    # - Cell temperatures (parsed via PackSubPackInfo, variable length)
    # - BMU info array (parsed via parsePackBMUInfo, depends on bmu_cnt)
    # These require separate parsing logic and are not included in this baseline schema


# Generate canonical BlockSchema object
BLOCK_6100_DECLARATIVE_SCHEMA = PackItemInfoBlock.to_schema()  # type: ignore[attr-defined]
