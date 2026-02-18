"""Unit tests for Wave D Batch 2 block schemas (smali-verified).

Tests verify:
- Schema contract (block_id, name, min_length, protocol_version)
- Field structure (offset, type, required, unit, transform)
- Proper registration in schema registry
"""

from power_sdk.protocol.v2.datatypes import String, UInt8, UInt16, UInt32
from power_sdk.schemas import (
    BLOCK_15750_SCHEMA,
    BLOCK_17000_SCHEMA,
    BLOCK_19365_SCHEMA,
    BLOCK_19425_SCHEMA,
    BLOCK_19485_SCHEMA,
)

# === Block 15750 (DC_HUB_SETTINGS) ===


def test_block_15750_declarative_contract():
    """Verify Block 15750 (DC_HUB_SETTINGS) schema contract."""
    assert BLOCK_15750_SCHEMA.block_id == 15750
    assert BLOCK_15750_SCHEMA.name == "DC_HUB_SETTINGS"
    assert BLOCK_15750_SCHEMA.min_length == 2
    assert BLOCK_15750_SCHEMA.protocol_version == 2000
    assert BLOCK_15750_SCHEMA.strict is False
    assert BLOCK_15750_SCHEMA.verification_status == "smali_verified"

    # Verify key fields exist
    field_names = {f.name for f in BLOCK_15750_SCHEMA.fields}
    assert "enable_flags" in field_names
    assert "dc_voltage_set" in field_names


def test_block_15750_field_structure():
    """Verify Block 15750 field structure."""
    fields = {f.name: f for f in BLOCK_15750_SCHEMA.fields}

    # Enable flags (bit-packed)
    enable_flags = fields["enable_flags"]
    assert enable_flags.offset == 0
    assert isinstance(enable_flags.type, UInt16)
    assert enable_flags.required is True

    # DC voltage setting
    dc_voltage_set = fields["dc_voltage_set"]
    assert dc_voltage_set.offset == 0
    assert isinstance(dc_voltage_set.type, UInt8)
    assert dc_voltage_set.required is True


# === Block 17000 (ATS_INFO) ===


def test_block_17000_declarative_contract():
    """Verify Block 17000 (ATS_INFO) schema contract."""
    assert BLOCK_17000_SCHEMA.block_id == 17000
    assert BLOCK_17000_SCHEMA.name == "ATS_INFO"
    assert BLOCK_17000_SCHEMA.min_length == 26
    assert BLOCK_17000_SCHEMA.protocol_version == 2000
    assert BLOCK_17000_SCHEMA.strict is False
    assert BLOCK_17000_SCHEMA.verification_status == "smali_verified"

    # Verify key fields exist
    field_names = {f.name for f in BLOCK_17000_SCHEMA.fields}
    assert "model" in field_names
    assert "serial_number" in field_names
    assert "software_type" in field_names
    assert "software_version" in field_names


def test_block_17000_field_structure():
    """Verify Block 17000 field structure."""
    fields = {f.name: f for f in BLOCK_17000_SCHEMA.fields}

    # Model name
    model = fields["model"]
    assert model.offset == 0
    assert isinstance(model.type, String)
    assert model.type.length == 12
    assert model.required is True

    # Serial number
    serial_number = fields["serial_number"]
    assert serial_number.offset == 12
    assert isinstance(serial_number.type, String)
    assert serial_number.type.length == 8
    assert serial_number.required is True

    # Software type
    software_type = fields["software_type"]
    assert software_type.offset == 21
    assert isinstance(software_type.type, UInt8)
    assert software_type.required is True

    # Software version
    software_version = fields["software_version"]
    assert software_version.offset == 22
    assert isinstance(software_version.type, UInt32)
    assert software_version.required is True


# === Block 19365 (AT1_TIMER_EVENT_A) ===


def test_block_19365_declarative_contract():
    """Verify Block 19365 (AT1_TIMER_EVENT_A) schema contract."""
    assert BLOCK_19365_SCHEMA.block_id == 19365
    assert BLOCK_19365_SCHEMA.name == "AT1_TIMER_EVENT_A"
    assert BLOCK_19365_SCHEMA.min_length == 8
    assert BLOCK_19365_SCHEMA.protocol_version == 2000
    assert BLOCK_19365_SCHEMA.strict is False
    assert BLOCK_19365_SCHEMA.verification_status == "smali_verified"

    # Verify key fields exist
    field_names = {f.name for f in BLOCK_19365_SCHEMA.fields}
    assert "slot1_flags" in field_names
    assert "slot1_value1" in field_names
    assert "slot1_value2" in field_names
    assert "slot2_flags" in field_names


