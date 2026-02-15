"""Unit tests for Wave C (P2 monitoring) block schemas.

Tests verify:
- Schema contract (block_id, name, min_length, protocol_version)
- Field structure (offset, type, required, unit, transform)
- Proper registration in schema registry
"""


from bluetti_sdk.protocol.v2.datatypes import (
    Int16,
    String,
    UInt8,
    UInt16,
    UInt32,
)
from bluetti_sdk.schemas import (
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
    assert BLOCK_720_SCHEMA.min_length == 2
    assert BLOCK_720_SCHEMA.protocol_version == 2000
    assert BLOCK_720_SCHEMA.strict is False

    # Verify key fields exist
    field_names = {f.name for f in BLOCK_720_SCHEMA.fields}
    assert "ota_status" in field_names
    assert "ota_progress" in field_names


def test_block_720_field_structure():
    """Verify Block 720 field structure."""
    fields = {f.name: f for f in BLOCK_720_SCHEMA.fields}

    ota_status = fields["ota_status"]
    assert ota_status.offset == 0
    assert isinstance(ota_status.type, UInt8)
    assert ota_status.required is False

    ota_progress = fields["ota_progress"]
    assert ota_progress.offset == 1
    assert isinstance(ota_progress.type, UInt8)
    assert ota_progress.required is False


# === Block 1700 (METER_INFO) ===


def test_block_1700_declarative_contract():
    """Verify Block 1700 (METER_INFO) schema contract."""
    assert BLOCK_1700_SCHEMA.block_id == 1700
    assert BLOCK_1700_SCHEMA.name == "METER_INFO"
    assert BLOCK_1700_SCHEMA.min_length == 4
    assert BLOCK_1700_SCHEMA.protocol_version == 2000
    assert BLOCK_1700_SCHEMA.strict is False

    # Verify key fields exist
    field_names = {f.name for f in BLOCK_1700_SCHEMA.fields}
    assert "meter_power" in field_names
    assert "meter_current" in field_names


def test_block_1700_field_structure():
    """Verify Block 1700 field structure."""
    fields = {f.name: f for f in BLOCK_1700_SCHEMA.fields}

    meter_power = fields["meter_power"]
    assert meter_power.offset == 0
    assert isinstance(meter_power.type, Int16)
    assert meter_power.unit == "W"
    assert meter_power.required is False

    meter_current = fields["meter_current"]
    assert meter_current.offset == 2
    assert isinstance(meter_current.type, Int16)
    assert meter_current.unit == "A"
    assert meter_current.required is False


# === Block 3500 (TOTAL_ENERGY_INFO) ===


def test_block_3500_declarative_contract():
    """Verify Block 3500 (TOTAL_ENERGY_INFO) schema contract."""
    assert BLOCK_3500_SCHEMA.block_id == 3500
    assert BLOCK_3500_SCHEMA.name == "TOTAL_ENERGY_INFO"
    assert BLOCK_3500_SCHEMA.min_length == 16
    assert BLOCK_3500_SCHEMA.protocol_version == 2000
    assert BLOCK_3500_SCHEMA.strict is False

    # Verify key fields exist
    field_names = {f.name for f in BLOCK_3500_SCHEMA.fields}
    assert "total_pv_energy" in field_names
    assert "total_charge_energy" in field_names
    assert "total_discharge_energy" in field_names
    assert "total_grid_energy" in field_names


def test_block_3500_field_structure():
    """Verify Block 3500 field structure."""
    fields = {f.name: f for f in BLOCK_3500_SCHEMA.fields}

    total_pv_energy = fields["total_pv_energy"]
    assert total_pv_energy.offset == 0
    assert isinstance(total_pv_energy.type, UInt32)
    assert total_pv_energy.unit == "kWh"
    assert total_pv_energy.required is False
    assert total_pv_energy.transform is not None  # scale(0.1)

    total_discharge_energy = fields["total_discharge_energy"]
    assert total_discharge_energy.offset == 8
    assert isinstance(total_discharge_energy.type, UInt32)
    assert total_discharge_energy.unit == "kWh"


# === Block 3600 (CURR_YEAR_ENERGY) ===


def test_block_3600_declarative_contract():
    """Verify Block 3600 (CURR_YEAR_ENERGY) schema contract."""
    assert BLOCK_3600_SCHEMA.block_id == 3600
    assert BLOCK_3600_SCHEMA.name == "CURR_YEAR_ENERGY"
    assert BLOCK_3600_SCHEMA.min_length == 16
    assert BLOCK_3600_SCHEMA.protocol_version == 2000
    assert BLOCK_3600_SCHEMA.strict is False

    # Verify key fields exist
    field_names = {f.name for f in BLOCK_3600_SCHEMA.fields}
    assert "year_pv_energy" in field_names
    assert "year_charge_energy" in field_names
    assert "year_discharge_energy" in field_names
    assert "year_grid_energy" in field_names


def test_block_3600_field_structure():
    """Verify Block 3600 field structure."""
    fields = {f.name: f for f in BLOCK_3600_SCHEMA.fields}

    year_pv_energy = fields["year_pv_energy"]
    assert year_pv_energy.offset == 0
    assert isinstance(year_pv_energy.type, UInt32)
    assert year_pv_energy.unit == "kWh"
    assert year_pv_energy.required is False
    assert year_pv_energy.transform is not None  # scale(0.1)

    year_discharge_energy = fields["year_discharge_energy"]
    assert year_discharge_energy.offset == 8
    assert isinstance(year_discharge_energy.type, UInt32)
    assert year_discharge_energy.unit == "kWh"


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
    assert bmu0_serial_number.required is False

    bmu0_fault_data = fields["bmu0_fault_data"]
    assert bmu0_fault_data.offset == 8
    assert isinstance(bmu0_fault_data.type, UInt32)
    assert bmu0_fault_data.required is False

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
    assert "iot_enable" in field_names
    assert "iot_mode" in field_names
    assert "iot_ctrl_status" in field_names


def test_block_12161_field_structure():
    """Verify Block 12161 field structure."""
    fields = {f.name: f for f in BLOCK_12161_SCHEMA.fields}

    iot_enable = fields["iot_enable"]
    assert iot_enable.offset == 0
    assert isinstance(iot_enable.type, UInt8)
    assert iot_enable.required is False

    iot_mode = fields["iot_mode"]
    assert iot_mode.offset == 1
    assert isinstance(iot_mode.type, UInt8)
    assert iot_mode.required is False

    iot_ctrl_status = fields["iot_ctrl_status"]
    assert iot_ctrl_status.offset == 2
    assert isinstance(iot_ctrl_status.type, UInt16)
    assert iot_ctrl_status.required is False
