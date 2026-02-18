"""Convenience helpers for Bluetti devices.

Provides a one-call factory for creating a fully configured Client or AsyncClient
for Bluetti devices without manual dependency injection.

Example::

    from power_sdk.contrib.bluetti import build_bluetti_client
    from power_sdk.transport.mqtt import MQTTConfig, MQTTTransport

    config = MQTTConfig(device_sn="SN123", pfx_cert=cert_bytes, cert_password="pw")
    client = build_bluetti_client("EL100V2", MQTTTransport(config))
    client.connect()
    data = client.read_block(1300)

This module is the ONLY place in power_sdk that is allowed to import directly
from power_sdk.plugins.bluetti.*.  Core modules (client.py, bootstrap.py, etc.)
must remain plugin-neutral.
"""

from __future__ import annotations

from typing import Any

from power_sdk.client import Client
from power_sdk.client_async import AsyncClient
from power_sdk.contracts.transport import TransportProtocol
from power_sdk.plugins.bluetti.v2.manifest_instance import (
    BLUETTI_V2_MANIFEST,
    _load_schemas_for_profile,
)
from power_sdk.plugins.bluetti.v2.profiles.registry import get_device_profile
from power_sdk.plugins.bluetti.v2.protocol.layer import ModbusProtocolLayer
from power_sdk.plugins.bluetti.v2.protocol.parser import V2Parser


def build_bluetti_client(
    profile_id: str,
    transport: TransportProtocol,
    device_address: int = 1,
    **kwargs: Any,
) -> Client:
    """Build a fully configured Client for a Bluetti device.

    Args:
        profile_id: Device profile ID, e.g. "EL100V2", "EL30V2", "ELITE200V2".
        transport: Connected or unconnected transport instance.
        device_address: Modbus device address (default: 1).
        **kwargs: Extra keyword arguments forwarded to Client (e.g. retry_policy).

    Returns:
        Client instance with V2Parser pre-configured with all profile schemas.
    """
    profile = get_device_profile(profile_id)
    parser = V2Parser()
    _load_schemas_for_profile(profile, parser)
    protocol = ModbusProtocolLayer()

    return Client(
        transport=transport,
        profile=profile,
        parser=parser,
        protocol=protocol,
        device_address=device_address,
        **kwargs,
    )


def build_bluetti_async_client(
    profile_id: str,
    transport: TransportProtocol,
    device_address: int = 1,
    **kwargs: Any,
) -> AsyncClient:
    """Build a fully configured AsyncClient for a Bluetti device.

    Args:
        profile_id: Device profile ID, e.g. "EL100V2", "EL30V2", "ELITE200V2".
        transport: Transport instance.
        device_address: Modbus device address (default: 1).
        **kwargs: Extra keyword arguments forwarded to AsyncClient.

    Returns:
        AsyncClient instance ready for use.
    """
    profile = get_device_profile(profile_id)
    parser = V2Parser()
    _load_schemas_for_profile(profile, parser)
    protocol = ModbusProtocolLayer()

    return AsyncClient(
        transport=transport,
        profile=profile,
        parser=parser,
        protocol=protocol,
        device_address=device_address,
        **kwargs,
    )


__all__ = [
    "BLUETTI_V2_MANIFEST",
    "ModbusProtocolLayer",
    "V2Parser",
    "build_bluetti_async_client",
    "build_bluetti_client",
    "get_device_profile",
]
