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
import re
import ssl
import stat
import time
import uuid
import weakref
from dataclasses import dataclass, field
from pathlib import Path
from threading import Event, Lock
from typing import Any

try:
    import paho.mqtt.client as mqtt
except ImportError:
    raise ImportError(
        "paho-mqtt is required. Install with: pip install paho-mqtt"
    ) from None

from ..contracts.transport import TransportProtocol
from ..errors import TransportError

logger = logging.getLogger(__name__)

# MQTT topic wildcard and null characters are not allowed in device serial numbers
# because device_sn is interpolated directly into topic strings (PUB/{sn}, SUB/{sn}).
# '+' and '#' are MQTT wildcards; '/' creates unintended topic hierarchy levels;
# null bytes (\x00) are disallowed by the MQTT spec.
_VALID_SN_RE = re.compile(r"^[^+#\x00/][^+#\x00]*$")


# Maximum bytes to include in debug hex dumps.  Frames for blocks 12002 (WiFi
# password) and 2200 (admin password) can carry credentials in plaintext; cap
# the log output so those bytes are never emitted in full.
_MAX_LOG_BYTES = 16


def _safe_hex(data: bytes, max_bytes: int = _MAX_LOG_BYTES) -> str:
    """Return hex of data, truncated for safe logging (may contain sensitive fields)."""
    if len(data) <= max_bytes:
        return data.hex()
    return data[:max_bytes].hex() + f"...[{len(data)} bytes total]"

@dataclass
class MQTTConfig:
    """MQTT connection configuration.

    TLS is required by default.  Set ``allow_insecure=True`` only for
    local development / testing against a broker that does not use TLS.
    """

    broker: str = "localhost"
    port: int = 1883
    device_sn: str = ""
    pfx_cert: bytes | None = None
    cert_password: str | None = field(default=None, repr=False)
    keepalive: int = 60
    allow_insecure: bool = False

    def __post_init__(self) -> None:
        # Validate device_sn only when a non-empty value is supplied.
        # An empty device_sn is caught later in MQTTTransport.connect() with
        # a more descriptive error; rejecting it here would break the common
        # pattern of constructing MQTTConfig() with no arguments in tests.
        if self.device_sn and not _VALID_SN_RE.match(self.device_sn):
            raise TransportError(
                f"device_sn {self.device_sn!r} contains invalid MQTT topic characters "
                f"('+', '#', '/', null are not allowed)"
            )


