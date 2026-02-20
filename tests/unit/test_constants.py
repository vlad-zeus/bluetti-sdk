"""Tests for platform constants and plugin protocol constants."""

from power_sdk.plugins.bluetti.v2.constants import V2_PROTOCOL_VERSION
from power_sdk.plugins.bluetti.v2.schemas.declarative import block_schema
from power_sdk.transport.mqtt import MQTTConfig, MQTTTransport


def test_v2_protocol_version_constant_exists():
    """Verify V2_PROTOCOL_VERSION is defined in Bluetti plugin."""
    assert V2_PROTOCOL_VERSION == 2000


def test_v2_protocol_version_not_in_core_api():
    """Verify V2_PROTOCOL_VERSION is NOT in core public API (vendor-neutral)."""
    import power_sdk

    assert not hasattr(power_sdk, "V2_PROTOCOL_VERSION")


def test_client_uses_profile_protocol_version():
    """Verify Client propagates profile.protocol_version to device."""
    from power_sdk.contrib.bluetti import build_bluetti_client

    config = MQTTConfig(device_sn="test_device")
    transport = MQTTTransport(config)

    client = build_bluetti_client("EL100V2", transport, device_address=1)

    # Device should use protocol_version from profile
    assert client.device.protocol_version == V2_PROTOCOL_VERSION
    assert client.device.protocol_version == 2000


def test_block_schema_default_protocol_version():
    """Verify block_schema decorator uses V2_PROTOCOL_VERSION as default."""
    from dataclasses import dataclass

    from power_sdk.plugins.bluetti.v2.protocol.datatypes import UInt16
    from power_sdk.plugins.bluetti.v2.schemas.declarative import block_field

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
    assert schema.protocol_version == V2_PROTOCOL_VERSION
    assert schema.protocol_version == 2000


def test_schema_factory_uses_constant():
    """Verify schema factories use V2_PROTOCOL_VERSION."""
    from power_sdk.plugins.bluetti.v2.schemas.factories.epad_liquid import (
        build_epad_liquid_schema,
    )

    schema = build_epad_liquid_schema(
        block_id=99998,
        name="TEST_EPAD_LIQUID",
        point_index=99,
    )

    assert schema.protocol_version == V2_PROTOCOL_VERSION
    assert schema.protocol_version == 2000


def test_constant_immutability():
    """Verify V2_PROTOCOL_VERSION is effectively immutable."""
    from power_sdk.plugins.bluetti.v2.constants import V2_PROTOCOL_VERSION as const1
    from power_sdk.plugins.bluetti.v2.constants import V2_PROTOCOL_VERSION as const2

    assert const1 is const2
    assert const1 == 2000
    assert const2 == 2000
