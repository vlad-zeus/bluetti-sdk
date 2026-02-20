"""Test declarative Block 1400 definition."""


def test_block_1400_declarative_schema_generation():
    """Test that InvLoadInfoBlock generates valid BlockSchema."""
    from power_sdk.plugins.bluetti.v2.schemas.block_1400_declarative import (
        InvLoadInfoBlock,
    )

    schema = InvLoadInfoBlock.to_schema()

    # Check basic properties
    assert schema.block_id == 1400
    assert schema.name == "INV_LOAD_INFO"
    assert schema.min_length == 72
    assert schema.protocol_version == 2000
    assert schema.strict is False

    # Check has fields
    assert len(schema.fields) > 0

    # Check specific critical fields exist
    field_names = {f.name for f in schema.fields}
    assert "dc_total_power" in field_names
    assert "ac_total_power" in field_names
    assert "load_5v_power" in field_names
    assert "load_5v_current" in field_names
    assert "sys_phase_number" in field_names
    assert "phase_0_voltage" in field_names


def test_block_1400_declarative_contract():
    """Test canonical Block 1400 schema contract."""
    from power_sdk.plugins.bluetti.v2.schemas.block_1400_declarative import (
        BLOCK_1400_DECLARATIVE_SCHEMA,
    )

    assert BLOCK_1400_DECLARATIVE_SCHEMA.block_id == 1400
    assert BLOCK_1400_DECLARATIVE_SCHEMA.name == "INV_LOAD_INFO"
    assert BLOCK_1400_DECLARATIVE_SCHEMA.min_length == 72

    # Verify min_length includes DC loads + AC total + Phase 0 (single-phase baseline)
    assert BLOCK_1400_DECLARATIVE_SCHEMA.min_length >= 72


def test_block_1400_declarative_field_structure():
    """Test specific field details in declarative Block 1400."""
    from power_sdk.plugins.bluetti.v2.protocol.datatypes import UInt8, UInt16, UInt32
    from power_sdk.plugins.bluetti.v2.schemas.block_1400_declarative import (
        InvLoadInfoBlock,
    )

    schema = InvLoadInfoBlock.to_schema()
    fields_by_name = {f.name: f for f in schema.fields}

    # Test DC total fields
    dc_total_power = fields_by_name["dc_total_power"]
    assert dc_total_power.offset == 0
    assert isinstance(dc_total_power.type, UInt32)
    assert dc_total_power.unit == "W"
    assert dc_total_power.required is True

    dc_total_energy = fields_by_name["dc_total_energy"]
    assert dc_total_energy.offset == 4
    assert isinstance(dc_total_energy.type, UInt32)
    assert len(dc_total_energy.transform) == 1
    assert dc_total_energy.transform[0].name == "scale"
    assert dc_total_energy.unit == "kWh"

    # Test 5V output fields
    load_5v_power = fields_by_name["load_5v_power"]
    assert load_5v_power.offset == 8
    assert isinstance(load_5v_power.type, UInt16)
    assert load_5v_power.unit == "W"

    load_5v_current = fields_by_name["load_5v_current"]
    assert load_5v_current.offset == 10
    assert isinstance(load_5v_current.type, UInt16)
    assert load_5v_current.transform[0].name == "scale"

    # Test AC total fields
    ac_total_power = fields_by_name["ac_total_power"]
    assert ac_total_power.offset == 40
    assert isinstance(ac_total_power.type, UInt32)
    assert ac_total_power.required is True

    # Test phase number field
    sys_phase_number = fields_by_name["sys_phase_number"]
    assert sys_phase_number.offset == 59
    assert isinstance(sys_phase_number.type, UInt8)

    # Test Phase 0 AC load fields
    phase_0_power = fields_by_name["phase_0_power"]
    assert phase_0_power.offset == 60
    assert isinstance(phase_0_power.type, UInt16)
    assert phase_0_power.required is True

    phase_0_voltage = fields_by_name["phase_0_voltage"]
    assert phase_0_voltage.offset == 62
    assert isinstance(phase_0_voltage.type, UInt16)
    assert len(phase_0_voltage.transform) == 1
    assert phase_0_voltage.transform[0].name == "scale"
    assert phase_0_voltage.required is True

    phase_0_current = fields_by_name["phase_0_current"]
    assert phase_0_current.offset == 64
    assert isinstance(phase_0_current.type, UInt16)
    assert len(phase_0_current.transform) == 1
    assert phase_0_current.transform[0].name == "scale"
