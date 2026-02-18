"""Transport layer contract."""

from abc import ABC, abstractmethod


class TransportProtocol(ABC):
    """Transport layer interface.

    Responsibilities:
    - Send/receive raw frames over wire (MQTT, BLE, Serial)
    - Connection management
    - Retries and timeouts

    Does NOT know about:
    - Modbus framing
    - Block schemas
    - Device models
    """

    @abstractmethod
    def send_frame(self, frame: bytes, timeout: float = 5.0) -> bytes:
        """Send frame and wait for response.

        Args:
            frame: Raw frame to send (complete with framing/CRC)
            timeout: Timeout in seconds

        Returns:
            Raw response frame

        Raises:
            TimeoutError: If no response within timeout
            ConnectionError: If connection lost
        """

    @abstractmethod
    def connect(self) -> None:
        """Establish connection to device."""

    @abstractmethod
    def disconnect(self) -> None:
        """Close connection to device."""

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected."""
