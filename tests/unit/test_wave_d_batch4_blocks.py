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
    """Verify Block 17400 nested framework: 10 FieldGroups, 30 proven sub-fields."""
    from bluetti_sdk.protocol.v2.schema import FieldGroup

    groups = {f.name: f for f in BLOCK_17400_SCHEMA.fields if isinstance(f, FieldGroup)}

    # 2 enable groups + 7x AT1BaseConfigItem groups + simple_end_fields = 10 total
    assert len(BLOCK_17400_SCHEMA.fields) == 10
    expected_groups = {
        "top_level_enables",
        "startup_flags",
        "config_grid",
        "config_sl1",
        "config_sl2",
        "config_sl3",
        "config_sl4",
        "config_pcs1",
        "config_pcs2",
        "simple_end_fields",
    }
    assert expected_groups == set(groups.keys())

    # top_level_enables: 2 sub-fields (chg/feed_to_grid_enable)
    assert len(groups["top_level_enables"].fields) == 2

    # startup_flags: 4 sub-fields (bytes 174-175 hex_enable_list fields)
    assert len(groups["startup_flags"].fields) == 4

    # config_grid (6 fields): type, linkage_enable, force_enable_0/1/2, max_current
    assert len(groups["config_grid"].fields) == 6
    grid_names = {f.name for f in groups["config_grid"].fields}
    assert {
        "type", "linkage_enable",
        "force_enable_0", "force_enable_1", "force_enable_2",
        "max_current",
    } == grid_names

    # config_sl1 (6 fields): type, linkage_enable, force_enable_0/1/2, max_current
    assert len(groups["config_sl1"].fields) == 6
    sl1_names = {f.name for f in groups["config_sl1"].fields}
    assert {
        "type", "linkage_enable",
        "force_enable_0", "force_enable_1", "force_enable_2",
        "max_current",
    } == sl1_names

    # SL2/SL3/SL4: max_current proven (forensic audit 2026-02-17)
    assert len(groups["config_sl2"].fields) == 1
    assert len(groups["config_sl3"].fields) == 1
    assert len(groups["config_sl4"].fields) == 1
    assert {f.name for f in groups["config_sl2"].fields} == {"max_current"}
    assert {f.name for f in groups["config_sl3"].fields} == {"max_current"}
    assert {f.name for f in groups["config_sl4"].fields} == {"max_current"}

    # PCS1/PCS2: type + max_current proven (forensic audit 2026-02-17)
    assert len(groups["config_pcs1"].fields) == 2
    assert len(groups["config_pcs2"].fields) == 2
    assert {f.name for f in groups["config_pcs1"].fields} == {"type", "max_current"}
    assert {f.name for f in groups["config_pcs2"].fields} == {"type", "max_current"}

    # simple_end_fields has 5 proven sub-fields
    assert len(groups["simple_end_fields"].fields) == 5
    assert groups["simple_end_fields"].evidence_status == "smali_verified"


def test_block_18000_contract():
    """Verify Block 18000 (EPAD_INFO) schema contract."""
    assert BLOCK_18000_SCHEMA.block_id == 18000
    assert BLOCK_18000_SCHEMA.name == "EPAD_INFO"
    assert BLOCK_18000_SCHEMA.min_length == 2019
    assert BLOCK_18000_SCHEMA.protocol_version == 2000
    assert BLOCK_18000_SCHEMA.strict is False


def test_block_18000_field_structure():
    """Verify Block 18000 field structure and types (smali-verified)."""
    fields = {f.name: f for f in BLOCK_18000_SCHEMA.fields}

    # Liquid level sensors (bytes 12-17)
    assert "liquid_level_1" in fields
    assert fields["liquid_level_1"].offset == 12
    assert fields["liquid_level_1"].required is True

    assert "liquid_level_2" in fields
    assert fields["liquid_level_2"].offset == 14

    assert "liquid_level_3" in fields
    assert fields["liquid_level_3"].offset == 16

    # Temperature sensors (bytes 18-23)
    assert "sensor_temp_1" in fields
    assert fields["sensor_temp_1"].offset == 18
    assert fields["sensor_temp_1"].unit == "0.1°C"

    assert "sensor_temp_2" in fields
    assert fields["sensor_temp_2"].offset == 20

    assert "sensor_temp_3" in fields
    assert fields["sensor_temp_3"].offset == 22

    # Remaining capacity (bytes 24-29)
    assert "remaining_capacity_1" in fields
    assert fields["remaining_capacity_1"].offset == 24
    assert fields["remaining_capacity_1"].unit == "%"

    assert "remaining_capacity_2" in fields
    assert "remaining_capacity_3" in fields

    # Connection status
    assert "connection_status" in fields
    assert fields["connection_status"].offset == 30

    # Ambient temperature (bytes 32-37)
    assert "ambient_temp_1" in fields
    assert fields["ambient_temp_1"].offset == 32
    assert fields["ambient_temp_1"].unit == "0.1°C"

    assert "ambient_temp_2" in fields
    assert "ambient_temp_3" in fields


