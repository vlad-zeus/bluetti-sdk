"""Power SDK - Protocol-Agnostic Device Control Platform

This SDK provides a clean, type-safe interface for interacting with
power devices via pluggable transports and protocol layers.

The core (this package) is vendor-neutral.  Device-vendor conveniences
live in ``power_sdk.contrib``.

Quick Start (runtime-first):

    Create a ``runtime.yaml`` config file::

        version: 1
        pipelines:
          bluetti_pull:
            mode: pull
            transport: mqtt
            vendor: bluetti
            protocol: v2
        defaults:
          poll_interval: 30
        devices:
          - id: my_device
            pipeline: bluetti_pull
            profile_id: EL100V2
            transport:
              opts:
                device_sn: "${DEVICE_SN}"

    Then run::

        power-sdk runtime --config runtime.yaml --dry-run

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
from .client import Client as Client
from .client_async import AsyncClient
from .client_services.group_reader import ReadGroupResult

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
from .models.device import Device as DeviceModel
from .protocol.factory import ProtocolFactory

# Transport layer
from .transport import TransportFactory
from .transport.mqtt import MQTTConfig, MQTTTransport

__all__ = [
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
]