class MQTTTransport(TransportProtocol):
    """MQTT transport for Modbus-over-MQTT devices.

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
        self._client: mqtt.Client | None = None
        self._connected = False
        self._connect_event = Event()
        self._connect_rc: int | None = None

        # Response handling
        self._response_event = Event()
        self._response_data: bytes | None = None
        self._response_lock = Lock()
        self._waiting = False  # Flag to filter unexpected responses

        # Request serialization (enforce "single request at a time")
        self._request_lock = Lock()
        # NOTE on two-lock design: _connected is written under _response_lock
        # (in _on_disconnect) but read under _request_lock (in send_frame).
        # This is intentional: paho-mqtt's callback threading model prevents a
        # single-lock design without deadlock.  In CPython the GIL makes bare
        # bool reads/writes atomic, so the cross-lock read is safe today.
        # In a free-threading build (PEP 703) this becomes a data race and
        # would require an atomic flag or a dedicated lock for _connected.

        # Topics
        self._subscribe_topic = f"PUB/{config.device_sn}"  # Device publishes here
        self._publish_topic = f"SUB/{config.device_sn}"  # Device subscribes here

        # SSL context
        self._ssl_context: ssl.SSLContext | None = None

        # Private temp directory for certificates (owner-only permissions)
        self._temp_cert_dir: str | None = None
        self._temp_cert_file: str | None = None
        self._temp_key_file: str | None = None
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

            # Create MQTT client — unique suffix prevents broker from kicking the
            # previous session with the same client_id on reconnect.
            _client_id = (
                f"power_sdk_{self.config.device_sn}_{uuid.uuid4().hex[:8]}"
            )
            self._client = mqtt.Client(
                client_id=_client_id, protocol=mqtt.MQTTv311
            )

            # Set callbacks
            self._client.on_connect = self._on_connect
            self._client.on_subscribe = self._on_subscribe
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

            # Clear stale state BEFORE publish so a very fast response (arriving
            # between publish and the wait call) is not lost.  _waiting is set to
            # True only AFTER the broker acknowledges the publish to prevent a
            # retained/stale MQTT message from being accepted as the response.
            with self._response_lock:
                self._response_event.clear()
                self._response_data = None
                # _waiting deliberately NOT set here — set after publish is confirmed.

            # Monotonic deadline so publish + response together stay within timeout.
            deadline = time.monotonic() + timeout

            try:
                # Publish request
                # Use _safe_hex to avoid logging credential blocks in full
                logger.debug(
                    f"Publishing to {self._publish_topic}: {_safe_hex(frame)}"
                )

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

                    # Wait for publish to complete (consume part of deadline)
                    pub_remaining = max(0.0, deadline - time.monotonic())
                    result.wait_for_publish(timeout=pub_remaining)
                    if not result.is_published():
                        raise TransportError(
                            f"Publish timeout after {timeout}s (no broker ack)"
                        )
                except TransportError:
                    raise
                except Exception as e:
                    raise TransportError(f"Failed to publish: {e}") from e

                # Publish confirmed — now open the response window.
                # Any message that arrived between clear() and this point is lost,
                # but that window is tiny and corresponds to a spurious response
                # (broker retained or device reply to a previous request), which
                # we must not accept anyway.
                with self._response_lock:
                    self._waiting = True

                # Wait for response (remaining time only)
                resp_remaining = max(0.0, deadline - time.monotonic())
                logger.debug(
                    f"Waiting for response (remaining={resp_remaining:.2f}s)..."
                )

                if not self._response_event.wait(resp_remaining):
                    raise TransportError(f"Response timeout after {timeout}s")

                # Retrieve response data first, then check connection state.
                # If the response arrived concurrently with a disconnect,
                # _connected may already be False while _response_data holds
                # a valid payload — prefer the data over the connection flag.
                with self._response_lock:
                    response = self._response_data
                    self._response_data = None

                if response is not None:
                    # Use _safe_hex to avoid logging credential blocks in full
                    logger.debug(f"Received response: {_safe_hex(response)}")
                elif not self._connected:
                    raise TransportError("Connection lost while waiting for response")
                else:
                    raise TransportError("No response data received")

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
        if self.config.pfx_cert is not None and self.config.cert_password is None:
            raise TransportError("pfx_cert provided but cert_password is missing")
        if self.config.pfx_cert is None:
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
            cert_password = self.config.cert_password
            if cert_password is None:
                raise TransportError(
                    "cert_password is required when pfx_cert is provided"
                )
            private_key, certificate, _ca_certs = pkcs12.load_key_and_certificates(
                self.config.pfx_cert, cert_password.encode()
            )
            if certificate is None:
                raise TransportError("PFX bundle contains no certificate")
            if private_key is None:
                raise TransportError("PFX bundle contains no private key")

            from cryptography.hazmat.primitives import serialization

            # Create private temp directory explicitly under an SDK-owned root.
            # tempfile.mkdtemp() can produce unwritable dirs under restrictive
            # Windows ACL inheritance in some environments.
            self._temp_cert_dir = self._create_private_temp_dir()
            logger.debug(f"Created private temp directory: {self._temp_cert_dir}")

            # Register cleanup handler once to ensure deletion on process exit.
            # Use a weakref so atexit does not hold a strong reference to self,
            # which would prevent garbage collection of the MQTTTransport instance.
            if not self._atexit_cleanup_registered:
                ref = weakref.ref(self)

                def _atexit_cleanup() -> None:
                    obj = ref()
                    if obj is not None:
                        obj._cleanup_certs()

                atexit.register(_atexit_cleanup)
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

                # Create SSL context that does NOT fall back to system CAs when
                # a PFX is provided — the PFX bundle is the authoritative trust
                # anchor for corporate/private PKI deployments.
                # ssl.create_default_context() would trust system CAs even when
                # the broker uses a private CA, opening a MitM vector if the
                # private CA cert is absent from the system store.
                self._ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                # Enforce TLS 1.2 minimum — reject TLS 1.0/1.1 which are deprecated
                # (RFC 8996) and have known vulnerabilities (BEAST, POODLE).
                self._ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
                self._ssl_context.check_hostname = True
                self._ssl_context.verify_mode = ssl.CERT_REQUIRED

                # Load CA certificates extracted from the PFX bundle.
                # Without this step the SSL context would only trust system CAs,
                # causing handshake failures (or worse, silent fallback to a
                # less strict context) for brokers signed by a private CA.
                if _ca_certs:
                    for ca_cert in _ca_certs:
                        ca_pem = ca_cert.public_bytes(
                            serialization.Encoding.PEM
                        ).decode()
                        self._ssl_context.load_verify_locations(cadata=ca_pem)
                    logger.debug(
                        "Loaded %d CA certificate(s) from PFX bundle", len(_ca_certs)
                    )
                else:
                    # No CA certs in the PFX bundle.  The SSL context will trust
                    # system CAs only.  If the broker uses a private/corporate CA
                    # that is NOT in the system store, the TLS handshake will fail.
                    # Ensure the broker's CA is installed system-wide, or include
                    # it in the PFX bundle.
                    logger.warning(
                        "No CA certificates found in PFX bundle; "
                        "SSL context will trust system CAs only. "
                        "If the broker uses a private CA, add it to the PFX bundle."
                    )

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
        if os.name == "nt":
            # Windows ACLs do not map cleanly from POSIX mode bits passed to os.open.
            # Create file exclusively and set read-only attribute best-effort.
            with open(path, "xb") as f:
                f.write(data)
            with contextlib.suppress(Exception):
                os.chmod(path, stat.S_IREAD)
            return

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

    @staticmethod
    def _create_private_temp_dir() -> str:
        """Create per-connection private temp directory under a stable root."""
        root = Path.cwd() / ".power_sdk_tls_tmp"
        root.mkdir(parents=True, exist_ok=True)

        path = root / f"tls_{uuid.uuid4().hex}"
        path.mkdir(parents=False, exist_ok=False)
        return str(path)

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
        self, client: mqtt.Client, userdata: Any, flags: dict[str, Any], rc: int
    ) -> None:
        """MQTT connect callback.

        Only issues the subscribe call on success.  _connected and
        _connect_event are set in _on_subscribe once the broker ACKs the
        subscription, so we know the topic is actually available.
        """
        if rc == 0:
            logger.info(f"Connected to MQTT broker (rc={rc})")
            # Store rc for error reporting in _on_subscribe
            self._connect_rc = rc
            # Subscribe to response topic; _on_subscribe will signal readiness.
            client.subscribe(self._subscribe_topic, qos=1)
            logger.debug(f"Subscribe request sent for {self._subscribe_topic}")
        else:
            logger.error(f"Connection failed (rc={rc})")
            self._connected = False
            self._connect_rc = rc
            self._connect_event.set()

    def _on_subscribe(
        self,
        client: mqtt.Client,
        userdata: Any,
        mid: int,
        granted_qos: tuple[int, ...],
    ) -> None:
        """MQTT subscribe ACK callback.

        Broker signals success with granted_qos[0] < 0x80.
        Values >= 0x80 (128, 135 …) indicate ACL rejection or other failure.
        Only after a successful ACK do we mark the transport as connected.
        """
        qos_value = granted_qos[0] if granted_qos else 0x80
        if qos_value >= 0x80:
            logger.error(
                "Subscribe to %r rejected by broker (granted_qos=0x%02X); "
                "check ACL/permissions",
                self._subscribe_topic,
                qos_value,
            )
            self._connected = False
            self._connect_rc = qos_value
            self._connect_event.set()
        else:
            logger.info(
                "Subscribed to %r (granted_qos=%d)", self._subscribe_topic, qos_value
            )
            self._connected = True
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
        if msg.topic != self._subscribe_topic:
            logger.warning(
                "Received message on unexpected topic %r (expected %r), ignoring",
                msg.topic,
                self._subscribe_topic,
            )
            return
        retain = getattr(msg, "retain", False)
        if isinstance(retain, (bool, int)) and bool(retain):
            logger.warning(
                "Ignoring retained MQTT message on %r to avoid stale response reuse",
                msg.topic,
            )
            return

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

        Stale-callback guard: if this callback fires from a previous paho client
        instance (e.g. after a reconnect replaced self._client), ignore it.
        Without this guard the old callback can set _connected=False on the NEW
        connection, causing the next send_frame() to fail spuriously.
        """
        if client is not self._client:
            logger.debug(
                "Ignoring stale _on_disconnect from replaced paho client (rc=%d)", rc
            )
            return
        logger.info(f"Disconnected from MQTT broker (rc={rc})")
        # Update connection/waiting state and event visibility under one lock to
        # avoid races with send_frame() waiting path.
        with self._response_lock:
            self._connected = False
            # Wake up send_frame() if waiting — it will check _connected and fail fast.
            # Only signal if someone is actually waiting to avoid spurious wakeups.
            if self._waiting:
                self._response_event.set()
