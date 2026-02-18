"""Device models and state."""

from .device import BatteryPackInfo, Device, GridInfo, HomeData

# Backward-compatible alias
V2Device = Device

__all__ = [
    "BatteryPackInfo",
    "Device",
    "GridInfo",
    "HomeData",
    "V2Device",  # deprecated alias -- use Device
]