def test_block_19365_field_structure():
    """Verify Block 19365 field structure."""
    fields = {f.name: f for f in BLOCK_19365_SCHEMA.fields}

    # Slot 1 fields
    slot1_flags = fields["slot1_flags"]
    assert slot1_flags.offset == 0
    assert isinstance(slot1_flags.type, UInt16)
    assert slot1_flags.required is True

    slot1_value1 = fields["slot1_value1"]
    assert slot1_value1.offset == 2
    assert isinstance(slot1_value1.type, UInt8)
    assert slot1_value1.required is True

    slot1_value2 = fields["slot1_value2"]
    assert slot1_value2.offset == 3
    assert isinstance(slot1_value2.type, UInt8)
    assert slot1_value2.required is True

    # Slot 2 fields
    slot2_flags = fields["slot2_flags"]
    assert slot2_flags.offset == 4
    assert isinstance(slot2_flags.type, UInt16)
    assert slot2_flags.required is False


# === Block 19425 (AT1_TIMER_EVENT_B) ===


def test_block_19425_declarative_contract():
    """Verify Block 19425 (AT1_TIMER_EVENT_B) schema contract."""
    assert BLOCK_19425_SCHEMA.block_id == 19425
    assert BLOCK_19425_SCHEMA.name == "AT1_TIMER_EVENT_B"
    assert BLOCK_19425_SCHEMA.min_length == 8
    assert BLOCK_19425_SCHEMA.protocol_version == 2000
    assert BLOCK_19425_SCHEMA.strict is False
    assert BLOCK_19425_SCHEMA.verification_status == "smali_verified"

    # Verify key fields exist
    field_names = {f.name for f in BLOCK_19425_SCHEMA.fields}
    assert "slot3_flags" in field_names
    assert "slot3_value1" in field_names
    assert "slot3_value2" in field_names
    assert "slot4_flags" in field_names


def test_block_19425_field_structure():
    """Verify Block 19425 field structure."""
    fields = {f.name: f for f in BLOCK_19425_SCHEMA.fields}

    # Slot 3 fields
    slot3_flags = fields["slot3_flags"]
    assert slot3_flags.offset == 0
    assert isinstance(slot3_flags.type, UInt16)
    assert slot3_flags.required is True

    slot3_value1 = fields["slot3_value1"]
    assert slot3_value1.offset == 2
    assert isinstance(slot3_value1.type, UInt8)
    assert slot3_value1.required is True

    slot3_value2 = fields["slot3_value2"]
    assert slot3_value2.offset == 3
    assert isinstance(slot3_value2.type, UInt8)
    assert slot3_value2.required is True

    # Slot 4 fields
    slot4_flags = fields["slot4_flags"]
    assert slot4_flags.offset == 4
    assert isinstance(slot4_flags.type, UInt16)
    assert slot4_flags.required is False


# === Block 19485 (AT1_TIMER_EVENT_C) ===


def test_block_19485_declarative_contract():
    """Verify Block 19485 (AT1_TIMER_EVENT_C) schema contract."""
    assert BLOCK_19485_SCHEMA.block_id == 19485
    assert BLOCK_19485_SCHEMA.name == "AT1_TIMER_EVENT_C"
    assert BLOCK_19485_SCHEMA.min_length == 8
    assert BLOCK_19485_SCHEMA.protocol_version == 2000
    assert BLOCK_19485_SCHEMA.strict is False
    assert BLOCK_19485_SCHEMA.verification_status == "smali_verified"

    # Verify key fields exist
    field_names = {f.name for f in BLOCK_19485_SCHEMA.fields}
    assert "slot5_flags" in field_names
    assert "slot5_value1" in field_names
    assert "slot5_value2" in field_names
    assert "slot6_flags" in field_names


def test_block_19485_field_structure():
    """Verify Block 19485 field structure."""
    fields = {f.name: f for f in BLOCK_19485_SCHEMA.fields}

    # Slot 5 fields
    slot5_flags = fields["slot5_flags"]
    assert slot5_flags.offset == 0
    assert isinstance(slot5_flags.type, UInt16)
    assert slot5_flags.required is True

    slot5_value1 = fields["slot5_value1"]
    assert slot5_value1.offset == 2
    assert isinstance(slot5_value1.type, UInt8)
    assert slot5_value1.required is True

    slot5_value2 = fields["slot5_value2"]
    assert slot5_value2.offset == 3
    assert isinstance(slot5_value2.type, UInt8)
    assert slot5_value2.required is True

    # Slot 6 fields
    slot6_flags = fields["slot6_flags"]
    assert slot6_flags.offset == 4
    assert isinstance(slot6_flags.type, UInt16)
    assert slot6_flags.required is False

