"""Transport contract conformance tests.

Any class that claims to implement TransportProtocol must pass these tests.
Run with: pytest tests/conformance/test_transport_conformance.py

To test your own transport, add it to the `transport_factory` fixture params.
"""

from __future__ import annotations

from typing import Callable

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
# Fixture — parametrize with all known transport implementations
# ---------------------------------------------------------------------------

TRANSPORT_FACTORIES: list[tuple[str, Callable[[], TransportProtocol]]] = [
    ("stub", make_stub_transport),
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

    def test_disconnect_makes_not_connected(
        self, transport: TransportProtocol
    ) -> None:
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

    def test_send_frame_timeout_is_float(
        self, transport: TransportProtocol
    ) -> None:
        """send_frame() must accept float timeout."""
        transport.connect()
        if isinstance(transport, StubTransport):
            transport.set_response(b"\x01")
        result = transport.send_frame(b"\x01", timeout=2.5)
        assert isinstance(result, bytes)
        transport.disconnect()
