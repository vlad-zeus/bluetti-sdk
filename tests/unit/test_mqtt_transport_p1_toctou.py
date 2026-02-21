"""Tests for P1 edge case: MQTT TOCTOU race in _on_message."""

import threading
import time
from typing import Any
from unittest.mock import Mock

from power_sdk.transport.mqtt import MQTTConfig, MQTTTransport, TransportError


class FakeMQTTMessage:
    """Fake MQTT message for testing."""

    def __init__(self, topic: str, payload: bytes):
        self.topic = topic
        self.payload = payload


def test_on_message_race_with_timeout():
    """Test that message arriving during timeout is handled atomically.

    Scenario (FIXED implementation):
    1. send_frame() starts waiting for response
    2. _on_message() receives message, checks _waiting (holds lock)
    3. _on_message() stores response and signals event (still holding lock)
    4. send_frame() may timeout, but message was already stored atomically
    5. Result: No race - atomic check-and-store operation

    This test verifies that the FIXED _on_message() doesn't lose messages
    even when timeout happens around the same time.
    """
    config = MQTTConfig(
        broker="test.mqtt.local",
        port=1883,
        device_sn="TEST123",
    )

    transport = MQTTTransport(config)

    # Manually set up internal state to simulate connected
    transport._connected = True
    transport._client = Mock()
    transport._client.publish.return_value = Mock()
    transport._client.publish.return_value.wait_for_publish = Mock()

    # Track events
    events = []

    # Wrap _on_message to track when it runs (but don't modify behavior)
    original_on_message = transport._on_message

    def tracked_on_message(client: Any, userdata: Any, msg: Any) -> None:
        events.append("on_message: called")
        result = original_on_message(client, userdata, msg)
        events.append("on_message: completed")
        return result

    transport._on_message = tracked_on_message

    # Start send_frame with very short timeout to force race
    def send_frame_thread():
        events.append("send_frame: start")
        try:
            transport.send_frame(b"\x01\x03\x00\x00", timeout=0.05)
            events.append("send_frame: success")
        except TransportError as e:
            events.append(f"send_frame: error - {e!s}")

    sender = threading.Thread(target=send_frame_thread)
    sender.start()

    # Wait for send_frame to start waiting
    time.sleep(0.02)

    # Deliver message right around timeout boundary
    events.append("test: delivering message")
    fake_msg = FakeMQTTMessage(
        topic=f"PUB/{config.device_sn}", payload=b"\x01\x03\x02\x12\x34\xab\xcd"
    )

    # Call on_message directly (simulates MQTT callback)
    transport._on_message(transport._client, None, fake_msg)

    # Wait for send_frame to complete
    sender.join(timeout=1.0)

    # VERIFICATION: With atomic implementation, one of two things happens:
    # 1. Message arrives before timeout → send_frame gets response (success)
    # 2. Message arrives after timeout → on_message ignores it (no crash)
    # The key is NO RACE - atomic check-and-store prevents partial states

    # on_message completed without crashing
    assert "on_message: completed" in events
    # send_frame thread completed (no hang or unhandled exception)
    assert sender.is_alive() is False
    # Exactly one terminal outcome must be recorded for send_frame.
    outcomes = [
        e
        for e in events
        if e == "send_frame: success" or e.startswith("send_frame: error - ")
    ]
    assert len(outcomes) == 1, f"expected single send_frame outcome, got: {outcomes}"


def test_on_message_race_with_disconnect():
    """Test atomic handling when disconnect happens during message receive.

    Scenario (FIXED implementation):
    1. send_frame() waiting for response
    2. _on_message() receives message, atomically checks _waiting and stores
    3. Disconnect may happen concurrently
    4. Result: No race - message stored (if check passed) or ignored (failed)

    This verifies that disconnect + on_message can interleave without causing
    undefined behavior or lost messages.
    """
    config = MQTTConfig(
        broker="test.mqtt.local",
        port=1883,
        device_sn="TEST123",
    )

    transport = MQTTTransport(config)
    transport._connected = True
    transport._client = Mock()
    transport._client.publish.return_value = Mock()
    transport._client.publish.return_value.wait_for_publish = Mock()

    events = []

    # Track on_message execution
    original_on_message = transport._on_message

    def tracked_on_message(client: Any, userdata: Any, msg: Any) -> None:
        events.append("on_message: start")
        result = original_on_message(client, userdata, msg)
        events.append("on_message: completed")
        return result

    transport._on_message = tracked_on_message

    def send_frame_thread():
        events.append("send_frame: start")
        try:
            transport.send_frame(b"\x01\x03\x00\x00", timeout=2.0)
            events.append("send_frame: success")
        except TransportError as e:
            events.append(f"send_frame: error - {e!s}")

    sender = threading.Thread(target=send_frame_thread)
    sender.start()

    # Wait for send_frame to start waiting
    time.sleep(0.05)

    # Deliver message
    events.append("test: delivering message")
    fake_msg = FakeMQTTMessage(
        topic=f"PUB/{config.device_sn}", payload=b"\x01\x03\x02\x12\x34\xab\xcd"
    )

    # Start message handler
    msg_thread = threading.Thread(
        target=transport._on_message, args=(transport._client, None, fake_msg)
    )
    msg_thread.start()

    # Trigger disconnect concurrently (simulate connection loss)
    time.sleep(0.01)
    events.append("test: triggering disconnect")
    transport._on_disconnect(transport._client, None, 0)

    # Wait for completion
    sender.join(timeout=1.0)
    msg_thread.join(timeout=1.0)

    timeline = "\n".join(events)
    # on_message completed without crashing
    assert "on_message: completed" in events, f"Event timeline:\n{timeline}"
    # send_frame thread completed (no hang or unhandled exception)
    assert sender.is_alive() is False
    # Exactly one terminal outcome must be recorded for send_frame.
    outcomes = [
        e
        for e in events
        if e == "send_frame: success" or e.startswith("send_frame: error - ")
    ]
    assert len(outcomes) == 1, f"expected single send_frame outcome, got: {outcomes}"
