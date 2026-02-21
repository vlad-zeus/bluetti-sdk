"""Transport contract conformance tests.

Any class that claims to implement TransportProtocol must pass these tests.
Run with: pytest tests/conformance/test_transport_conformance.py

To test your own transport, add it to the `transport_factory` fixture params.
"""

from __future__ import annotations

from collections.abc import Callable
from unittest.mock import MagicMock

import pytest
from power_sdk.contracts.transport import TransportProtocol
from power_sdk.errors import TransportError

# ---------------------------------------------------------------------------
# Stub transport — an in-process transport for conformance testing.
# It records sent frames and returns a preset response.
# ---------------------------------------------------------------------------


class StubTransport(TransportProtocol):
    """Minimal in-process transport for conformance testing."""

    def __init__(self) -> None:
        self._connected = False
        self._next_response: bytes = b""
        self.sent_frames: list[bytes] = []

    def set_response(self, data: bytes) -> None:
        self._next_response = data

    def connect(self) -> None:
        self._connected = True

    def disconnect(self) -> None:
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def send_frame(self, frame: bytes, timeout: float = 5.0) -> bytes:
        if not self._connected:
            raise TransportError("Not connected")
        self.sent_frames.append(frame)
        return self._next_response


def make_stub_transport() -> StubTransport:
    return StubTransport()


# ---------------------------------------------------------------------------
# MQTT transport — exercised via an in-process broker simulator.
#
# The real MQTTTransport state machine is tested (threading events, locks,
# _connected / _waiting flags).  Only the paho network I/O is replaced by
# mock objects so the test runs without a real broker.
# ---------------------------------------------------------------------------

_MQTT_PRESET_RESPONSE = b"\x01\x03\x00\x04\x00\x01\x00\x00"


def make_mqtt_transport() -> TransportProtocol:
    """Create MQTTTransport with network I/O replaced by an in-process simulator."""
    try:
        from power_sdk.transport.mqtt import MQTTConfig, MQTTTransport
    except ImportError:
        pytest.skip("paho-mqtt not installed")

    class _SimulatedBrokerMQTTTransport(MQTTTransport):
        """MQTTTransport with paho replaced by an in-process simulator.

        connect() installs a mock paho client that:
        - Immediately triggers _on_connect(rc=0) to simulate broker acceptance.
        - Wires publish() to call _on_message() synchronously with a preset
          response payload, allowing send_frame() to complete without blocking.
        """

        def connect(self) -> None:
            mock_client = MagicMock()
            self._client = mock_client
            mock_client.subscribe.return_value = (0, 1)
            mock_client.loop_start.return_value = None
            mock_client.loop_stop.return_value = None
            mock_client.disconnect.return_value = None
            mock_client.unsubscribe.return_value = (0, 1)

            def _fake_publish(topic: str, payload: bytes, qos: int) -> MagicMock:
                result = MagicMock()
                result.wait_for_publish.return_value = None
                # Simulate the device responding immediately after we publish.
                # _response_lock is NOT held here (released before publish call),
                # so _on_message can safely acquire it.
                mock_msg = MagicMock()
                mock_msg.topic = self._subscribe_topic
                mock_msg.payload = _MQTT_PRESET_RESPONSE
                self._on_message(mock_client, None, mock_msg)
                return result

            mock_client.publish.side_effect = _fake_publish
            # Simulate broker accepting the connection (sets _connected + event).
            self._on_connect(mock_client, None, {}, 0)

    return _SimulatedBrokerMQTTTransport(
        MQTTConfig(
            broker="test.local",
            port=1883,
            device_sn="TEST001",
            allow_insecure=True,
        )
    )


# ---------------------------------------------------------------------------
# Fixture — parametrize with all known transport implementations
# ---------------------------------------------------------------------------

TRANSPORT_FACTORIES: list[tuple[str, Callable[[], TransportProtocol]]] = [
    ("stub", make_stub_transport),
    ("mqtt", make_mqtt_transport),
]


@pytest.fixture(params=[name for name, _ in TRANSPORT_FACTORIES])
def transport(request: pytest.FixtureRequest) -> TransportProtocol:
    factory_map = dict(TRANSPORT_FACTORIES)
    return factory_map[request.param]()


# ---------------------------------------------------------------------------
# Conformance tests
# ---------------------------------------------------------------------------


class TestTransportConformance:
    """Parameterized conformance suite for TransportProtocol implementations."""

    def test_implements_interface(self, transport: TransportProtocol) -> None:
        """Transport must be a TransportProtocol."""
        assert isinstance(transport, TransportProtocol)

    def test_is_not_connected_before_connect(
        self, transport: TransportProtocol
    ) -> None:
        """is_connected() returns False before connect()."""
        assert transport.is_connected() is False

    def test_connect_makes_connected(self, transport: TransportProtocol) -> None:
        """After connect(), is_connected() returns True."""
        transport.connect()
        assert transport.is_connected() is True
        transport.disconnect()

    def test_disconnect_makes_not_connected(self, transport: TransportProtocol) -> None:
        """After disconnect(), is_connected() returns False."""
        transport.connect()
        transport.disconnect()
        assert transport.is_connected() is False

    def test_disconnect_when_not_connected_is_safe(
        self, transport: TransportProtocol
    ) -> None:
        """disconnect() on an unconnected transport must not raise."""
        transport.disconnect()  # should not raise

    def test_connect_disconnect_cycle_is_repeatable(
        self, transport: TransportProtocol
    ) -> None:
        """Multiple connect/disconnect cycles must work."""
        for _ in range(3):
            transport.connect()
            assert transport.is_connected()
            transport.disconnect()
            assert not transport.is_connected()

    def test_send_frame_returns_bytes(self, transport: TransportProtocol) -> None:
        """send_frame() must return bytes when connected."""
        transport.connect()
        if isinstance(transport, StubTransport):
            transport.set_response(b"\x01\x02\x03")
        result = transport.send_frame(b"\xff\xfe", timeout=1.0)
        assert isinstance(result, bytes)
        transport.disconnect()

    def test_send_frame_raises_when_not_connected(
        self, transport: TransportProtocol
    ) -> None:
        """send_frame() must raise when not connected."""
        assert not transport.is_connected()
        with pytest.raises((TransportError, ConnectionError, OSError, RuntimeError)):
            transport.send_frame(b"\xff", timeout=0.1)

    def test_send_frame_timeout_is_float(self, transport: TransportProtocol) -> None:
        """send_frame() must accept float timeout."""
        transport.connect()
        if isinstance(transport, StubTransport):
            transport.set_response(b"\x01")
        result = transport.send_frame(b"\x01", timeout=2.5)
        assert isinstance(result, bytes)
        transport.disconnect()
