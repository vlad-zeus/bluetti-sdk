"""Mock-based unit tests for MQTT transport layer.

These tests use mocks to test MQTT transport without real broker connection.
Covers thread-safety, timeout handling, and response validation.
"""

from contextlib import suppress
from unittest.mock import MagicMock, Mock, patch

import pytest
from power_sdk.errors import TransportError
from power_sdk.plugins.bluetti.v2.protocol.modbus import build_modbus_request
from power_sdk.transport.mqtt import MQTTConfig, MQTTTransport


def build_test_response(data: bytes) -> bytes:
    """Build valid Modbus response frame with CRC.

    Args:
        data: Raw data bytes (without framing)

    Returns:
        Complete Modbus frame with valid CRC
    """
    # Build frame: [addr][func][count][data...][crc]
    device_addr = 0x01
    function_code = 0x03
    byte_count = len(data)

    frame = bytes([device_addr, function_code, byte_count]) + data

    # Calculate CRC16-Modbus
    crc = 0xFFFF
    for byte in frame:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1

    # Append CRC (little-endian)
    frame_with_crc = frame + bytes([crc & 0xFF, (crc >> 8) & 0xFF])

    return frame_with_crc


@pytest.fixture
def mqtt_config():
    """Create test MQTT config without real certificates."""
    return MQTTConfig(broker="test.broker.com", port=18760, device_sn="TEST_DEVICE_001")


@pytest.fixture
def mock_mqtt_client():
    """Create mock paho MQTT client."""
    mock_client = MagicMock()

    # Mock successful operations
    mock_client.connect.return_value = 0
    mock_client.subscribe.return_value = (0, 1)
    mock_client.publish.return_value = MagicMock(wait_for_publish=MagicMock())
    mock_client.loop_start.return_value = None
    mock_client.loop_stop.return_value = None
    mock_client.disconnect.return_value = None

    return mock_client


class TestMQTTConfig:
    """Test MQTTConfig dataclass."""

    def test_config_defaults(self):
        """Test default values."""
        config = MQTTConfig(device_sn="TEST")

        assert config.broker == "iot.bluettipower.com"
        assert config.port == 18760
        assert config.device_sn == "TEST"
        assert config.pfx_cert is None
        assert config.cert_password is None
        assert config.keepalive == 60

    def test_config_custom_values(self):
        """Test custom configuration."""
        config = MQTTConfig(
            broker="custom.broker.com",
            port=8883,
            device_sn="CUSTOM_DEVICE",
            keepalive=120,
        )

        assert config.broker == "custom.broker.com"
        assert config.port == 8883
        assert config.device_sn == "CUSTOM_DEVICE"
        assert config.keepalive == 120


class TestMQTTTransportCreation:
    """Test MQTT transport initialization."""

    @patch("power_sdk.transport.mqtt.mqtt.Client")
    def test_transport_creation(self, mock_client_class, mqtt_config):
        """Test creating transport."""
        transport = MQTTTransport(mqtt_config)

        assert transport.config == mqtt_config
        assert not transport._connected
        assert transport._waiting is False
        assert transport._subscribe_topic == "PUB/TEST_DEVICE_001"
        assert transport._publish_topic == "SUB/TEST_DEVICE_001"

    @patch("power_sdk.transport.mqtt.mqtt.Client")
    def test_topics_generation(self, mock_client_class, mqtt_config):
        """Test topic name generation."""
        transport = MQTTTransport(mqtt_config)

        # From client perspective:
        # - Subscribe to device's publish topic (PUB/{sn})
        # - Publish to device's subscribe topic (SUB/{sn})
        assert transport._subscribe_topic == "PUB/TEST_DEVICE_001"
        assert transport._publish_topic == "SUB/TEST_DEVICE_001"


