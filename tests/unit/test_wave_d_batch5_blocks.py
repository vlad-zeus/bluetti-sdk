"""Unit tests for Wave D Batch 5 block schemas (18400, 18500, 18600, 29770, 29772)."""

from bluetti_sdk.schemas import (
    BLOCK_18400_SCHEMA,
    BLOCK_18500_SCHEMA,
    BLOCK_18600_SCHEMA,
    BLOCK_29770_SCHEMA,
    BLOCK_29772_SCHEMA,
)


def test_block_18400_contract():
    """Verify Block 18400 (EPAD_LIQUID_POINT1) schema contract."""
    assert BLOCK_18400_SCHEMA.block_id == 18400
    assert BLOCK_18400_SCHEMA.name == "EPAD_LIQUID_POINT1"
    assert BLOCK_18400_SCHEMA.min_length == 100
    assert BLOCK_18400_SCHEMA.protocol_version == 2000
    assert BLOCK_18400_SCHEMA.strict is False


def test_block_18400_field_structure():
    """Verify Block 18400 field structure and types."""
    fields = {f.name: f for f in BLOCK_18400_SCHEMA.fields}

    # Measurement point identification
    assert "point_id" in fields
    assert fields["point_id"].offset == 0
    assert fields["point_id"].required is False

    assert "point_status" in fields
    assert fields["point_status"].offset == 1

    # Measurement data
    assert "temperature" in fields
    assert fields["temperature"].unit == "0.1°C"
    assert fields["temperature"].required is False

    assert "pressure" in fields
    assert "flow_rate" in fields
    assert "level" in fields

    # Calibration
    assert "calibration_offset" in fields


def test_block_18500_contract():
    """Verify Block 18500 (EPAD_LIQUID_POINT2) schema contract."""
    assert BLOCK_18500_SCHEMA.block_id == 18500
    assert BLOCK_18500_SCHEMA.name == "EPAD_LIQUID_POINT2"
    assert BLOCK_18500_SCHEMA.min_length == 100
    assert BLOCK_18500_SCHEMA.protocol_version == 2000
    assert BLOCK_18500_SCHEMA.strict is False


def test_block_18500_field_structure():
    """Verify Block 18500 field structure and types."""
    fields = {f.name: f for f in BLOCK_18500_SCHEMA.fields}

    # Same structure as 18400
    assert "point_id" in fields
    assert "point_status" in fields
    assert "temperature" in fields
    assert fields["temperature"].unit == "0.1°C"
    assert "pressure" in fields
    assert "flow_rate" in fields
    assert "level" in fields
    assert "calibration_offset" in fields


def test_block_18600_contract():
    """Verify Block 18600 (EPAD_LIQUID_POINT3) schema contract."""
    assert BLOCK_18600_SCHEMA.block_id == 18600
    assert BLOCK_18600_SCHEMA.name == "EPAD_LIQUID_POINT3"
    assert BLOCK_18600_SCHEMA.min_length == 100
    assert BLOCK_18600_SCHEMA.protocol_version == 2000
    assert BLOCK_18600_SCHEMA.strict is False


def test_block_18600_field_structure():
    """Verify Block 18600 field structure and types."""
    fields = {f.name: f for f in BLOCK_18600_SCHEMA.fields}

    # Same structure as 18400/18500
    assert "point_id" in fields
    assert "point_status" in fields
    assert "temperature" in fields
    assert fields["temperature"].unit == "0.1°C"
    assert "pressure" in fields
    assert "flow_rate" in fields
    assert "level" in fields
    assert "calibration_offset" in fields


def test_block_29770_contract():
    """Verify Block 29770 (BOOT_UPGRADE_SUPPORT) schema contract."""
    assert BLOCK_29770_SCHEMA.block_id == 29770
    assert BLOCK_29770_SCHEMA.name == "BOOT_UPGRADE_SUPPORT"
    assert BLOCK_29770_SCHEMA.min_length == 4
    assert BLOCK_29770_SCHEMA.protocol_version == 2000
    assert BLOCK_29770_SCHEMA.strict is False


def test_block_29770_field_structure():
    """Verify Block 29770 field structure and types."""
    fields = {f.name: f for f in BLOCK_29770_SCHEMA.fields}

    # Boot upgrade support values
    assert "upgrade_supported_flag" in fields
    assert fields["upgrade_supported_flag"].offset == 0
    assert fields["upgrade_supported_flag"].required is False

    assert "upgrade_support_raw" in fields
    assert fields["upgrade_support_raw"].offset == 2
    assert fields["upgrade_support_raw"].required is False


def test_block_29772_contract():
    """Verify Block 29772 (BOOT_SOFTWARE_INFO) schema contract."""
    assert BLOCK_29772_SCHEMA.block_id == 29772
    assert BLOCK_29772_SCHEMA.name == "BOOT_SOFTWARE_INFO"
    assert BLOCK_29772_SCHEMA.min_length == 10
    assert BLOCK_29772_SCHEMA.protocol_version == 2000
    assert BLOCK_29772_SCHEMA.strict is False


def test_block_29772_field_structure():
    """Verify Block 29772 field structure and types."""
    fields = {f.name: f for f in BLOCK_29772_SCHEMA.fields}

    # First component item (10 bytes)
    assert "component_address" in fields
    assert fields["component_address"].offset == 0
    assert fields["component_address"].required is False

    assert "component_value_raw" in fields
    assert fields["component_value_raw"].offset == 2

    assert "reserved_byte_0" in fields
    assert fields["reserved_byte_0"].offset == 6

    assert "reserved_byte_3" in fields
    assert fields["reserved_byte_3"].offset == 9
