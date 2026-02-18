"""Block 1100 - INV_BASE_INFO Declarative Schema

Declarative version of Block 1100 using the declarative schema API.
Inverter base information including ID, type, serial number, and software versions.

Usage:
    # Get generated BlockSchema
    schema = InvBaseInfoBlock.to_schema()

    # Register with parser
    parser.register_schema(schema)

    # Parse block
    parsed = parser.parse_block(1100, data)

    # Type-safe access (IDE autocomplete works!)
    inv_id = parsed.values['inv_id']
    inv_type = parsed.values['inv_type']
"""

from dataclasses import dataclass

from power_sdk.protocol.v2.datatypes import String, UInt8, UInt16, UInt32
from power_sdk.protocol.v2.transforms import minus
from .declarative import block_field, block_schema


@block_schema(
    block_id=1100,
    name="INV_BASE_INFO",
    description="Inverter base info (ID, type, SN, software versions)",
    min_length=62,  # Core fields including 6 software modules
    protocol_version=2000,
    schema_version="1.0.0",
    strict=False,  # Allow protocol-dependent fields
    verification_status="smali_verified",
)
@dataclass
class InvBaseInfoBlock:
    """Inverter base information for Elite V2 devices.

    Contains device identification, type information, and software version data.

    Note: Temperature field offsets vary by protocol version.
    Software version array contains 6 modules (fixed count).
    """

    # === Basic Device Information (1-24) ===
    inv_id: int = block_field(
        offset=1,
        type=UInt8(),
        required=True,
        description="Inverter ID number",
        default=0,
    )

    inv_type: str = block_field(
        offset=2,
        type=String(length=12),
        required=True,
        description="Inverter type string (ASCII)",
        default="",
    )

    inv_sn: str = block_field(
        offset=14,
        type=String(length=8),
        required=True,
        description="Inverter serial number",
        default="",
    )

    inv_power_type: int = block_field(
        offset=23,
        type=UInt8(),
        required=False,
        description="Inverter power type identifier",
        default=0,
    )

    software_number: int = block_field(
        offset=25,
        type=UInt8(),
        required=True,
        description="Number of software version entries (usually 6)",
        default=6,
    )

    # === Software Module 0 (26-31) ===
    software_0_module_id: int = block_field(
        offset=26,
        type=UInt16(),
        required=False,
        description="Software module 0 identifier",
        default=0,
    )

    software_0_version: int = block_field(
        offset=28,
        type=UInt32(),
        required=False,
        description="Software module 0 version number",
        default=0,
    )

    # === Software Module 1 (32-37) ===
    software_1_module_id: int = block_field(
        offset=32,
        type=UInt16(),
        required=False,
        description="Software module 1 identifier",
        default=0,
    )

    software_1_version: int = block_field(
        offset=34,
        type=UInt32(),
        required=False,
        description="Software module 1 version number",
        default=0,
    )

    # === Software Module 2 (38-43) ===
    software_2_module_id: int = block_field(
        offset=38,
        type=UInt16(),
        required=False,
        description="Software module 2 identifier",
        default=0,
    )

    software_2_version: int = block_field(
        offset=40,
        type=UInt32(),
        required=False,
        description="Software module 2 version number",
        default=0,
    )

    # === Software Module 3 (44-49) ===
    software_3_module_id: int = block_field(
        offset=44,
        type=UInt16(),
        required=False,
        description="Software module 3 identifier",
        default=0,
    )

    software_3_version: int = block_field(
        offset=46,
        type=UInt32(),
        required=False,
        description="Software module 3 version number",
        default=0,
    )

    # === Software Module 4 (50-55) ===
    software_4_module_id: int = block_field(
        offset=50,
        type=UInt16(),
        required=False,
        description="Software module 4 identifier",
        default=0,
    )

    software_4_version: int = block_field(
        offset=52,
        type=UInt32(),
        required=False,
        description="Software module 4 version number",
        default=0,
    )

    # === Software Module 5 (56-61) ===
    software_5_module_id: int = block_field(
        offset=56,
        type=UInt16(),
        required=False,
        description="Software module 5 identifier",
        default=0,
    )

    software_5_version: int = block_field(
        offset=58,
        type=UInt32(),
        required=False,
        description="Software module 5 version number",
        default=0,
    )

    # === Temperature Sensors (Protocol >= 2005) ===
    ambient_temp: int = block_field(
        offset=102,
        type=UInt16(),
        transform=[minus(40)],
        unit="°C",
        min_protocol_version=2005,
        required=False,
        description="Ambient temperature (0 = invalid)",
        default=0,
    )

    inv_max_temp: int = block_field(
        offset=104,
        type=UInt16(),
        transform=[minus(40)],
        unit="°C",
        min_protocol_version=2005,
        required=False,
        description="Inverter maximum temperature (0 = invalid)",
        default=0,
    )

    pv_dcdc_max_temp: int = block_field(
        offset=106,
        type=UInt16(),
        transform=[minus(40)],
        unit="°C",
        min_protocol_version=2005,
        required=False,
        description="PV DC-DC converter max temperature (0 = invalid)",
        default=0,
    )

    # === Fault Information (Protocol >= 2005) ===
    fault_code: int = block_field(
        offset=108,
        type=UInt16(),
        min_protocol_version=2005,
        required=False,
        description="Fault/error code",
        default=0,
    )

    # Note: For protocol versions < 2005, temperature fields are at different offsets
    # Protocol 2001-2004: workingTimeNumber at 97, devVoltageType at 99
    # Protocol < 2001: workingTimeNumber at 85, devVoltageType at 87
    # These are not included in this baseline schema


# Generate canonical BlockSchema object
BLOCK_1100_DECLARATIVE_SCHEMA = InvBaseInfoBlock.to_schema()  # type: ignore[attr-defined]
