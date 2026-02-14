"""Bluetti SDK - Official Python SDK for Bluetti Elite V2 Devices

This SDK provides a clean, type-safe interface for interacting with
Bluetti Elite V2 power stations via MQTT.

Quick Start:
    >>> from bluetti_sdk import BluettiClient, MQTTTransport, MQTTConfig, get_device_profile
    >>>
    >>> config = MQTTConfig(
    ...     device_sn="2345EB200xxxxxxx",
    ...     pfx_cert=cert_bytes,
    ...     cert_password="password"
    ... )
    >>>
    >>> transport = MQTTTransport(config)
    >>> profile = get_device_profile("EL100V2")
    >>> client = BluettiClient(transport, profile)
    >>> client.connect()
    >>>
    >>> # Read grid information
    >>> grid_data = client.read_block(1300)
    >>> print(f"Grid voltage: {grid_data.values['phase_0_voltage']} V")

Public API:
    - BluettiClient: Main client for device interaction
    - MQTTTransport: MQTT transport implementation
    - MQTTConfig: MQTT configuration
    - DeviceProfile: Device configuration
    - Errors: BluettiError, TransportError, ProtocolError, ParserError
"""

__version__ = "2.0.0"
__author__ = "Zeus Fabric Team"
__license__ = "MIT"

# Core client
from .client import ReadGroupResult
from .client import V2Client as BluettiClient
from .client_async import AsyncV2Client

# Errors
from .errors import (
    BluettiError,
    DeviceError,
    ParserError,
    ProtocolError,
    TransportError,
)

# Models
from .devices.profiles import get_device_profile
from .devices.types import DeviceProfile
from .models.device import V2Device as BluettiDevice

# Protocol V2 (advanced usage)
from .protocol.v2 import (
    ArrayField,
    BlockSchema,
    Field,
    PackedField,
    SubField,
    V2Parser,
)

# Transport layer
from .transport.mqtt import MQTTConfig, MQTTTransport

__all__ = [
    # Version
    "__version__",
    # Client
    "BluettiClient",
    "AsyncV2Client",
    "ReadGroupResult",
    # Transport
    "MQTTTransport",
    "MQTTConfig",
    # Models
    "BluettiDevice",
    "DeviceProfile",
    "get_device_profile",
    # Errors
    "BluettiError",
    "TransportError",
    "ProtocolError",
    "ParserError",
    "DeviceError",
    # V2 Protocol (advanced)
    "V2Parser",
    "BlockSchema",
    "Field",
    "ArrayField",
    "PackedField",
    "SubField",
]
