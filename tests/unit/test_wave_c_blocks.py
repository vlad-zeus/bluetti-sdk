"""Unit tests for Wave C (P2 monitoring) block schemas (smali-verified).

Tests verify:
- Schema contract (block_id, name, min_length, protocol_version)
- Field structure (offset, type, required, unit, transform)
- Proper registration in schema registry
"""

from power_sdk.plugins.bluetti.v2.protocol.datatypes import (
    String,
    UInt8,
    UInt16,
    UInt32,
)
from power_sdk.plugins.bluetti.v2.schemas import (
    BLOCK_720_SCHEMA,
    BLOCK_1700_SCHEMA,
    BLOCK_3500_SCHEMA,
    BLOCK_3600_SCHEMA,
    BLOCK_6300_SCHEMA,
    BLOCK_12161_SCHEMA,
)

# === Block 720 (OTA_STATUS) ===


def test_block_720_declarative_contract():
    """Verify Block 720 (OTA_STATUS) schema contract."""
    assert BLOCK_720_SCHEMA.block_id == 720
    assert BLOCK_720_SCHEMA.name == "OTA_STATUS"
    assert BLOCK_720_SCHEMA.min_length == 8  # Updated from 2
    assert BLOCK_720_SCHEMA.protocol_version == 2000
    assert BLOCK_720_SCHEMA.strict is False

    # Verify key fields exist
    field_names = {f.name for f in BLOCK_720_SCHEMA.fields}
    assert "ota_group" in field_names
    assert "file0_ota_status" in field_names
    assert "file0_progress" in field_names


def test_block_720_field_structure():
    """Verify Block 720 field structure."""
    fields = {f.name: f for f in BLOCK_720_SCHEMA.fields}

    ota_group = fields["ota_group"]
    assert ota_group.offset == 0
    assert isinstance(ota_group.type, UInt8)
    assert ota_group.required is True

    file0_progress = fields["file0_progress"]
    assert file0_progress.offset == 6
    assert isinstance(file0_progress.type, UInt8)
    assert file0_progress.required is True


# === Block 1700 (METER_INFO) ===


def test_block_1700_declarative_contract():
    """Verify Block 1700 (METER_INFO) schema contract."""
    assert BLOCK_1700_SCHEMA.block_id == 1700
    assert BLOCK_1700_SCHEMA.name == "METER_INFO"
    assert BLOCK_1700_SCHEMA.min_length == 138  # Updated from 4
    assert BLOCK_1700_SCHEMA.protocol_version == 2000
    assert BLOCK_1700_SCHEMA.strict is False

    # Verify key fields exist
    field_names = {f.name: f for f in BLOCK_1700_SCHEMA.fields}
    assert "model" in field_names
    assert "sn" in field_names
    assert "status" in field_names


def test_block_1700_field_structure():
    """Verify Block 1700 field structure."""
    fields = {f.name: f for f in BLOCK_1700_SCHEMA.fields}

    model = fields["model"]
    assert model.offset == 0
    assert isinstance(model.type, String)
    assert model.required is True

    sn = fields["sn"]
    assert sn.offset == 12
    assert isinstance(sn.type, String)
    assert sn.required is True


# === Block 3500 (TOTAL_ENERGY_INFO) ===


def test_block_3500_declarative_contract():
    """Verify Block 3500 (TOTAL_ENERGY_INFO) schema contract."""
    assert BLOCK_3500_SCHEMA.block_id == 3500
    assert BLOCK_3500_SCHEMA.name == "TOTAL_ENERGY_INFO"
    assert BLOCK_3500_SCHEMA.min_length == 96  # Updated from 16
    assert BLOCK_3500_SCHEMA.protocol_version == 2000
    assert BLOCK_3500_SCHEMA.strict is False

    # Verify key fields exist
    field_names = {f.name: f for f in BLOCK_3500_SCHEMA.fields}
    assert "energy_type" in field_names
    assert "total_energy" in field_names
    assert "year0_year" in field_names
    assert "year0_energy" in field_names


def test_block_3500_field_structure():
    """Verify Block 3500 field structure."""
    fields = {f.name: f for f in BLOCK_3500_SCHEMA.fields}

    total_energy = fields["total_energy"]
    assert total_energy.offset == 2
    assert isinstance(total_energy.type, UInt32)
    assert total_energy.unit == "kWh"
    assert total_energy.required is True
    assert total_energy.transform is not None  # scale(0.1)

    year0_energy = fields["year0_energy"]
    assert year0_energy.offset == 8
    assert isinstance(year0_energy.type, UInt32)
    assert year0_energy.unit == "kWh"