class TestMQTTConnection:
    """Test MQTT connection lifecycle."""

    @patch("power_sdk.transport.mqtt.mqtt.Client")
    def test_connect_success(self, mock_client_class, mqtt_config, mock_mqtt_client):
        """Test successful connection."""
        mock_client_class.return_value = mock_mqtt_client

        transport = MQTTTransport(mqtt_config)

        # Mock successful connection via callback
        def trigger_on_connect(*args, **kwargs):
            # Simulate connection callback
            transport._on_connect(mock_mqtt_client, None, None, 0)

        mock_mqtt_client.connect.side_effect = trigger_on_connect

        transport.connect()

        # Verify connection sequence (keyword argument)
        mock_mqtt_client.connect.assert_called_once_with(
            "test.broker.com", 18760, keepalive=60
        )
        mock_mqtt_client.loop_start.assert_called_once()
        assert transport.is_connected()

    @patch("power_sdk.transport.mqtt.mqtt.Client")
    def test_connect_failure(self, mock_client_class, mqtt_config, mock_mqtt_client):
        """Test connection failure."""
        mock_client_class.return_value = mock_mqtt_client
        mock_mqtt_client.connect.side_effect = Exception("Connection refused")

        transport = MQTTTransport(mqtt_config)

        with pytest.raises(TransportError, match="Failed to connect"):
            transport.connect()

        assert not transport.is_connected()

    @patch("power_sdk.transport.mqtt.mqtt.Client")
    def test_connect_failure_rc(self, mock_client_class, mqtt_config, mock_mqtt_client):
        """Test broker connection reject (rc != 0) fails fast with rc."""
        mock_client_class.return_value = mock_mqtt_client

        transport = MQTTTransport(mqtt_config)

        def trigger_on_connect_fail(*args, **kwargs):
            transport._on_connect(mock_mqtt_client, None, None, 5)

        mock_mqtt_client.connect.side_effect = trigger_on_connect_fail

        with pytest.raises(TransportError, match=r"rc=5"):
            transport.connect()

    @patch("power_sdk.transport.mqtt.mqtt.Client")
    def test_connect_failure_cleanup(
        self, mock_client_class, mqtt_config, mock_mqtt_client
    ):
        """Test connect() failure triggers proper cleanup to prevent resource leak.

        When connect() fails after loop_start(), it must:
        1. Stop the network loop
        2. Reset _connected flag
        3. Reset _client reference
        This prevents resource accumulation during retry scenarios.
        """
        mock_client_class.return_value = mock_mqtt_client

        # Simulate connection timeout after loop_start()
        def connect_side_effect(*args, **kwargs):
            # Connection succeeds at protocol level
            pass

        mock_mqtt_client.connect.side_effect = connect_side_effect

        transport = MQTTTransport(mqtt_config)

        # Connection will timeout waiting for _connect_event
        with pytest.raises(TransportError, match="Connection timeout"):
            transport.connect()

        # Verify cleanup happened
        mock_mqtt_client.loop_stop.assert_called_once()
        assert transport._connected is False
        assert transport._client is None

    @patch("power_sdk.transport.mqtt.mqtt.Client")
    def test_disconnect(self, mock_client_class, mqtt_config, mock_mqtt_client):
        """Test disconnection."""
        mock_client_class.return_value = mock_mqtt_client

        transport = MQTTTransport(mqtt_config)

        # Simulate connected state
        transport._connected = True
        transport._client = mock_mqtt_client

        transport.disconnect()

        mock_mqtt_client.unsubscribe.assert_called_once_with("PUB/TEST_DEVICE_001")
        mock_mqtt_client.disconnect.assert_called_once()
        mock_mqtt_client.loop_stop.assert_called_once()
        assert not transport.is_connected()

    @patch("power_sdk.transport.mqtt.mqtt.Client")
    def test_disconnect_when_not_connected(
        self, mock_client_class, mqtt_config, mock_mqtt_client
    ):
        """Test disconnect when not connected."""
        mock_client_class.return_value = mock_mqtt_client

        transport = MQTTTransport(mqtt_config)
        transport._client = mock_mqtt_client

        # Should not raise
        transport.disconnect()

        # Should still cleanup
        mock_mqtt_client.loop_stop.assert_called_once()


