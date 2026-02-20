"""MQTT transport layer.

Implements TransportProtocol — vendor-neutral MQTT over Modbus-RTU framing.

Responsibilities:
- Connect to an MQTT broker
- Send Modbus frames (publish to SUB/{device_sn})
- Receive responses (subscribe to PUB/{device_sn})
- Timeout and reconnect handling

Does NOT know about:
- Block schemas
- Field parsing
- Device models

TLS / Security:
    TLS is required by default (MQTTConfig.allow_insecure defaults to False).
    Pass pfx_cert + cert_password, or set allow_insecure=True only for
    local testing against a broker without TLS.

    paho-mqtt Limitation:
        paho-mqtt requires TLS certificates as filesystem paths,
        not in-memory objects.  This forces a temporary write of the
        private key to disk during connection establishment.

    Mitigation Strategy:
        - Private temp directory with owner-only permissions (0o700)
        - Owner read-only file permissions (0o400) set at creation
        - Automatic cleanup via atexit + finally blocks
        - Entire directory removed on disconnect / error (not just files)

    Residual Risk:
        On systems with filesystem monitoring or snapshots, the private key
        may be captured during the brief window.  For maximum security, use
        secure boot and encrypted filesystems.
"""

import atexit
import contextlib
import logging
import os
import ssl
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
    """MQTT connection configuration.

    TLS is required by default.  Set ``allow_insecure=True`` only for
    local development / testing against a broker that does not use TLS.
    """

    broker: str = "iot.bluettipower.com"
    port: int = 18760
    device_sn: str = ""
    pfx_cert: Optional[bytes] = None
    cert_password: Optional[str] = None
    keepalive: int = 60
    allow_insecure: bool = False


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

        if not self.config.device_sn:
            raise TransportError(
                "device_sn is required for MQTT transport topic resolution"
            )

        # Avoid leaking background loop threads on repeated connect() calls.
        # disconnect() resets all state in its finally block, so even if it
        # raises we can safely proceed with a fresh connection attempt.
        if self._client is not None:
            logger.warning(
                "connect() called with existing client; reconnecting cleanly"
            )
            try:
                self.disconnect()
            except Exception as exc:
                logger.warning(
                    "Pre-connect cleanup error (state reset by disconnect): %s", exc
                )

        try:
            # Extract certificate from PFX
            self._setup_ssl()
            self._connect_event.clear()
            self._connect_rc = None
            with self._response_lock:
                self._response_event.clear()
                self._response_data = None
                self._waiting = False

            # Create MQTT client
            self._client = mqtt.Client(
                client_id=f"power_sdk_{self.config.device_sn}", protocol=mqtt.MQTTv311
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
                try:
                    # Stop network loop if it was started
                    # (safe to call even if not started)
                    self._client.loop_stop()
                except Exception as cleanup_err:
                    logger.debug(
                        f"Error stopping MQTT loop during cleanup: {cleanup_err}"
                    )

                try:
                    # Disconnect if connection was initiated
                    if self._connected:
                        self._client.disconnect()
                except Exception as cleanup_err:
                    logger.debug(
                        f"Error disconnecting MQTT during cleanup: {cleanup_err}"
                    )

            # Reset state for clean retry
            self._connected = False
            self._client = None

            # Clean up temp certificates on failure
            self._cleanup_certs()
            raise TransportError(f"Failed to connect: {e}") from e

    def disconnect(self) -> None:
        """Disconnect from MQTT broker.

        Acquires ``_request_lock`` before calling any paho-mqtt client methods
        to prevent concurrent access from a racing ``send_frame()`` call.  If
        ``send_frame()`` is blocked on ``_response_event.wait()``, the paho
        network thread will fire ``_on_disconnect`` independently (setting
        ``_connected=False`` and signalling the event), which causes
        ``send_frame()`` to fail fast and release ``_request_lock`` — so there
        is no deadlock.
        """
        logger.info("Disconnecting from MQTT broker...")

        try:
            with self._request_lock:
                if self._client:
                    if self._connected:
                        self._client.unsubscribe(self._subscribe_topic)
                        self._client.disconnect()
                    self._client.loop_stop()
        finally:
            # Always clean up temp certificate files and reset state
            self._cleanup_certs()
            self._connected = False
            self._ssl_context = None
            self._client = None
            with self._response_lock:
                self._response_data = None
                self._waiting = False
                self._response_event.clear()
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
                    if self._client is None:
                        raise TransportError(
                            "MQTT client unavailable while connected state is set"
                        )
                    result = self._client.publish(
                        self._publish_topic,
                        payload=frame,
                        qos=1,  # At least once delivery
                    )

                    # Wait for publish to complete
                    result.wait_for_publish(timeout=timeout)
                    if not result.is_published():
                        raise TransportError(
                            f"Publish timeout after {timeout}s (no broker ack)"
                        )

                except TransportError:
                    raise
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
            - Creates key/cert files with 0o400 atomically (os.open + O_EXCL)
            - Registers atexit cleanup handler for crash recovery
            - Cleans up entire directory in finally blocks

        Raises:
            TransportError: If certificate setup fails
        """
        if not self.config.pfx_cert or not self.config.cert_password:
            if not self.config.allow_insecure:
                raise TransportError(
                    "No TLS certificate provided. "
                    "Pass pfx_cert + cert_password, or set allow_insecure=True "
                    "to connect without TLS (development only)."
                )
            logger.warning(
                "Connecting without TLS (allow_insecure=True). "
                "Do NOT use in production."
            )
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
            self._temp_cert_dir = tempfile.mkdtemp(prefix="power_sdk_tls_")
            logger.debug(f"Created private temp directory: {self._temp_cert_dir}")

            # Register cleanup handler once to ensure deletion on process exit
            if not self._atexit_cleanup_registered:
                atexit.register(self._cleanup_certs)
                self._atexit_cleanup_registered = True

            try:
                # Write certificate to temp file in private directory
                cert_path = os.path.join(self._temp_cert_dir, "cert.pem")
                self._write_private_file(
                    cert_path,
                    certificate.public_bytes(serialization.Encoding.PEM),
                )
                self._temp_cert_file = cert_path

                # Write private key to temp file in private directory
                key_path = os.path.join(self._temp_cert_dir, "key.pem")
                self._write_private_file(
                    key_path,
                    private_key.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.TraditionalOpenSSL,
                        encryption_algorithm=serialization.NoEncryption(),
                    ),
                )
                self._temp_key_file = key_path

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

    @staticmethod
    def _write_private_file(path: str, data: bytes) -> None:
        """Atomically create and write file with owner-only read permission."""
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        fd = os.open(path, flags, 0o400)
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(data)
        except Exception:
            # If os.fdopen() raised, fd is still open — close it to prevent a
            # file-descriptor leak.  If the write raised, the context manager
            # already closed fd; os.close() will fail with OSError (suppressed).
            with contextlib.suppress(OSError):
                os.close(fd)
            with contextlib.suppress(Exception):
                os.unlink(path)
            raise

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
        """MQTT message callback.

        THREAD SAFETY: Single atomic check-and-store operation to prevent TOCTOU race.
        The check and store must happen in the same critical section to ensure that
        if we pass the _waiting check, we're guaranteed to store the response before
        any timeout/disconnect can clear the flag.

        Previous implementation had a race window:
        1. Check _waiting==True (with lock)
        2. Release lock to process payload
        3. Timeout/disconnect sets _waiting=False
        4. Reacquire lock, check _waiting==False, ignore message
        Result: Valid response lost

        Current implementation eliminates the window by keeping the lock held during
        the entire check-and-store operation.
        """
        logger.debug(f"Received message on {msg.topic}: {len(msg.payload)} bytes")

        # Single atomic check-and-store (no lock release between check/store)
        with self._response_lock:
            if not self._waiting:
                logger.debug(
                    "Ignoring unexpected response (not waiting for any request)"
                )
                return

            # We're waiting - store response and signal event immediately
            # (msg.payload is already a bytes object in memory - just a reference)
            self._response_data = msg.payload
            self._response_event.set()

            # Note: We DON'T clear _waiting here - that's send_frame's responsibility
            # in its finally block. This ensures proper cleanup even if we race with
            # timeout/disconnect.

    def _on_disconnect(self, client: mqtt.Client, userdata: Any, rc: int) -> None:
        """MQTT disconnect callback.

        Sets connected flag to False and wakes up any waiting send_frame()
        calls to fail fast instead of waiting for timeout.
        """
        logger.info(f"Disconnected from MQTT broker (rc={rc})")
        # Update connection/waiting state and event visibility under one lock to
        # avoid races with send_frame() waiting path.
        with self._response_lock:
            self._connected = False
            # Wake up send_frame() if waiting - it will check _connected and fail fast
            self._response_event.set()
