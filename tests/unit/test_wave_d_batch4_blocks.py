"""Unit tests for Wave D Batch 4 block schemas (15700, 17400, 18000, 18300, 26001)."""

from bluetti_sdk.schemas import (
    BLOCK_15700_SCHEMA,
    BLOCK_17400_SCHEMA,
    BLOCK_18000_SCHEMA,
    BLOCK_18300_SCHEMA,
    BLOCK_26001_SCHEMA,
)


def test_block_15700_contract():
    """Verify Block 15700 (DC_HUB_INFO) schema contract."""
    assert BLOCK_15700_SCHEMA.block_id == 15700
    assert BLOCK_15700_SCHEMA.name == "DC_HUB_INFO"
    assert BLOCK_15700_SCHEMA.min_length == 68
    assert BLOCK_15700_SCHEMA.protocol_version == 2000
    assert BLOCK_15700_SCHEMA.strict is False


def test_block_15700_field_structure():
    """Verify Block 15700 field structure and types."""
    fields = {f.name: f for f in BLOCK_15700_SCHEMA.fields}

    # Device identification
    assert "model" in fields
    assert fields["model"].offset == 0
    assert fields["model"].required is False

    assert "serial_number" in fields
    assert fields["serial_number"].offset == 12
    assert fields["serial_number"].required is False

    # DC Input/Output monitoring
    assert "dc_input_power" in fields
    assert fields["dc_input_power"].unit == "W"
    assert fields["dc_input_power"].required is False

    assert "dc_output_power" in fields
    assert fields["dc_output_power"].unit == "W"

    # Port scalar fields
    assert "cigarette_lighter_1_power" in fields
    assert fields["cigarette_lighter_1_power"].offset == 32

    assert "usb_a_power" in fields
    assert fields["usb_a_power"].offset == 44

    assert "type_c_1_power" in fields
    assert fields["type_c_1_power"].offset == 50

    assert "anderson_power" in fields
    assert fields["anderson_power"].offset == 62


def test_block_17400_contract():
    """Verify Block 17400 (ATS_EVENT_EXT) schema contract."""
    assert BLOCK_17400_SCHEMA.block_id == 17400
    assert BLOCK_17400_SCHEMA.name == "ATS_EVENT_EXT"
    assert BLOCK_17400_SCHEMA.min_length == 91
    assert BLOCK_17400_SCHEMA.protocol_version == 2000
    assert BLOCK_17400_SCHEMA.strict is False


def test_block_17400_field_structure():
    """Verify Block 17400 field structure and types."""
    fields = {f.name: f for f in BLOCK_17400_SCHEMA.fields}

    # Transfer switch control fields
    assert "grid_enable_flags" in fields
    assert fields["grid_enable_flags"].required is False

    assert "transfer_mode" in fields
    assert "grid_voltage_low_limit" in fields
    assert fields["grid_voltage_low_limit"].unit == "0.1V"

    assert "grid_frequency_low_limit" in fields
    assert fields["grid_frequency_low_limit"].unit == "0.01Hz"

    assert "transfer_delay_time" in fields
    assert fields["transfer_delay_time"].unit == "ms"

    assert "max_transfer_current" in fields
    assert fields["max_transfer_current"].unit == "0.1A"


def test_block_18000_contract():
    """Verify Block 18000 (EPAD_INFO) schema contract."""
    assert BLOCK_18000_SCHEMA.block_id == 18000
    assert BLOCK_18000_SCHEMA.name == "EPAD_INFO"
    assert BLOCK_18000_SCHEMA.min_length == 2019
    assert BLOCK_18000_SCHEMA.protocol_version == 2000
    assert BLOCK_18000_SCHEMA.strict is False


def test_block_18000_field_structure():
    """Verify Block 18000 field structure and types."""
    fields = {f.name: f for f in BLOCK_18000_SCHEMA.fields}

    # Device identification
    assert "model" in fields
    assert fields["model"].offset == 0
    assert fields["model"].required is False

    assert "serial_number" in fields
    assert "software_version" in fields

    # Operational data
    assert "device_status" in fields
    assert "total_power" in fields
    assert fields["total_power"].unit == "W"

    assert "total_energy" in fields
    assert fields["total_energy"].unit == "Wh"


def test_block_18300_contract():
    """Verify Block 18300 (EPAD_SETTINGS) schema contract."""
    assert BLOCK_18300_SCHEMA.block_id == 18300
    assert BLOCK_18300_SCHEMA.name == "EPAD_SETTINGS"
    assert BLOCK_18300_SCHEMA.min_length == 75
    assert BLOCK_18300_SCHEMA.protocol_version == 2000
    assert BLOCK_18300_SCHEMA.strict is False


def test_block_18300_field_structure():
    """Verify Block 18300 field structure and types."""
    fields = {f.name: f for f in BLOCK_18300_SCHEMA.fields}

    # Control fields
    assert "operating_mode" in fields
    assert fields["operating_mode"].required is False

    assert "enable_flags" in fields
    assert "max_power_limit" in fields
    assert fields["max_power_limit"].unit == "W"

    assert "max_current_limit" in fields
    assert fields["max_current_limit"].unit == "0.1A"

    # Protection settings
    assert "overvoltage_threshold" in fields
    assert fields["overvoltage_threshold"].unit == "0.1V"

    assert "overcurrent_threshold" in fields
    assert fields["overcurrent_threshold"].unit == "0.1A"


def test_block_26001_contract():
    """Verify Block 26001 (TOU_SETTINGS) schema contract."""
    assert BLOCK_26001_SCHEMA.block_id == 26001
    assert BLOCK_26001_SCHEMA.name == "TOU_SETTINGS"
    assert BLOCK_26001_SCHEMA.min_length == 126
    assert BLOCK_26001_SCHEMA.protocol_version == 2000
    assert BLOCK_26001_SCHEMA.strict is False


def test_block_26001_field_structure():
    """Verify Block 26001 field structure and types."""
    fields = {f.name: f for f in BLOCK_26001_SCHEMA.fields}

    # TOU control fields
    assert "tou_enable" in fields
    assert fields["tou_enable"].required is False

    assert "tou_mode" in fields

    # Rate period fields
    assert "period_1_start_hour" in fields
    assert "period_1_end_hour" in fields
    assert "period_1_rate_tier" in fields
    assert "period_1_days_of_week" in fields

    # Priority controls
    assert "charge_priority_enable" in fields
    assert "discharge_priority_enable" in fields

    assert "peak_rate_threshold" in fields
    assert "off_peak_rate_threshold" in fields
