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

Security Model - TLS Certificate Handling:
    paho-mqtt Limitation:
        The paho-mqtt library requires TLS certificates as filesystem paths,
        not in-memory objects. This forces us to temporarily write private
        keys to disk during connection establishment.

    Risk Window:
        There is a brief window between file creation and permission setting
        where the key file has default system permissions. We minimize this
        by:
        1. Using tempfile.mkdtemp() which creates directories with 0o700 (owner-only)
        2. Setting file permissions immediately after writing
        3. Cleaning up in all exit paths (success, error, atexit)

    Mitigation Strategy:
        - Private temp directory: Created with owner-only permissions (0o700)
        - Restrictive file permissions: Owner read-only (0o400) set immediately
        - Automatic cleanup: Registered with atexit + finally blocks
        - Directory deletion: Entire directory removed, not just files
        - Fail-safe cleanup: All temp resources cleaned in error paths

    Residual Risk:
        On systems with filesystem monitoring or snapshots, the private key
        may be captured during the brief window. For maximum security, use
        secure boot and encrypted filesystems.
"""

import atexit
import contextlib
import logging
import os
import ssl
import stat
import tempfile
from dataclasses import dataclass
from threading import Event, Lock
from typing import Any, Dict, Optional

try:
    import paho.mqtt.client as mqtt
except ImportError:
    raise ImportError(
        "paho-mqtt is required. Install with: pip install paho-mqtt"
    ) from None

from ..contracts.transport import TransportProtocol
from ..errors import TransportError

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
        self._publish_topic = f"SUB/{config.device_sn}"  # Device subscribes here

        # SSL context
        self._ssl_context: Optional[ssl.SSLContext] = None

        # Private temp directory for certificates (owner-only permissions)
        self._temp_cert_dir: Optional[str] = None
        self._temp_cert_file: Optional[str] = None
        self._temp_key_file: Optional[str] = None
        self._atexit_cleanup_registered = False

    def connect(self) -> None:
        """Connect to MQTT broker.

        Steps:
        1. Extract PFX certificate
        2. Create SSL context
        3. Connect to broker
        4. Subscribe to response topic

        Raises:
            TransportError: If connection fails
        """
        logger.info(
            f"Connecting to MQTT broker: {self.config.broker}:{self.config.port}"
        )

        try:
            # Extract certificate from PFX
            self._setup_ssl()
            self._connect_event.clear()
            self._connect_rc = None

            # Create MQTT client
            self._client = mqtt.Client(
                client_id=f"bluetti_v2_{self.config.device_sn}", protocol=mqtt.MQTTv311
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
                self.config.broker, self.config.port, keepalive=self.config.keepalive
            )

            # Start network loop
            self._client.loop_start()

            # Wait for connect callback (with timeout)
            if not self._connect_event.wait(10.0):
                raise TransportError("Connection timeout")

            if not self._connected:
                rc = self._connect_rc
                raise TransportError(f"Connection failed (rc={rc})")

            logger.info("Connected to MQTT broker")

        except Exception as e:
            # Safe teardown of partially initialized client
            # Critical for retry scenarios to prevent resource leak
            if self._client:
                with contextlib.suppress(Exception):
                    # Stop network loop if it was started
                    # (safe to call even if not started)
                    self._client.loop_stop()

                with contextlib.suppress(Exception):
                    # Disconnect if connection was initiated
                    if self._connected:
                        self._client.disconnect()

            # Reset state for clean retry
            self._connected = False
            self._client = None

            # Clean up temp certificates on failure
            self._cleanup_certs()
            raise TransportError(f"Failed to connect: {e}") from e

    def disconnect(self) -> None:
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
                    assert self._client is not None  # Connected, so client must exist
                    result = self._client.publish(
                        self._publish_topic,
                        payload=frame,
                        qos=1,  # At least once delivery
                    )

                    # Wait for publish to complete
                    result.wait_for_publish()

                except Exception as e:
                    raise TransportError(f"Failed to publish: {e}") from e

                # Wait for response
                logger.debug(f"Waiting for response (timeout={timeout}s)...")

                if not self._response_event.wait(timeout):
                    raise TransportError(f"Response timeout after {timeout}s")

                # Fail-fast: check if disconnected while waiting
                if not self._connected:
                    raise TransportError("Connection lost while waiting for response")

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

    def _setup_ssl(self) -> None:
        """Setup SSL context from PFX certificate.

        Creates a private temp directory with owner-only permissions (0o700),
        writes certificate and key files with restrictive permissions (0o400),
        and ensures cleanup in all exit paths.

        Security Notes:
            - Uses tempfile.mkdtemp() for automatic owner-only directory creation
            - Sets file permissions to 0o400 (read-only) immediately after writing
            - Registers atexit cleanup handler for crash recovery
            - Cleans up entire directory in finally blocks

        Raises:
            TransportError: If certificate setup fails
        """
        if not self.config.pfx_cert or not self.config.cert_password:
            logger.warning("No certificate provided, attempting insecure connection")
            return

        try:
            from cryptography.hazmat.primitives.serialization import pkcs12

            # Load PFX
            private_key, certificate, _ca_certs = pkcs12.load_key_and_certificates(
                self.config.pfx_cert, self.config.cert_password.encode()
            )

            from cryptography.hazmat.primitives import serialization

            # Create private temp directory with owner-only permissions (0o700)
            # mkdtemp() automatically sets restrictive permissions
            self._temp_cert_dir = tempfile.mkdtemp(prefix="bluetti_tls_")
            logger.debug(f"Created private temp directory: {self._temp_cert_dir}")

            # Register cleanup handler once to ensure deletion on process exit
            if not self._atexit_cleanup_registered:
                atexit.register(self._cleanup_certs)
                self._atexit_cleanup_registered = True

            try:
                # Write certificate to temp file in private directory
                cert_path = os.path.join(self._temp_cert_dir, "cert.pem")
                with open(cert_path, "wb") as cert_file:
                    cert_file.write(
                        certificate.public_bytes(serialization.Encoding.PEM)
                    )
                self._temp_cert_file = cert_path

                # Set restrictive permissions (owner read-only)
                os.chmod(self._temp_cert_file, stat.S_IRUSR)

                # Write private key to temp file in private directory
                key_path = os.path.join(self._temp_cert_dir, "key.pem")
                with open(key_path, "wb") as key_file:
                    key_file.write(
                        private_key.private_bytes(
                            encoding=serialization.Encoding.PEM,
                            format=serialization.PrivateFormat.TraditionalOpenSSL,
                            encryption_algorithm=serialization.NoEncryption(),
                        )
                    )
                self._temp_key_file = key_path

                # CRITICAL: Set restrictive permissions immediately (owner read-only)
                os.chmod(self._temp_key_file, stat.S_IRUSR)

                # Create SSL context
                self._ssl_context = ssl.create_default_context()
                self._ssl_context.load_cert_chain(
                    certfile=self._temp_cert_file, keyfile=self._temp_key_file
                )
                logger.info("SSL certificates loaded successfully")

            except Exception:
                # Clean up temp directory if any step fails
                self._cleanup_certs()
                raise

        except Exception as e:
            # Clean up any temp resources created before the error
            self._cleanup_certs()
            raise TransportError(f"Failed to setup SSL: {e}") from e

    def _cleanup_certs(self) -> None:
        """Clean up temporary certificate directory and files.

        Deletes the entire private temp directory containing certificate files.
        This is safer than deleting individual files as it ensures complete cleanup.

        Safe to call multiple times (idempotent).
        """
        temp_dir = self._temp_cert_dir
        if temp_dir and os.path.exists(temp_dir):
            try:
                import shutil

                shutil.rmtree(temp_dir, ignore_errors=False)
                logger.debug(f"Deleted temp cert directory: {temp_dir}")
                # Reset state only after successful deletion.
                # If deletion fails, keep paths so cleanup can be retried.
                self._temp_cert_dir = None
                self._temp_cert_file = None
                self._temp_key_file = None
            except Exception as e:
                logger.warning(f"Failed to delete temp cert directory: {e}")
        else:
            # No directory to clean up, just reset file paths
            self._temp_cert_file = None
            self._temp_key_file = None

    def _on_connect(
        self, client: mqtt.Client, userdata: Any, flags: Dict[str, Any], rc: int
    ) -> None:
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

    def _on_message(
        self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage
    ) -> None:
        """MQTT message callback."""
        logger.debug(f"Received message on {msg.topic}: {len(msg.payload)} bytes")

        # Check if we're expecting a response
        with self._response_lock:
            if not self._waiting:
                logger.debug(
                    "Ignoring unexpected response (not waiting for any request)"
                )
                return

        # Validate response before storing
        payload = msg.payload

        # Transport layer: just store the raw response.
        # Protocol validation (CRC, function code, length) happens in protocol layer.
        # This keeps transport layer focused on MQTT communication only.

        # Store response and signal event
        with self._response_lock:
            # Double-check we're still waiting (could have timed out)
            if self._waiting:
                self._response_data = payload
                self._response_event.set()
            else:
                logger.debug("Ignoring late response (request already timed out)")

    def _on_disconnect(self, client: mqtt.Client, userdata: Any, rc: int) -> None:
        """MQTT disconnect callback.

        Sets connected flag to False and wakes up any waiting send_frame()
        calls to fail fast instead of waiting for timeout.
        """
        logger.info(f"Disconnected from MQTT broker (rc={rc})")
        self._connected = False
        # Wake up send_frame() if waiting - it will check _connected and fail fast
        self._response_event.set()
