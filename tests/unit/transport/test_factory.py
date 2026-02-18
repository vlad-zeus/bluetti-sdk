"""Unit tests for transport factory."""

from __future__ import annotations

from typing import Any

import pytest
from power_sdk.contracts.transport import TransportProtocol
from power_sdk.errors import TransportError
from power_sdk.transport.factory import TransportFactory
from power_sdk.transport.mqtt import MQTTTransport


class _DummyTransport(TransportProtocol):
    def connect(self) -> None:
        return None

    def disconnect(self) -> None:
        return None

    def is_connected(self) -> bool:
        return True

    def send_frame(self, frame: bytes, timeout: float = 5.0) -> bytes:
        return frame


def test_factory_creates_mqtt_transport() -> None:
    transport = TransportFactory.create("mqtt", device_sn="TEST123")
    assert isinstance(transport, MQTTTransport)


def test_factory_rejects_unknown_transport() -> None:
    with pytest.raises(TransportError, match="Unknown transport"):
        TransportFactory.create("nope")


def test_factory_registers_custom_transport_builder() -> None:
    def _builder(**opts: Any) -> TransportProtocol:
        assert opts.get("marker") == "ok"
        return _DummyTransport()

    TransportFactory.register("dummy", _builder)
    transport = TransportFactory.create("dummy", marker="ok")
    assert isinstance(transport, _DummyTransport)

