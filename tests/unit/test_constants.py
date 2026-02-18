"""Tests for platform constants.

Verifies that V2_PROTOCOL_VERSION constant is used consistently
across the SDK instead of magic number literals.
"""

from power_sdk.client import Client
from power_sdk.constants import V2_PROTOCOL_VERSION
from power_sdk.devices.profiles import get_device_profile
from power_sdk.plugins.bluetti.v2.schemas.declarative import block_schema
from power_sdk.transport.mqtt import MQTTConfig, MQTTTransport


def test_v2_protocol_version_constant_exists():
    """Verify V2_PROTOCOL_VERSION constant is defined."""
    assert V2_PROTOCOL_VERSION == 2000


def test_v2_protocol_version_exported():
    """Verify V2_PROTOCOL_VERSION is exported in public API."""
    from power_sdk import V2_PROTOCOL_VERSION as exported_const

    assert exported_const == 2000


def test_client_uses_protocol_version_constant():
    """Verify Client uses V2_PROTOCOL_VERSION for device initialization."""
    config = MQTTConfig(device_sn="test_device")
    transport = MQTTTransport(config)
    profile = get_device_profile("EL100V2")

    client = Client(transport, profile, device_address=1)

    # Device should be initialized with V2_PROTOCOL_VERSION
    assert client.device.protocol_version == V2_PROTOCOL_VERSION
    assert client.device.protocol_version == 2000


def test_block_schema_default_protocol_version():
    """Verify block_schema decorator uses V2_PROTOCOL_VERSION as default."""
    from dataclasses import dataclass

    from power_sdk.protocol.v2.datatypes import UInt16
    from power_sdk.plugins.bluetti.v2.schemas.declarative import block_field

    # Create schema with default protocol_version
    @block_schema(
        block_id=99999,
        name="TEST_BLOCK",
        description="Test block for constant verification",
    )
    @dataclass
    class TestBlock:
        test_field: int = block_field(
            offset=0,
            type=UInt16(),
            description="Test field",
        )

    schema = TestBlock.to_schema()  # type: ignore[attr-defined]

    # Should use V2_PROTOCOL_VERSION as default
    assert schema.protocol_version == V2_PROTOCOL_VERSION
    assert schema.protocol_version == 2000


def test_schema_factory_uses_constant():
    """Verify schema factories use V2_PROTOCOL_VERSION constant."""
    from power_sdk.plugins.bluetti.v2.schemas.factories.epad_liquid import build_epad_liquid_schema

    # Build schema using factory
    schema = build_epad_liquid_schema(
        block_id=99998,
        name="TEST_EPAD_LIQUID",
        point_index=99,
    )

    # Should use V2_PROTOCOL_VERSION
    assert schema.protocol_version == V2_PROTOCOL_VERSION
    assert schema.protocol_version == 2000


def test_constant_immutability():
    """Verify V2_PROTOCOL_VERSION is effectively immutable."""
    # Constants module imports should provide same value
    from power_sdk.constants import V2_PROTOCOL_VERSION as const1
    from power_sdk.constants import V2_PROTOCOL_VERSION as const2

    assert const1 is const2
    assert const1 == 2000
    assert const2 == 2000