class TestMQTTSendFrame:
    """Test send_frame operation."""

    @patch("power_sdk.transport.mqtt.mqtt.Client")
    def test_send_frame_success(self, mock_client_class, mqtt_config, mock_mqtt_client):
        """Test successful send and receive."""
        mock_client_class.return_value = mock_mqtt_client

        transport = MQTTTransport(mqtt_config)
        transport._connected = True
        transport._client = mock_mqtt_client

        # Build valid Modbus response with correct CRC
        test_data = bytes([0x00, 0x64, 0x00, 0xC8])  # 4 bytes of data
        response_data = build_test_response(test_data)

        # Simulate response via callback
        def trigger_response(*args, **kwargs):
            # Create mock message
            mock_msg = Mock()
            mock_msg.topic = "PUB/TEST_DEVICE_001"
            mock_msg.payload = response_data

            # Trigger on_message callback
            transport._on_message(mock_mqtt_client, None, mock_msg)

            return MagicMock(wait_for_publish=MagicMock())

        mock_mqtt_client.publish.side_effect = trigger_response

        # Send frame
        request = build_modbus_request(
            device_address=1, block_address=100, register_count=2
        )
        result = transport.send_frame(request, timeout=5.0)

        assert result == response_data
        mock_mqtt_client.publish.assert_called_once()

    @patch("power_sdk.transport.mqtt.mqtt.Client")
    def test_send_frame_timeout(self, mock_client_class, mqtt_config, mock_mqtt_client):
        """Test timeout when no response."""
        mock_client_class.return_value = mock_mqtt_client

        transport = MQTTTransport(mqtt_config)
        transport._connected = True
        transport._client = mock_mqtt_client

        # Don't trigger response - let it timeout
        mock_mqtt_client.publish.return_value = MagicMock(wait_for_publish=MagicMock())

        request = bytes([0x01, 0x03, 0x00, 0x64, 0x00, 0x02, 0x00, 0x00])

        with pytest.raises(TransportError, match="timeout"):
            transport.send_frame(request, timeout=0.1)

        # Verify waiting flag is cleared
        assert not transport._waiting

    @patch("power_sdk.transport.mqtt.mqtt.Client")
    def test_send_frame_not_connected(
        self, mock_client_class, mqtt_config, mock_mqtt_client
    ):
        """Test sending when not connected."""
        mock_client_class.return_value = mock_mqtt_client

        transport = MQTTTransport(mqtt_config)
        # Don't set _connected

        request = bytes([0x01, 0x03, 0x00, 0x64, 0x00, 0x02, 0x00, 0x00])

        with pytest.raises(TransportError, match="Not connected"):
            transport.send_frame(request)

    @patch("power_sdk.transport.mqtt.mqtt.Client")
    def test_send_frame_publish_failure(
        self, mock_client_class, mqtt_config, mock_mqtt_client
    ):
        """Test publish failure."""
        mock_client_class.return_value = mock_mqtt_client

        transport = MQTTTransport(mqtt_config)
        transport._connected = True
        transport._client = mock_mqtt_client

        mock_mqtt_client.publish.side_effect = Exception("Publish failed")

        request = bytes([0x01, 0x03, 0x00, 0x64, 0x00, 0x02, 0x00, 0x00])

        with pytest.raises(TransportError, match="Failed to publish"):
            transport.send_frame(request)

        # Verify waiting flag is cleared
        assert not transport._waiting


