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

        power-cli runtime --config runtime.yaml --dry-run

Public API:
    - Client: Main client for device interaction (requires parser DI)
    - AsyncClient: Async wrapper around Client
    - Device: Runtime device model (state + block registry)
    - TransportFactory: Registry for pluggable transport implementations
    - DeviceProfile: Device configuration
    - ParserInterface: Contract for parser implementations
    - Errors: SDKError, TransportError, ProtocolError, ParserError

Transport implementations (not imported eagerly — import explicitly):
    - power_sdk.transport.mqtt: MQTTTransport, MQTTConfig (requires paho-mqtt)
"""

__version__ = "2.1.0"
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
    ParserError,
    ProtocolError,
    SDKError,
    TransportError,
)
from .models.device import Device
from .runtime import Executor, RuntimeRegistry

# Transport layer
from .transport import TransportFactory

__all__ = [
    "AsyncClient",
    "Client",
    "Device",
    "DeviceProfile",
    "Executor",
    "ParsedRecord",
    "ParserError",
    "ParserInterface",
    "ProtocolError",
    "ReadGroupResult",
    "RuntimeRegistry",
    "SDKError",
    "TransportError",
    "TransportFactory",
    "__version__",
]
