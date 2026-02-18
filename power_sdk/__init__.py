"""Power SDK - Protocol-Agnostic Device Control Platform

This SDK provides a clean, type-safe interface for interacting with
power devices via pluggable transports and protocol layers.

The core (this package) is vendor-neutral.  Device-vendor conveniences
live in ``power_sdk.contrib``.

Quick Start (Bluetti device):
    >>> from power_sdk import MQTTConfig, MQTTTransport
    >>> from power_sdk.contrib.bluetti import build_bluetti_client
    >>>
    >>> config = MQTTConfig(
    ...     device_sn="2345EB200xxxxxxx",
    ...     pfx_cert=cert_bytes,
    ...     cert_password="password"
    ... )
    >>>
    >>> client = build_bluetti_client("EL100V2", MQTTTransport(config))
    >>> client.connect()
    >>>
    >>> # Read grid information
    >>> grid_data = client.read_block(1300, register_count=16)
    >>> print(f"Grid voltage: {grid_data.values['phase_0_voltage']} V")
    >>>
    >>> client.disconnect()

Public API:
    - Client: Main client for device interaction (requires parser DI)
    - AsyncClient: Async wrapper around Client
    - MQTTTransport: MQTT transport implementation
    - MQTTConfig: MQTT configuration
    - DeviceProfile: Device configuration
    - ParserInterface: Contract for parser implementations
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

# Contracts (public types)
from .contracts import ParsedRecord, ParserInterface
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

# Transport layer
from .transport import TransportFactory
from .transport.mqtt import MQTTConfig, MQTTTransport

__all__ = [
    "V2_PROTOCOL_VERSION",
    "AsyncClient",
    "Client",
    "DeviceError",
    "DeviceModel",
    "DeviceProfile",
    "MQTTConfig",
    "MQTTTransport",
    "ParsedRecord",
    "ParserError",
    "ParserInterface",
    "ProtocolError",
    "ProtocolFactory",
    "ReadGroupResult",
    "SDKError",
    "TransportError",
    "TransportFactory",
    "__version__",
    "build_all_clients",
    "build_client_from_entry",
    "load_config",
]