class TestMQTTResponseValidation:
    """Test response validation in on_message callback."""

    @patch("power_sdk.transport.mqtt.mqtt.Client")
    def test_ignore_unexpected_response(
        self, mock_client_class, mqtt_config, mock_mqtt_client
    ):
        """Test ignoring response when not waiting."""
        mock_client_class.return_value = mock_mqtt_client

        transport = MQTTTransport(mqtt_config)
        transport._waiting = False

        mock_msg = Mock()
        mock_msg.payload = build_test_response(bytes([0x00, 0x64, 0x00, 0xC8]))

        # Should not raise, just ignore
        transport._on_message(mock_mqtt_client, None, mock_msg)

        # Should not store response
        assert transport._response_data is None

    @patch("power_sdk.transport.mqtt.mqtt.Client")
    def test_transport_accepts_any_payload(
        self, mock_client_class, mqtt_config, mock_mqtt_client
    ):
        """Test that transport accepts any payload without validation.

        Transport layer is now protocol-agnostic and just passes bytes.
        Validation (CRC, function code, length) happens in protocol layer.
        """
        mock_client_class.return_value = mock_mqtt_client

        transport = MQTTTransport(mqtt_config)
        transport._waiting = True

        # Test 1: Too short payload - should be accepted
        mock_msg = Mock()
        mock_msg.payload = bytes([0x01, 0x03])
        transport._on_message(mock_mqtt_client, None, mock_msg)
        assert transport._response_data == bytes([0x01, 0x03])

        # Reset for next test
        transport._response_data = None
        transport._response_event.clear()

        # Test 2: Invalid function code - should be accepted
        mock_msg.payload = bytes([0x01, 0x04, 0x04, 0x00, 0x64, 0x00, 0xC8, 0x00, 0x00])
        transport._on_message(mock_mqtt_client, None, mock_msg)
        assert transport._response_data == bytes(
            [0x01, 0x04, 0x04, 0x00, 0x64, 0x00, 0xC8, 0x00, 0x00]
        )

        # Reset for next test
        transport._response_data = None
        transport._response_event.clear()

        # Test 3: Invalid CRC - should be accepted
        mock_msg.payload = bytes([0x01, 0x03, 0x04, 0x00, 0x64, 0x00, 0xC8, 0xFF, 0xFF])
        transport._on_message(mock_mqtt_client, None, mock_msg)
        assert transport._response_data == bytes(
            [0x01, 0x03, 0x04, 0x00, 0x64, 0x00, 0xC8, 0xFF, 0xFF]
        )

    @patch("power_sdk.transport.mqtt.mqtt.Client")
    def test_ignore_late_response(
        self, mock_client_class, mqtt_config, mock_mqtt_client
    ):
        """Test ignoring response that arrives after timeout."""
        mock_client_class.return_value = mock_mqtt_client

        transport = MQTTTransport(mqtt_config)

        # Set waiting initially
        transport._waiting = True

        # Simulate timeout (waiting flag cleared)
        transport._waiting = False

        mock_msg = Mock()
        mock_msg.payload = build_test_response(bytes([0x00, 0x64, 0x00, 0xC8]))

        transport._on_message(mock_mqtt_client, None, mock_msg)

        # Should not store late response
        assert transport._response_data is None


class TestMQTTCallbacks:
    """Test MQTT callback handlers."""

    @patch("power_sdk.transport.mqtt.mqtt.Client")
    def test_on_connect_success(self, mock_client_class, mqtt_config, mock_mqtt_client):
        """Test on_connect callback with success."""
        mock_client_class.return_value = mock_mqtt_client

        transport = MQTTTransport(mqtt_config)

        transport._on_connect(mock_mqtt_client, None, None, 0)

        assert transport._connected
        mock_mqtt_client.subscribe.assert_called_once_with("PUB/TEST_DEVICE_001", qos=1)

    @patch("power_sdk.transport.mqtt.mqtt.Client")
    def test_on_connect_failure(self, mock_client_class, mqtt_config, mock_mqtt_client):
        """Test on_connect callback with failure."""
        mock_client_class.return_value = mock_mqtt_client

        transport = MQTTTransport(mqtt_config)

        transport._on_connect(mock_mqtt_client, None, None, 5)  # rc != 0

        assert not transport._connected
        mock_mqtt_client.subscribe.assert_not_called()

    @patch("power_sdk.transport.mqtt.mqtt.Client")
    def test_on_disconnect(self, mock_client_class, mqtt_config, mock_mqtt_client):
        """Test on_disconnect callback."""
        mock_client_class.return_value = mock_mqtt_client

        transport = MQTTTransport(mqtt_config)
        transport._connected = True

        transport._on_disconnect(mock_mqtt_client, None, 0)

        assert not transport._connected


