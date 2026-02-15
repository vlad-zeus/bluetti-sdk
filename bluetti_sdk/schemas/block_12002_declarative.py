"""Block 12002 (IOT_WIFI_SETTINGS) - IOT WiFi Configuration.

Source: docs/blocks/ADDITIONAL_BLOCKS.md (lines 203-224)
Method: parseIOTSettingsInfo
Bean: IOTSettingsInfo

Purpose: WiFi configuration for IOT module.

WARNING: Contains WiFi credentials - handle securely!

Format Notes:
- SSID/Password length depends on WifiPasswordH32BEnable flag
- If H32BEnable=1: uses 96-byte encoding
- If H32BEnable=0: uses 64-byte encoding
- This schema uses conservative 64-byte allocation
"""

from dataclasses import dataclass

from ..protocol.v2.datatypes import String, UInt8
from .declarative import block_field, block_schema


@block_schema(
    block_id=12002,
    name="IOT_WIFI_SETTINGS",
    description="WiFi configuration for IOT module",
    min_length=98,
    protocol_version=2000,
    strict=False,
)
@dataclass
class IotWifiSettingsBlock:
    """IOT WiFi settings schema."""

    wifi_ssid: str = block_field(
        offset=0,
        type=String(length=64),
        description="WiFi SSID (variable length, 64 or 96 bytes)",
        required=True,
        default="",
    )

    # TODO(smali-verify): Actual offset depends on WifiPasswordH32BEnable
    wifi_password: str = block_field(
        offset=64,
        type=String(length=32),
        description="WiFi password (hex-encoded, variable length)",
        required=False,
        default="",
    )

    wifi_no_password_enable: int = block_field(
        offset=96,
        type=UInt8(),
        description="Open WiFi (no password) enable",
        required=False,
        default=0,
    )

    wifi_password_h32b_enable: int = block_field(
        offset=97,
        type=UInt8(),
        description="Use 32-byte hex password encoding",
        required=False,
        default=0,
    )


BLOCK_12002_SCHEMA = IotWifiSettingsBlock.to_schema()  # type: ignore[attr-defined]
