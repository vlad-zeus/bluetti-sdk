"""Unit tests for Wave D Batch 3 block schemas (provisional EVENT/UNKNOWN blocks).

Tests verify:
- Schema contract (block_id, name, min_length, protocol_version)
- Field structure (offset, type, required, unit, transform)
- Proper registration in schema registry

Note: These are provisional schemas for EVENT/UNKNOWN blocks without
dedicated parse methods. Field mappings require device testing to verify.
"""

from bluetti_sdk.protocol.v2.datatypes import String, UInt8, UInt16, UInt32
from bluetti_sdk.schemas import (
    BLOCK_14500_SCHEMA,
    BLOCK_14700_SCHEMA,
    BLOCK_15500_SCHEMA,
    BLOCK_15600_SCHEMA,
    BLOCK_17100_SCHEMA,
)

# === Block 14500 (SMART_PLUG_INFO) ===


def test_block_14500_declarative_contract():
    """Verify Block 14500 (SMART_PLUG_INFO) schema contract."""
    assert BLOCK_14500_SCHEMA.block_id == 14500
    assert BLOCK_14500_SCHEMA.name == "SMART_PLUG_INFO"
    assert BLOCK_14500_SCHEMA.min_length == 26
    assert BLOCK_14500_SCHEMA.protocol_version == 2000
    assert BLOCK_14500_SCHEMA.strict is False

    # Verify key fields exist
    field_names = {f.name for f in BLOCK_14500_SCHEMA.fields}
    assert "model" in field_names
    assert "serial_number" in field_names
    assert "software_version" in field_names
    assert "plug_count" in field_names


def test_block_14500_field_structure():
    """Verify Block 14500 field structure."""
    fields = {f.name: f for f in BLOCK_14500_SCHEMA.fields}

    # Model name
    model = fields["model"]
    assert model.offset == 0
    assert isinstance(model.type, String)
    assert model.type.length == 12
    assert model.required is False  # Provisional

    # Serial number
    serial_number = fields["serial_number"]
    assert serial_number.offset == 12
    assert isinstance(serial_number.type, String)
    assert serial_number.type.length == 8
    assert serial_number.required is False  # Provisional

    # Software version
    software_version = fields["software_version"]
    assert software_version.offset == 20
    assert isinstance(software_version.type, UInt32)
    assert software_version.required is False

    # Plug count
    plug_count = fields["plug_count"]
    assert plug_count.offset == 24
    assert isinstance(plug_count.type, UInt16)
    assert plug_count.required is False


# === Block 14700 (SMART_PLUG_SETTINGS) ===


def test_block_14700_declarative_contract():
    """Verify Block 14700 (SMART_PLUG_SETTINGS) schema contract."""
    assert BLOCK_14700_SCHEMA.block_id == 14700
    assert BLOCK_14700_SCHEMA.name == "SMART_PLUG_SETTINGS"
    assert BLOCK_14700_SCHEMA.min_length == 32
    assert BLOCK_14700_SCHEMA.protocol_version == 2000
    assert BLOCK_14700_SCHEMA.strict is False

    # Verify key fields exist
    field_names = {f.name for f in BLOCK_14700_SCHEMA.fields}
    assert "enable_flags" in field_names
    assert "max_power" in field_names


def test_block_14700_field_structure():
    """Verify Block 14700 field structure."""
    fields = {f.name: f for f in BLOCK_14700_SCHEMA.fields}

    # Enable flags
    enable_flags = fields["enable_flags"]
    assert enable_flags.offset == 0
    assert isinstance(enable_flags.type, UInt16)
    assert enable_flags.required is False  # Provisional

    # Max power
    max_power = fields["max_power"]
    assert max_power.offset == 2
    assert isinstance(max_power.type, UInt16)
    assert max_power.unit == "W"
    assert max_power.required is False  # Provisional


# === Block 15500 (DC_DC_INFO) ===


def test_block_15500_declarative_contract():
    """Verify Block 15500 (DC_DC_INFO) schema contract."""
    assert BLOCK_15500_SCHEMA.block_id == 15500
    assert BLOCK_15500_SCHEMA.name == "DC_DC_INFO"
    assert BLOCK_15500_SCHEMA.min_length == 70
    assert BLOCK_15500_SCHEMA.protocol_version == 2000
    assert BLOCK_15500_SCHEMA.strict is False

    # Verify key fields exist
    field_names = {f.name for f in BLOCK_15500_SCHEMA.fields}
    assert "model" in field_names
    assert "serial_number" in field_names
    assert "input_voltage" in field_names
    assert "output_voltage" in field_names


