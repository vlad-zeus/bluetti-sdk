"""Smoke tests for Wave A block schemas (1100, 1400, 1500, 6100).

Tests that the new schemas are properly registered and can be read
via Client without errors.
"""

from unittest.mock import Mock

import pytest
from power_sdk.contrib.bluetti import build_bluetti_client
from power_sdk.models.types import BlockGroup


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
def mock_transport():
    """Mock transport that returns valid but minimal responses."""
    transport = Mock()
    transport.is_connected = False
    return transport


def build_minimal_response(block_id: int, data_length: int) -> bytes:
    """Build minimal valid Modbus response for a block.

    Args:
        block_id: Block ID (not used in response, just for documentation)
        data_length: Number of data bytes to include

    Returns:
        Valid Modbus RTU response frame with CRC
    """
    _ = block_id  # Block ID is for caller readability in tests
    # Create minimal data (all zeros)
    data = bytes(data_length)
    # Build response using test helper
    return build_test_response(data)


def test_block_1100_registered_and_parseable(mock_transport):
    """Test Block 1100 (INV_BASE_INFO) is registered and can be parsed."""
    from power_sdk.plugins.bluetti.v2.schemas import BLOCK_1100_SCHEMA

    # Verify schema is accessible
    assert BLOCK_1100_SCHEMA.block_id == 1100
    assert BLOCK_1100_SCHEMA.name == "INV_BASE_INFO"

    # Create client with EL100V2 profile via contrib builder
    client = build_bluetti_client("EL100V2", mock_transport)

    # Verify schema is registered in parser
    schema = client.parser.get_schema(1100)
    assert schema is not None
    assert schema.block_id == 1100

    # Verify can parse minimal data without errors
    min_data_length = BLOCK_1100_SCHEMA.min_length
    response = build_minimal_response(1100, min_data_length)
    mock_transport.send_frame.return_value = response
    mock_transport.is_connected = True

    # Should not raise
    parsed = client.read_block(1100, register_count=min_data_length // 2)
    assert parsed.block_id == 1100
    assert parsed.name == "INV_BASE_INFO"


def test_block_1400_registered_and_parseable(mock_transport):
    """Test Block 1400 (INV_LOAD_INFO) is registered and can be parsed."""
    from power_sdk.plugins.bluetti.v2.schemas import BLOCK_1400_SCHEMA

    # Verify schema is accessible
    assert BLOCK_1400_SCHEMA.block_id == 1400
    assert BLOCK_1400_SCHEMA.name == "INV_LOAD_INFO"

    # Create client with EL100V2 profile via contrib builder
    client = build_bluetti_client("EL100V2", mock_transport)

    # Verify schema is registered in parser
    schema = client.parser.get_schema(1400)
    assert schema is not None
    assert schema.block_id == 1400

    # Verify can parse minimal data without errors
    min_data_length = BLOCK_1400_SCHEMA.min_length
    response = build_minimal_response(1400, min_data_length)
    mock_transport.send_frame.return_value = response
    mock_transport.is_connected = True

    # Should not raise
    parsed = client.read_block(1400, register_count=min_data_length // 2)
    assert parsed.block_id == 1400
    assert parsed.name == "INV_LOAD_INFO"


def test_block_1500_registered_and_parseable(mock_transport):
    """Test Block 1500 (INV_INV_INFO) is registered and can be parsed."""
    from power_sdk.plugins.bluetti.v2.schemas import BLOCK_1500_SCHEMA

    # Verify schema is accessible
    assert BLOCK_1500_SCHEMA.block_id == 1500
    assert BLOCK_1500_SCHEMA.name == "INV_INV_INFO"

    # Create client with EL100V2 profile via contrib builder
    client = build_bluetti_client("EL100V2", mock_transport)

    # Verify schema is registered in parser
    schema = client.parser.get_schema(1500)
    assert schema is not None
    assert schema.block_id == 1500

    # Verify can parse minimal data without errors
    min_data_length = BLOCK_1500_SCHEMA.min_length
    response = build_minimal_response(1500, min_data_length)
    mock_transport.send_frame.return_value = response
    mock_transport.is_connected = True

    # Should not raise
    parsed = client.read_block(1500, register_count=min_data_length // 2)
    assert parsed.block_id == 1500
    assert parsed.name == "INV_INV_INFO"


def test_block_6100_registered_and_parseable(mock_transport):
    """Test Block 6100 (PACK_ITEM_INFO) is registered and can be parsed."""
    from power_sdk.plugins.bluetti.v2.schemas import BLOCK_6100_SCHEMA

    # Verify schema is accessible
    assert BLOCK_6100_SCHEMA.block_id == 6100
    assert BLOCK_6100_SCHEMA.name == "PACK_ITEM_INFO"

    # Create client with EL100V2 profile via contrib builder
    client = build_bluetti_client("EL100V2", mock_transport)

    # Verify schema is registered in parser
    schema = client.parser.get_schema(6100)
    assert schema is not None
    assert schema.block_id == 6100

    # Verify can parse minimal data without errors
    min_data_length = BLOCK_6100_SCHEMA.min_length
    response = build_minimal_response(6100, min_data_length)
    mock_transport.send_frame.return_value = response
    mock_transport.is_connected = True

    # Should not raise
    parsed = client.read_block(6100, register_count=min_data_length // 2)
    assert parsed.block_id == 6100
    assert parsed.name == "PACK_ITEM_INFO"


def test_inverter_group_includes_wave_a_blocks(mock_transport):
    """Test that EL100V2 inverter group includes blocks 1100, 1400, 1500."""
    client = build_bluetti_client("EL100V2", mock_transport)

    # Check inverter group definition (using string key, not enum)
    assert "inverter" in client.profile.groups
    inverter_blocks = client.profile.groups["inverter"].blocks

    # Verify all three inverter blocks are present
    assert 1100 in inverter_blocks
    assert 1400 in inverter_blocks
    assert 1500 in inverter_blocks

    # Verify all schemas are registered in parser
    for block_id in [1100, 1400, 1500]:
        schema = client.parser.get_schema(block_id)
        assert schema is not None, f"Block {block_id} schema not registered"


def test_cells_group_includes_block_6100(mock_transport):
    """Test that EL100V2 cells group includes block 6100."""
    client = build_bluetti_client("EL100V2", mock_transport)

    # Check cells group definition (using string key, not enum)
    assert "cells" in client.profile.groups
    cells_blocks = client.profile.groups["cells"].blocks

    # Verify block 6100 is present
    assert 6100 in cells_blocks

    # Verify schema is registered in parser
    schema = client.parser.get_schema(6100)
    assert schema is not None


def test_inverter_group_read_with_wave_a_schemas(mock_transport):
    """Test read_group() works with inverter group (blocks 1100, 1400, 1500)."""
    client = build_bluetti_client("EL100V2", mock_transport)

    # Mock responses for all three blocks
    expected_lengths = {1100: 62, 1400: 72, 1500: 30}

    def send_frame_side_effect(frame, timeout=5.0):
        _ = timeout
        block_id = int.from_bytes(frame[2:4], "big")
        return build_minimal_response(block_id, expected_lengths[block_id])

    mock_transport.send_frame.side_effect = send_frame_side_effect
    mock_transport.is_connected = True

    # Read inverter group (should attempt to read all 3 blocks)
    results = client.read_group(BlockGroup.INVERTER, partial_ok=True)

    assert len(results) == 3
    assert {parsed.block_id for parsed in results} == {1100, 1400, 1500}
    assert mock_transport.send_frame.call_count == 3


def test_min_length_validation_for_wave_a_blocks():
    """Test that min_length is sensible for all Wave A blocks."""
    from power_sdk.plugins.bluetti.v2.schemas import (
        BLOCK_1100_SCHEMA,
        BLOCK_1400_SCHEMA,
        BLOCK_1500_SCHEMA,
        BLOCK_6100_SCHEMA,
    )

    # Block 1100: basic fields (25) + 6 software modules (36) = 61+
    assert BLOCK_1100_SCHEMA.min_length >= 62

    # Block 1400: phase_0_apparent at offset 66+size 2=68 (corrected from 72)
    assert BLOCK_1400_SCHEMA.min_length >= 68

    # Block 1500: global fields (18) + Phase 0 (12) = 30+
    assert BLOCK_1500_SCHEMA.min_length >= 30

    # Block 6100: fixed fields up to software_number (160)
    assert BLOCK_6100_SCHEMA.min_length >= 160
