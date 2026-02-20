"""Unit tests for protocol factory."""

import pytest
from power_sdk.contracts.protocol import ProtocolLayerInterface
from power_sdk.errors import ProtocolError
from power_sdk.plugins.bluetti.v2.protocol.layer import ModbusProtocolLayer
from power_sdk.protocol.factory import ProtocolFactory


def test_factory_creates_default_v2_layer() -> None:
    ProtocolFactory.register("v2", ModbusProtocolLayer)
    layer = ProtocolFactory.create("v2")
    assert isinstance(layer, ModbusProtocolLayer)


def test_factory_raises_on_unknown_protocol() -> None:
    with pytest.raises(ProtocolError, match="Unknown protocol"):
        ProtocolFactory.create("__missing_protocol__")


def test_factory_registers_custom_builder() -> None:
    class DummyLayer(ProtocolLayerInterface):
        def read_block(self, transport, device_address, block_id, register_count):
            raise NotImplementedError

    ProtocolFactory.register("dummy_test_protocol", DummyLayer)
    layer = ProtocolFactory.create("dummy_test_protocol")
    assert isinstance(layer, DummyLayer)