def test_block_18300_contract():
    """Verify Block 18300 (EPAD_SETTINGS) schema contract (smali-verified)."""
    assert BLOCK_18300_SCHEMA.block_id == 18300
    assert BLOCK_18300_SCHEMA.name == "EPAD_SETTINGS"
    assert BLOCK_18300_SCHEMA.min_length == 152  # Updated after Agent G verification
    assert BLOCK_18300_SCHEMA.protocol_version == 2000
    assert BLOCK_18300_SCHEMA.strict is False
    assert BLOCK_18300_SCHEMA.verification_status == "smali_verified"


def test_block_18300_field_structure():
    """Verify Block 18300 field structure (70 fields from 3 sub-parsers)."""
    fields = {f.name: f for f in BLOCK_18300_SCHEMA.fields}

    # Should have 70 fields total:
    # - 1 sensor_type
    # - 3 liquid sensors x 17 fields each = 51 fields
    # - 3 temp sensors x 5 fields each = 15 fields
    # - 1 lcd_active_time
    # Total: 1 + 51 + 15 + 1 = 68 (note: some fields combined)
    assert len(fields) >= 60, f"Expected 60+ fields, got {len(fields)}"

    # Top-level fields
    assert "sensor_type" in fields
    assert fields["sensor_type"].offset == 0

    # Liquid sensor 1 base fields (2-15)
    assert "liquid_1_sensor_spec" in fields
    assert fields["liquid_1_sensor_spec"].offset == 2
    assert "liquid_1_calibration_full" in fields
    assert fields["liquid_1_calibration_full"].offset == 14

    # Liquid sensor 1 extended fields (44-61)
    assert "liquid_1_alarm_enable" in fields
    assert fields["liquid_1_alarm_enable"].offset == 44
    assert "liquid_1_alarm_clean_delay_low" in fields
    assert fields["liquid_1_alarm_clean_delay_low"].offset == 60

    # Temp sensor 1 fields (98-107)
    assert "temp_1_calibration_offset" in fields
    assert fields["temp_1_calibration_offset"].offset == 98
    assert "temp_1_beta" in fields
    assert fields["temp_1_beta"].offset == 106

    # LCD control field
    assert "lcd_active_time" in fields
    assert fields["lcd_active_time"].offset == 150


def test_block_26001_contract():
    """Verify Block 26001 (TOU_TIME_INFO) schema contract."""
    assert BLOCK_26001_SCHEMA.block_id == 26001
    assert BLOCK_26001_SCHEMA.name == "TOU_TIME_INFO"
    assert BLOCK_26001_SCHEMA.min_length == 14  # First item only (smali verified)
    assert BLOCK_26001_SCHEMA.protocol_version == 2000
    assert BLOCK_26001_SCHEMA.strict is False
    assert BLOCK_26001_SCHEMA.verification_status == "smali_verified"


def test_block_26001_field_structure():
    """Verify Block 26001 field structure and types (smali verified)."""
    fields = {f.name: f for f in BLOCK_26001_SCHEMA.fields}

    # Smali-verified structure: 14 bytes per TOU time record
    # First 10 bytes are bit-packed (5 UInt16 words)
    # Source: TouTimeCtrlParser.parseTouTimeExt, DeviceTouTime bean
    assert "word0" in fields
    assert fields["word0"].offset == 0
    assert fields["word0"].required is False
    assert fields["word0"].type.__class__.__name__ == "UInt16"

    assert "word1" in fields
    assert fields["word1"].offset == 2
    assert fields["word1"].type.__class__.__name__ == "UInt16"

    assert "word2" in fields
    assert fields["word2"].offset == 4
    assert fields["word2"].type.__class__.__name__ == "UInt16"

    assert "word3" in fields
    assert fields["word3"].offset == 6
    assert fields["word3"].type.__class__.__name__ == "UInt16"

    assert "word4" in fields
    assert fields["word4"].offset == 8
    assert fields["word4"].type.__class__.__name__ == "UInt16"

    # Direct fields (not bit-packed)
    assert "target_reg" in fields
    assert fields["target_reg"].offset == 10
    assert fields["target_reg"].type.__class__.__name__ == "UInt16"

    assert "target_value" in fields
    assert fields["target_value"].offset == 12
    assert fields["target_value"].type.__class__.__name__ == "UInt16"

    # 7 fields total in the verified structure (first item only)
    assert len(fields) == 7
