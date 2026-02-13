"""MQTT Transport Layer

Minimal MQTT transport for V2 devices.
Implements TransportProtocol interface.

Responsibilities:
- Connect to Bluetti MQTT broker
- Send Modbus frames
- Receive responses
- Timeout handling

Does NOT know about:
- Block schemas
- Field parsing
- Device models
"""

import ssl
import tempfile
import os
from typing import Optional, Callable
from dataclasses import dataclass
from threading import Event, Lock
import logging

try:
    import paho.mqtt.client as mqtt
except ImportError:
    raise ImportError(
        "paho-mqtt is required. Install with: pip install paho-mqtt"
    )

from .base import TransportProtocol
from ..errors import TransportError
from ..protocol.modbus import validate_crc

logger = logging.getLogger(__name__)


@dataclass
class MQTTConfig:
    """MQTT connection configuration."""
    broker: str = "iot.bluettipower.com"
    port: int = 18760
    device_sn: str = ""
    pfx_cert: Optional[bytes] = None
    cert_password: Optional[str] = None
    keepalive: int = 60


class MQTTTransport(TransportProtocol):
    """MQTT transport for Bluetti devices.

    Minimal implementation for Day 4:
    - Synchronous send_frame() with response wait
    - Single request at a time (no pipelining)
    - 5 second timeout

    Topic naming (from device perspective):
    - Device publishes to: PUB/{device_sn}
    - Device subscribes to: SUB/{device_sn}

    From client perspective (we are client):
    - We subscribe to: PUB/{device_sn}  ← Receive responses here
    - We publish to: SUB/{device_sn}    ← Send requests here
    """

    def __init__(self, config: MQTTConfig):
        """Initialize MQTT transport.

        Args:
            config: MQTT configuration
        """
        self.config = config
        self._client: Optional[mqtt.Client] = None
        self._connected = False
        self._connect_event = Event()
        self._connect_rc: Optional[int] = None

        # Response handling
        self._response_event = Event()
        self._response_data: Optional[bytes] = None
        self._response_lock = Lock()
        self._waiting = False  # Flag to filter unexpected responses

        # Request serialization (enforce "single request at a time")
        self._request_lock = Lock()

        # Topics
        self._subscribe_topic = f"PUB/{config.device_sn}"  # Device publishes here
        self._publish_topic = f"SUB/{config.device_sn}"    # Device subscribes here

        # SSL context
        self._ssl_context: Optional[ssl.SSLContext] = None

        # Temp files for certificates
        self._temp_cert_file: Optional[str] = None
        self._temp_key_file: Optional[str] = None

    def connect(self):
        """Connect to MQTT broker.

        Steps:
        1. Extract PFX certificate
        2. Create SSL context
        3. Connect to broker
        4. Subscribe to response topic

        Raises:
            TransportError: If connection fails
        """
        logger.info(f"Connecting to MQTT broker: {self.config.broker}:{self.config.port}")

        try:
            # Extract certificate from PFX
            self._setup_ssl()
            self._connect_event.clear()
            self._connect_rc = None

            # Create MQTT client
            self._client = mqtt.Client(
                client_id=f"bluetti_v2_{self.config.device_sn}",
                protocol=mqtt.MQTTv311
            )

            # Set callbacks
            self._client.on_connect = self._on_connect
            self._client.on_message = self._on_message
            self._client.on_disconnect = self._on_disconnect

            # Configure TLS
            if self._ssl_context:
                self._client.tls_set_context(self._ssl_context)

            # Connect
            self._client.connect(
                self.config.broker,
                self.config.port,
                keepalive=self.config.keepalive
            )

            # Start network loop
            self._client.loop_start()

            # Wait for connect callback (with timeout)
            if not self._connect_event.wait(10.0):
                raise TransportError("Connection timeout")

            if not self._connected:
                rc = self._connect_rc
                raise TransportError(
                    f"Connection failed (rc={rc})"
                )

            logger.info(f"Connected to MQTT broker")

        except Exception as e:
            # Clean up temp certificates on failure
            self._cleanup_certs()
            raise TransportError(f"Failed to connect: {e}")

    def disconnect(self):
        """Disconnect from MQTT broker."""
        logger.info("Disconnecting from MQTT broker...")

        try:
            if self._client:
                if self._connected:
                    self._client.unsubscribe(self._subscribe_topic)
                    self._client.disconnect()
                self._client.loop_stop()
        finally:
            # Always clean up temp certificate files and reset state
            self._cleanup_certs()
            self._connected = False
            logger.info("Disconnected")

    def is_connected(self) -> bool:
        """Check if connected to broker.

        Returns:
            True if connected
        """
        return self._connected

    def send_frame(self, frame: bytes, timeout: float = 5.0) -> bytes:
        """Send Modbus frame and wait for response.

        This is synchronous and thread-safe (single request at a time):
        1. Publish frame to SUB/{device_sn}
        2. Wait for response on PUB/{device_sn}
        3. Return response

        Args:
            frame: Modbus RTU frame (with CRC)
            timeout: Timeout in seconds

        Returns:
            Response frame (with CRC)

        Raises:
            TransportError: If send fails or timeout
        """
        # Serialize all requests - only one at a time
        with self._request_lock:
            if not self._connected:
                raise TransportError("Not connected to MQTT broker")

            # Reset response event and mark that we're waiting for response
            with self._response_lock:
                self._response_event.clear()
                self._response_data = None
                self._waiting = True  # Start expecting response

            try:
                # Publish request
                logger.debug(f"Publishing to {self._publish_topic}: {frame.hex()}")

                try:
                    result = self._client.publish(
                        self._publish_topic,
                        payload=frame,
                        qos=1  # At least once delivery
                    )

                    # Wait for publish to complete
                    result.wait_for_publish()

                except Exception as e:
                    raise TransportError(f"Failed to publish: {e}")

                # Wait for response
                logger.debug(f"Waiting for response (timeout={timeout}s)...")

                if not self._response_event.wait(timeout):
                    raise TransportError(f"Response timeout after {timeout}s")

                # Get response
                with self._response_lock:
                    if self._response_data is None:
                        raise TransportError("No response data received")

                    response = self._response_data
                    self._response_data = None

                logger.debug(f"Received response: {response.hex()}")

                return response

            finally:
                # Always clear waiting flag, even on timeout/exception
                with self._response_lock:
                    self._waiting = False

    def _setup_ssl(self):
        """Setup SSL context from PFX certificate.

        Raises:
            TransportError: If certificate setup fails
        """
        if not self.config.pfx_cert or not self.config.cert_password:
            logger.warning("No certificate provided, attempting insecure connection")
            return

        try:
            from cryptography.hazmat.primitives.serialization import pkcs12

            # Load PFX
            private_key, certificate, ca_certs = pkcs12.load_key_and_certificates(
                self.config.pfx_cert,
                self.config.cert_password.encode()
            )

            # Create temp files for cert and key
            # (paho-mqtt requires file paths, not in-memory objects)
            with tempfile.NamedTemporaryFile(
                mode='wb', delete=False, suffix='.pem'
            ) as cert_file:
                from cryptography.hazmat.primitives import serialization

                # Write certificate
                cert_file.write(
                    certificate.public_bytes(serialization.Encoding.PEM)
                )
                self._temp_cert_file = cert_file.name

            with tempfile.NamedTemporaryFile(
                mode='wb', delete=False, suffix='.pem'
            ) as key_file:
                # Write private key
                key_file.write(
                    private_key.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.TraditionalOpenSSL,
                        encryption_algorithm=serialization.NoEncryption()
                    )
                )
                self._temp_key_file = key_file.name

            # Create SSL context
            self._ssl_context = ssl.create_default_context()
            self._ssl_context.load_cert_chain(
                certfile=self._temp_cert_file,
                keyfile=self._temp_key_file
            )

            logger.info("SSL certificates loaded successfully")

        except Exception as e:
            raise TransportError(f"Failed to setup SSL: {e}")

    def _cleanup_certs(self):
        """Clean up temporary certificate files."""
        for temp_file in [self._temp_cert_file, self._temp_key_file]:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except Exception as e:
                    logger.warning(f"Failed to delete temp file {temp_file}: {e}")

    def _on_connect(self, client, userdata, flags, rc):
        """MQTT connect callback."""
        if rc == 0:
            logger.info(f"Connected to MQTT broker (rc={rc})")

            # Subscribe to response topic
            client.subscribe(self._subscribe_topic, qos=1)
            logger.info(f"Subscribed to {self._subscribe_topic}")

            self._connected = True
            self._connect_rc = rc
            self._connect_event.set()
        else:
            logger.error(f"Connection failed (rc={rc})")
            self._connected = False
            self._connect_rc = rc
            self._connect_event.set()

    def _on_message(self, client, userdata, msg):
        """MQTT message callback."""
        logger.debug(
            f"Received message on {msg.topic}: "
            f"{len(msg.payload)} bytes"
        )

        # Check if we're expecting a response
        with self._response_lock:
            if not self._waiting:
                logger.debug(
                    "Ignoring unexpected response (not waiting for any request)"
                )
                return

        # Validate response before storing
        payload = msg.payload

        # Minimum Modbus frame: [addr][func][count][crc_lo][crc_hi] = 5 bytes
        if len(payload) < 5:
            logger.warning(
                f"Ignoring invalid response: too short ({len(payload)} bytes)"
            )
            return

        # Check function code is reasonable (0x03 or 0x83 for errors)
        function_code = payload[1]
        if function_code not in (0x03, 0x83):
            logger.warning(
                f"Ignoring response with unexpected function code: 0x{function_code:02X}"
            )
            return

        # Validate CRC early to fail fast on corrupted frames
        if not validate_crc(payload):
            logger.warning("Ignoring response with invalid CRC")
            return

        # Store response and signal event
        with self._response_lock:
            # Double-check we're still waiting (could have timed out)
            if self._waiting:
                self._response_data = payload
                self._response_event.set()
            else:
                logger.debug(
                    "Ignoring late response (request already timed out)"
                )

    def _on_disconnect(self, client, userdata, rc):
        """MQTT disconnect callback."""
        logger.info(f"Disconnected from MQTT broker (rc={rc})")
        self._connected = False
