"""Block 12161 (IOT_ENABLE_INFO) - IOT Module Enable Status.

Source: ProtocolParserV2.smali lines 15526-15800 (parseIOTEnableInfo)
Bean: IoTCtrlStatus
Purpose: IOT module operational status and control flags

Smali-verified structure:
- Bytes 0-1: Control flags group 1 (hex string converted to bit array)
  - Bit 0: WifiSTA enable
  - Bit 6: Enable4G
- Bytes 2-3: Control flags group 2 (hex string converted to bit array)
  - Bit 0: Ethernet enable
  - Bit 1: WiFi mesh enable
  - Bit 3: Default mode
  - Bit 5: BLE match mode

Note: Values are bit-packed. Application code should use hexStrToEnableList
to extract individual bit flags from the raw UInt16 values.
"""

from dataclasses import dataclass

from ..protocol.v2.datatypes import UInt16
from .declarative import block_field, block_schema


@block_schema(
    block_id=12161,
    name="IOT_ENABLE_INFO",
    description="IOT module enable and control status (bit-packed)",
    min_length=4,
    protocol_version=2000,
    strict=False,
    verification_status="smali_verified",
)
@dataclass
class IotEnableInfoBlock:
    """IOT enable status schema (smali-verified bit-packed format)."""

    # Control flags group 1 (bytes 0-1)
    control_flags_1: int = block_field(
        offset=0,
        type=UInt16(),
        description=(
            "Control flags group 1 (bit-packed: "
            "bit0=WifiSTA, bit6=Enable4G)"
        ),
        required=True,
        default=0,
    )

    # Control flags group 2 (bytes 2-3)
    control_flags_2: int = block_field(
        offset=2,
        type=UInt16(),
        description=(
            "Control flags group 2 (bit-packed: "
            "bit0=EthernetEnable, bit1=WifiMeshEnable, "
            "bit3=DefaultMode, bit5=BleMatchMode)"
        ),
        required=True,
        default=0,
    )


BLOCK_12161_SCHEMA = IotEnableInfoBlock.to_schema()  # type: ignore[attr-defined]