def test_block_15500_field_structure():
    """Verify Block 15500 field structure."""
    fields = {f.name: f for f in BLOCK_15500_SCHEMA.fields}

    # Model name
    model = fields["model"]
    assert model.offset == 0
    assert isinstance(model.type, String)
    assert model.type.length == 12
    assert model.required is False  # Provisional

    # Input voltage
    input_voltage = fields["input_voltage"]
    assert input_voltage.offset == 24
    assert isinstance(input_voltage.type, UInt16)
    assert input_voltage.unit == "V"
    assert input_voltage.required is False  # Provisional

    # Output voltage
    output_voltage = fields["output_voltage"]
    assert output_voltage.offset == 26
    assert isinstance(output_voltage.type, UInt16)
    assert output_voltage.unit == "V"
    assert output_voltage.required is False  # Provisional


# === Block 15600 (DC_DC_SETTINGS) ===


def test_block_15600_declarative_contract():
    """Verify Block 15600 (DC_DC_SETTINGS) schema contract."""
    assert BLOCK_15600_SCHEMA.block_id == 15600
    assert BLOCK_15600_SCHEMA.name == "DC_DC_SETTINGS"
    assert BLOCK_15600_SCHEMA.min_length == 36
    assert BLOCK_15600_SCHEMA.protocol_version == 2000
    assert BLOCK_15600_SCHEMA.strict is False

    # Verify key fields exist
    field_names = {f.name for f in BLOCK_15600_SCHEMA.fields}
    assert "enable_flags" in field_names
    assert "output_voltage_set" in field_names
    assert "output_current_limit" in field_names


def test_block_15600_field_structure():
    """Verify Block 15600 field structure."""
    fields = {f.name: f for f in BLOCK_15600_SCHEMA.fields}

    # Enable flags
    enable_flags = fields["enable_flags"]
    assert enable_flags.offset == 0
    assert isinstance(enable_flags.type, UInt16)
    assert enable_flags.required is False  # Provisional

    # Output voltage setpoint
    output_voltage_set = fields["output_voltage_set"]
    assert output_voltage_set.offset == 2
    assert isinstance(output_voltage_set.type, UInt16)
    assert output_voltage_set.unit == "V"
    assert output_voltage_set.required is False  # Provisional

    # Output current limit
    output_current_limit = fields["output_current_limit"]
    assert output_current_limit.offset == 4
    assert isinstance(output_current_limit.type, UInt16)
    assert output_current_limit.unit == "A"
    assert output_current_limit.required is False  # Provisional


# === Block 17100 (AT1_BASE_INFO) ===


def test_block_17100_declarative_contract():
    """Verify Block 17100 (AT1_BASE_INFO) schema contract."""
    assert BLOCK_17100_SCHEMA.block_id == 17100
    assert BLOCK_17100_SCHEMA.name == "AT1_BASE_INFO"
    assert BLOCK_17100_SCHEMA.min_length == 127
    assert BLOCK_17100_SCHEMA.protocol_version == 2000
    assert BLOCK_17100_SCHEMA.strict is False

    # Verify key fields exist
    field_names = {f.name for f in BLOCK_17100_SCHEMA.fields}
    assert "model" in field_names
    assert "serial_number" in field_names
    assert "grid_voltage" in field_names
    assert "transfer_status" in field_names


def test_block_17100_field_structure():
    """Verify Block 17100 field structure."""
    fields = {f.name: f for f in BLOCK_17100_SCHEMA.fields}

    # Model name
    model = fields["model"]
    assert model.offset == 0
    assert isinstance(model.type, String)
    assert model.type.length == 12
    assert model.required is False  # Provisional

    # Software version
    software_version = fields["software_version"]
    assert software_version.offset == 22
    assert isinstance(software_version.type, UInt32)
    assert software_version.required is False  # Provisional

    # Grid voltage
    grid_voltage = fields["grid_voltage"]
    assert grid_voltage.offset == 26
    assert isinstance(grid_voltage.type, UInt16)
    assert grid_voltage.unit == "V"
    assert grid_voltage.required is False  # Provisional

    # Transfer status
    transfer_status = fields["transfer_status"]
    assert transfer_status.offset == 30
    assert isinstance(transfer_status.type, UInt8)
    assert transfer_status.required is False  # Provisional
