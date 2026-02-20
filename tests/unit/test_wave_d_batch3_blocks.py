"""Unit tests for Wave D Batch 3 block schemas (provisional EVENT/UNKNOWN blocks).

Tests verify:
- Schema contract (block_id, name, min_length, protocol_version)
- Field structure (offset, type, required, unit, transform)
- Proper registration in schema registry

Note: These are provisional schemas for EVENT/UNKNOWN blocks without
dedicated parse methods. Field mappings require device testing to verify.
"""

from power_sdk.plugins.bluetti.v2.protocol.datatypes import (
    String,
    UInt8,
    UInt16,
    UInt32,
)
from power_sdk.plugins.bluetti.v2.schemas import (
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
    assert BLOCK_14700_SCHEMA.min_length == 56  # Updated from 32 (Agent D deep dive)
    assert BLOCK_14700_SCHEMA.protocol_version == 2000
    assert BLOCK_14700_SCHEMA.strict is False
    assert BLOCK_14700_SCHEMA.verification_status == "verified_reference"  # Upgraded

    # Verify key fields exist (updated field names from reference analysis)
    field_names = {f.name for f in BLOCK_14700_SCHEMA.fields}
    assert "protection_ctrl" in field_names
    assert "overload_protection_power" in field_names
    assert "underload_protection_power" in field_names
    assert "timer_set" in field_names
    assert "delay_hour_set" in field_names
    assert "delay_min_set" in field_names


def test_block_14700_field_structure():
    """Verify Block 14700 field structure (reference-verified)."""
    fields = {f.name: f for f in BLOCK_14700_SCHEMA.fields}

    # Protection control
    protection_ctrl = fields["protection_ctrl"]
    assert protection_ctrl.offset == 0
    assert isinstance(protection_ctrl.type, UInt16)
    assert protection_ctrl.required is False

    # Overload protection power (safety critical)
    overload_protection_power = fields["overload_protection_power"]
    assert overload_protection_power.offset == 12
    assert isinstance(overload_protection_power.type, UInt16)
    assert overload_protection_power.unit == "W"
    assert overload_protection_power.required is False

    # Underload protection power (safety critical)
    underload_protection_power = fields["underload_protection_power"]
    assert underload_protection_power.offset == 14
    assert isinstance(underload_protection_power.type, UInt16)
    assert underload_protection_power.unit == "W"
    assert underload_protection_power.required is False

    # Timer set
    timer_set = fields["timer_set"]
    assert timer_set.offset == 18
    assert isinstance(timer_set.type, UInt32)
    assert timer_set.unit == "s"
    assert timer_set.required is False

    # Delay hour set
    delay_hour_set = fields["delay_hour_set"]
    assert delay_hour_set.offset == 22
    assert isinstance(delay_hour_set.type, UInt8)
    assert delay_hour_set.unit == "h"
    assert delay_hour_set.required is False

    # Delay minute set
    delay_min_set = fields["delay_min_set"]
    assert delay_min_set.offset == 23
    assert isinstance(delay_min_set.type, UInt8)
    assert delay_min_set.unit == "min"
    assert delay_min_set.required is False


# === Block 15500 (DC_DC_INFO) ===


def test_block_15500_declarative_contract():
    """Verify Block 15500 (DC_DC_INFO) schema contract."""
    assert BLOCK_15500_SCHEMA.block_id == 15500
    assert BLOCK_15500_SCHEMA.name == "DC_DC_INFO"
    assert BLOCK_15500_SCHEMA.min_length == 30  # Corrected from 70 (Agent E deep dive)
    assert BLOCK_15500_SCHEMA.protocol_version == 2000
    assert BLOCK_15500_SCHEMA.strict is False
    assert BLOCK_15500_SCHEMA.verification_status == "verified_reference"  # Upgraded

    # Verify key fields exist (updated by Agent E)
    field_names = {f.name for f in BLOCK_15500_SCHEMA.fields}
    assert "model" in field_names
    assert "serial_number" in field_names
    assert "dc_input_volt" in field_names
    assert "dc_output_volt" in field_names


def test_block_15600_declarative_contract():
    """Verify Block 15600 (DC_DC_SETTINGS) schema contract."""
    assert BLOCK_15600_SCHEMA.block_id == 15600
    assert BLOCK_15600_SCHEMA.name == "DC_DC_SETTINGS"
    assert BLOCK_15600_SCHEMA.min_length == 36
    assert BLOCK_15600_SCHEMA.protocol_version == 2000
    assert BLOCK_15600_SCHEMA.strict is False

    # Verify key fields exist (updated by Agent E)
    field_names = {f.name for f in BLOCK_15600_SCHEMA.fields}
    assert "dc_ctrl" in field_names
    assert "factory_set" in field_names
    assert "volt_set_dc1" in field_names
    assert "volt_set_dc2" in field_names
    assert "volt_set_dc3" in field_names
    assert "output_current_dc3" in field_names


def test_block_15600_proven_scale_fields():
    """Verify 15600 proven scale fields are modeled with scale(0.1)."""
    fields = {f.name: f for f in BLOCK_15600_SCHEMA.fields}

    volt_set_dc1 = fields["volt_set_dc1"]
    assert volt_set_dc1.offset == 2
    assert isinstance(volt_set_dc1.type, UInt16)
    assert volt_set_dc1.unit == "V"
    assert volt_set_dc1.transform is not None
    assert len(volt_set_dc1.transform) == 1
    assert volt_set_dc1.transform[0].name == "scale"

    volt_set_dc2 = fields["volt_set_dc2"]
    assert volt_set_dc2.offset == 6
    assert isinstance(volt_set_dc2.type, UInt16)
    assert volt_set_dc2.unit == "V"
    assert volt_set_dc2.transform is not None
    assert len(volt_set_dc2.transform) == 1
    assert volt_set_dc2.transform[0].name == "scale"

    volt_set_dc3 = fields["volt_set_dc3"]
    assert volt_set_dc3.offset == 10
    assert isinstance(volt_set_dc3.type, UInt16)
    assert volt_set_dc3.unit == "V"
    assert volt_set_dc3.transform is not None
    assert len(volt_set_dc3.transform) == 1
    assert volt_set_dc3.transform[0].name == "scale"

    output_current_dc3 = fields["output_current_dc3"]
    assert output_current_dc3.offset == 12
    assert isinstance(output_current_dc3.type, UInt16)
    assert output_current_dc3.unit == "A"
    assert output_current_dc3.transform is not None
    assert len(output_current_dc3.transform) == 1
    assert output_current_dc3.transform[0].name == "scale"


def test_block_17100_declarative_contract():
    """Verify Block 17100 (AT1_BASE_INFO) schema contract."""
    assert BLOCK_17100_SCHEMA.block_id == 17100
    assert BLOCK_17100_SCHEMA.name == "AT1_BASE_INFO"
    assert BLOCK_17100_SCHEMA.min_length == 26  # Corrected from 127 (Agent I deep dive)
    assert BLOCK_17100_SCHEMA.protocol_version == 2000
    assert BLOCK_17100_SCHEMA.strict is False
    assert BLOCK_17100_SCHEMA.verification_status == "verified_reference"  # Upgraded

    # Verify key fields exist (only 3 verified fields)
    field_names = {f.name for f in BLOCK_17100_SCHEMA.fields}
    assert "model" in field_names
    assert "serial_number" in field_names
    assert "software_version" in field_names
    # Note: grid_voltage, transfer_status removed (no reference evidence)


def test_block_17100_field_structure():
    """Verify Block 17100 field structure (reference-verified)."""
    fields = {f.name: f for f in BLOCK_17100_SCHEMA.fields}

    # Model name
    model = fields["model"]
    assert model.offset == 0
    assert isinstance(model.type, String)
    assert model.type.length == 12
    assert model.required is False

    # Serial number
    serial_number = fields["serial_number"]
    assert serial_number.offset == 12
    assert isinstance(serial_number.type, String)
    assert serial_number.type.length == 8
    assert serial_number.required is False

    # Software version
    software_version = fields["software_version"]
    assert software_version.offset == 22
    assert isinstance(software_version.type, UInt32)
    assert software_version.required is False
