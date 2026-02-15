"""Tests for MQTT cleanup error logging.

Verifies that cleanup errors are properly logged instead of silently suppressed.
"""

import logging
from unittest.mock import Mock, patch

import pytest
from bluetti_sdk.errors import TransportError
from bluetti_sdk.transport.mqtt import MQTTConfig, MQTTTransport


@pytest.fixture
def mqtt_config():
    """Create minimal MQTT config for testing."""
    return MQTTConfig(
        device_sn="test_device",
        pfx_cert=b"fake_cert",
        cert_password="fake_password",
    )


@pytest.fixture
def mqtt_transport(mqtt_config):
    """Create MQTT transport instance."""
    return MQTTTransport(mqtt_config)


def test_connect_cleanup_logs_loop_stop_error(mqtt_transport, caplog):
    """Verify loop_stop() cleanup errors are logged on connect failure."""
    with caplog.at_level(logging.DEBUG), patch.object(
        mqtt_transport, "_setup_ssl"
    ), patch("bluetti_sdk.transport.mqtt.mqtt.Client") as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.connect.side_effect = Exception("Connection failed")
        mock_client.loop_stop.side_effect = RuntimeError("Loop stop error")

        with pytest.raises(TransportError, match="Failed to connect"):
            mqtt_transport.connect()

        assert any(
            "Error stopping MQTT loop during cleanup" in record.message
            and record.levelname == "DEBUG"
            for record in caplog.records
        ), "loop_stop cleanup error should be logged at DEBUG level"


def test_connect_cleanup_logs_disconnect_error(mqtt_transport, caplog):
    """Verify disconnect() cleanup errors are logged on connect failure."""
    with caplog.at_level(logging.DEBUG), patch.object(
        mqtt_transport, "_setup_ssl"
    ), patch("bluetti_sdk.transport.mqtt.mqtt.Client") as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mqtt_transport._connected = True
        mock_client.connect.side_effect = Exception("Connection failed")
        mock_client.disconnect.side_effect = RuntimeError("Disconnect error")

        with pytest.raises(TransportError, match="Failed to connect"):
            mqtt_transport.connect()

        assert any(
            "Error disconnecting MQTT during cleanup" in record.message
            and record.levelname == "DEBUG"
            for record in caplog.records
        ), "disconnect cleanup error should be logged at DEBUG level"


def test_cleanup_certs_logs_deletion_error(mqtt_transport, caplog):
    """Verify certificate cleanup errors are logged at WARNING level."""
    with caplog.at_level(logging.WARNING), patch(
        "os.path.exists", return_value=True
    ), patch("shutil.rmtree", side_effect=PermissionError("Permission denied")):
        mqtt_transport._temp_cert_dir = "/fake/temp/dir"
        mqtt_transport._cleanup_certs()

        assert any(
            "Failed to delete temp cert directory" in record.message
            and record.levelname == "WARNING"
            for record in caplog.records
        ), "cert cleanup error should be logged at WARNING level"


def test_cleanup_does_not_suppress_critical_errors(mqtt_transport):
    """Verify cleanup errors are logged, not silently suppressed."""
    mqtt_transport._connected = True
    mock_client = Mock()
    mock_client.loop_stop.side_effect = RuntimeError("Critical error")
    mqtt_transport._client = mock_client

    with patch.object(mqtt_transport, "_setup_ssl"), patch(
        "bluetti_sdk.transport.mqtt.mqtt.Client", return_value=mock_client
    ):
        mock_client.connect.side_effect = Exception("Connection failed")

        with pytest.raises(TransportError):
            mqtt_transport.connect()

        mock_client.loop_stop.assert_called_once()