# === Block 3600 (CURR_YEAR_ENERGY) ===


def test_block_3600_declarative_contract():
    """Verify Block 3600 (CURR_YEAR_ENERGY) schema contract."""
    assert BLOCK_3600_SCHEMA.block_id == 3600
    assert BLOCK_3600_SCHEMA.name == "CURR_YEAR_ENERGY"
    assert BLOCK_3600_SCHEMA.min_length == 56  # Updated from 16
    assert BLOCK_3600_SCHEMA.protocol_version == 2000
    assert BLOCK_3600_SCHEMA.strict is False

    # Verify key fields exist
    field_names = {f.name: f for f in BLOCK_3600_SCHEMA.fields}
    assert "energy_type" in field_names
    assert "year" in field_names
    assert "total_year_energy" in field_names
    assert "month0_energy" in field_names


def test_block_3600_field_structure():
    """Verify Block 3600 field structure."""
    fields = {f.name: f for f in BLOCK_3600_SCHEMA.fields}

    year = fields["year"]
    assert year.offset == 2
    assert isinstance(year.type, UInt16)
    assert year.required is True

    total_year_energy = fields["total_year_energy"]
    assert total_year_energy.offset == 4
    assert isinstance(total_year_energy.type, UInt32)
    assert total_year_energy.unit == "kWh"
    assert total_year_energy.required is True
    assert total_year_energy.transform is not None  # scale(0.1)


# === Block 6300 (PACK_BMU_READ) ===


def test_block_6300_declarative_contract():
    """Verify Block 6300 (PACK_BMU_READ) schema contract."""
    assert BLOCK_6300_SCHEMA.block_id == 6300
    assert BLOCK_6300_SCHEMA.name == "PACK_BMU_READ"
    assert BLOCK_6300_SCHEMA.min_length == 25
    assert BLOCK_6300_SCHEMA.protocol_version == 2000
    assert BLOCK_6300_SCHEMA.strict is False

    # Verify key fields exist
    field_names = {f.name for f in BLOCK_6300_SCHEMA.fields}
    assert "bmu0_serial_number" in field_names
    assert "bmu0_fault_data" in field_names
    assert "bmu0_cell_count" in field_names
    assert "bmu0_ntc_count" in field_names
    assert "bmu0_model_type" in field_names


def test_block_6300_field_structure():
    """Verify Block 6300 field structure."""
    fields = {f.name: f for f in BLOCK_6300_SCHEMA.fields}

    bmu0_serial_number = fields["bmu0_serial_number"]
    assert bmu0_serial_number.offset == 0
    assert isinstance(bmu0_serial_number.type, String)
    assert bmu0_serial_number.required is True  # Changed from False

    bmu0_fault_data = fields["bmu0_fault_data"]
    assert bmu0_fault_data.offset == 8
    assert isinstance(bmu0_fault_data.type, UInt32)
    assert bmu0_fault_data.required is True  # Changed from False

    bmu0_cell_count = fields["bmu0_cell_count"]
    assert bmu0_cell_count.offset == 13
    assert isinstance(bmu0_cell_count.type, UInt8)

    bmu0_model_type = fields["bmu0_model_type"]
    assert bmu0_model_type.offset == 15
    assert isinstance(bmu0_model_type.type, UInt8)


# === Block 12161 (IOT_ENABLE_INFO) ===


def test_block_12161_declarative_contract():
    """Verify Block 12161 (IOT_ENABLE_INFO) schema contract."""
    assert BLOCK_12161_SCHEMA.block_id == 12161
    assert BLOCK_12161_SCHEMA.name == "IOT_ENABLE_INFO"
    assert BLOCK_12161_SCHEMA.min_length == 4
    assert BLOCK_12161_SCHEMA.protocol_version == 2000
    assert BLOCK_12161_SCHEMA.strict is False

    # Verify key fields exist
    field_names = {f.name for f in BLOCK_12161_SCHEMA.fields}
    assert "control_flags_1" in field_names
    assert "control_flags_2" in field_names


def test_block_12161_field_structure():
    """Verify Block 12161 field structure."""
    fields = {f.name: f for f in BLOCK_12161_SCHEMA.fields}

    control_flags_1 = fields["control_flags_1"]
    assert control_flags_1.offset == 0
    assert isinstance(control_flags_1.type, UInt16)
    assert control_flags_1.required is True

    control_flags_2 = fields["control_flags_2"]
    assert control_flags_2.offset == 2
    assert isinstance(control_flags_2.type, UInt16)
    assert control_flags_2.required is True
