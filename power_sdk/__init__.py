"""Power SDK - Protocol-Agnostic Device Control Platform

This SDK provides a clean, type-safe interface for interacting with
power devices via pluggable transports and protocol layers.

Quick Start:
    >>> from power_sdk import (
    ...     Client, MQTTTransport, MQTTConfig, get_device_profile
    ... )
    >>>
    >>> config = MQTTConfig(
    ...     device_sn="2345EB200xxxxxxx",
    ...     pfx_cert=cert_bytes,
    ...     cert_password="password"
    ... )
    >>>
    >>> transport = MQTTTransport(config)
    >>> profile = get_device_profile("EL100V2")
    >>> client = Client(transport, profile)
    >>> client.connect()
    >>>
    >>> # Read grid information
    >>> grid_data = client.read_block(1300, register_count=16)
    >>> print(f"Grid voltage: {grid_data.values['phase_0_voltage']} V")
    >>>
    >>> client.disconnect()

Public API:
    - Client: Main client for device interaction
    - MQTTTransport: MQTT transport implementation
    - MQTTConfig: MQTT configuration
    - DeviceProfile: Device configuration
    - Errors: SDKError, TransportError, ProtocolError, ParserError
"""

__version__ = "2.0.0"
__author__ = "Zeus Fabric Team"
__license__ = "MIT"

# Core client
from .bootstrap import build_all_clients, build_client_from_entry, load_config
from .client import Client as Client
from .client_async import AsyncClient
from .client_services.group_reader import ReadGroupResult

# Constants
from .constants import V2_PROTOCOL_VERSION

# Models
from .devices.profiles import get_device_profile
from .devices.types import DeviceProfile

# Errors
from .errors import (
    DeviceError,
    ParserError,
    ProtocolError,
    SDKError,
    TransportError,
)
from .models.device import V2Device as DeviceModel
from .protocol.factory import ProtocolFactory
from .protocol.layer import ModbusProtocolLayer

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
from .transport import TransportFactory
from .transport.mqtt import MQTTConfig, MQTTTransport

__all__ = [
    "V2_PROTOCOL_VERSION",
    "ArrayField",
    "AsyncClient",
    "BlockSchema",
    "Client",
    "DeviceError",
    "DeviceModel",
    "DeviceProfile",
    "Field",
    "MQTTConfig",
    "MQTTTransport",
    "ModbusProtocolLayer",
    "PackedField",
    "ParserError",
    "ProtocolError",
    "ProtocolFactory",
    "ReadGroupResult",
    "SDKError",
    "SubField",
    "TransportError",
    "TransportFactory",
    "V2Parser",
    "__version__",
    "build_all_clients",
    "build_client_from_entry",
    "get_device_profile",
    "load_config",
]