class TestMQTTThreadSafety:
    """Test thread-safety of MQTT transport."""

    @patch("power_sdk.transport.mqtt.mqtt.Client")
    def test_request_serialization(
        self, mock_client_class, mqtt_config, mock_mqtt_client
    ):
        """Test that requests are serialized (one at a time)."""
        mock_client_class.return_value = mock_mqtt_client

        transport = MQTTTransport(mqtt_config)
        transport._connected = True
        transport._client = mock_mqtt_client

        # Verify request lock exists
        assert hasattr(transport, "_request_lock")

        # Multiple sends should be serialized via lock
        # (Can't easily test actual concurrency in unit test,
        #  but verify lock is acquired)

        # Build valid response
        test_data = bytes([0x00, 0x64, 0x00, 0xC8])
        response_data = build_test_response(test_data)

        def trigger_response(*args, **kwargs):
            mock_msg = Mock()
            mock_msg.payload = response_data
            transport._on_message(mock_mqtt_client, None, mock_msg)
            return MagicMock(wait_for_publish=MagicMock())

        mock_mqtt_client.publish.side_effect = trigger_response

        request = build_modbus_request(
            device_address=1, block_address=100, register_count=2
        )

        # First request
        result1 = transport.send_frame(request)
        assert result1 == response_data
        assert not transport._waiting  # Cleared after request

        # Second request (should work sequentially)
        result2 = transport.send_frame(request)
        assert result2 == response_data
        assert not transport._waiting

    @patch("power_sdk.transport.mqtt.mqtt.Client")
    def test_waiting_flag_cleanup_on_exception(
        self, mock_client_class, mqtt_config, mock_mqtt_client
    ):
        """Test that waiting flag is cleared even on exception."""
        mock_client_class.return_value = mock_mqtt_client

        transport = MQTTTransport(mqtt_config)
        transport._connected = True
        transport._client = mock_mqtt_client

        mock_mqtt_client.publish.side_effect = Exception("Publish failed")

        request = bytes([0x01, 0x03, 0x00, 0x64, 0x00, 0x02, 0x00, 0x00])

        with suppress(TransportError):
            transport.send_frame(request)

        # Waiting flag should be cleared (via finally block)
        assert not transport._waiting

    @patch("power_sdk.transport.mqtt.mqtt.Client")
    def test_send_frame_fail_fast_on_disconnect_during_wait(
        self, mock_client_class, mqtt_config, mock_mqtt_client
    ):
        """Test send_frame fails fast when disconnect happens during wait.

        Instead of waiting for full timeout, send_frame should detect
        disconnect and raise TransportError immediately.
        """
        import threading
        import time

        mock_client_class.return_value = mock_mqtt_client

        transport = MQTTTransport(mqtt_config)
        transport._connected = True
        transport._client = mock_mqtt_client

        # Track when wait started
        wait_started = threading.Event()

        def trigger_disconnect(*args, **kwargs):
            # Wait a bit then trigger disconnect
            wait_started.set()
            time.sleep(0.1)  # Short delay
            transport._on_disconnect(mock_mqtt_client, None, 0)
            return MagicMock(wait_for_publish=MagicMock())

        mock_mqtt_client.publish.side_effect = trigger_disconnect

        request = build_modbus_request(
            device_address=1, block_address=100, register_count=2
        )

        # Should fail fast with connection lost error
        # NOT timeout error (which would take 5s)
        start_time = time.time()

        with pytest.raises(TransportError, match="Connection lost while waiting"):
            transport.send_frame(request, timeout=5.0)

        elapsed = time.time() - start_time

        # Should fail in < 1s (much faster than 5s timeout)
        assert elapsed < 1.0

        # Verify disconnect was detected
        assert not transport._connected

