"""Tests for MQTT cleanup error logging.

Verifies that cleanup errors are properly logged instead of silently suppressed.
"""

import logging
from unittest.mock import Mock, patch

import pytest
from power_sdk.errors import TransportError
from power_sdk.transport.mqtt import MQTTConfig, MQTTTransport


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
    ), patch("power_sdk.transport.mqtt.mqtt.Client") as mock_client_class:
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
    ), patch("power_sdk.transport.mqtt.mqtt.Client") as mock_client_class:
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
    """Verify cleanup errors during failed connect are logged, not swallowed.

    When a new connection attempt fails and loop_stop() raises during cleanup,
    connect() must still raise TransportError (not the raw RuntimeError).
    """
    with patch.object(mqtt_transport, "_setup_ssl"), patch(
        "power_sdk.transport.mqtt.mqtt.Client"
    ) as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.connect.side_effect = Exception("Connection failed")
        mock_client.loop_stop.side_effect = RuntimeError("Critical error")

        with pytest.raises(TransportError):
            mqtt_transport.connect()

        mock_client.loop_stop.assert_called_once()


def test_double_connect_cleanup_error_is_logged_not_raised(mqtt_transport, caplog):
    """Verify that a pre-connect cleanup error (guard path) is logged, not raised."""
    mock_client = Mock()
    mock_client.loop_stop.side_effect = RuntimeError("Loop stop failed")
    mqtt_transport._client = mock_client  # simulate existing connection

    with caplog.at_level(logging.WARNING), patch.object(
        mqtt_transport, "_setup_ssl"
    ), patch("power_sdk.transport.mqtt.mqtt.Client") as mock_client_class:
        new_client = Mock()
        mock_client_class.return_value = new_client

        def trigger_connect(*args, **kwargs):
            mqtt_transport._on_connect(new_client, None, {}, 0)

        new_client.connect.side_effect = trigger_connect

        mqtt_transport.connect()  # should succeed despite cleanup error

    assert any("Pre-connect cleanup error" in r.message for r in caplog.records), (
        "guard cleanup error should be logged at WARNING level"
    )
    assert mqtt_transport.is_connected()
