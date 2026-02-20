"""Test declarative Block 1500 definition."""


def test_block_1500_declarative_schema_generation():
    """Test that InvInvInfoBlock generates valid BlockSchema."""
    from power_sdk.plugins.bluetti.v2.schemas.block_1500_declarative import (
        InvInvInfoBlock,
    )

    schema = InvInvInfoBlock.to_schema()

    # Check basic properties
    assert schema.block_id == 1500
    assert schema.name == "INV_INV_INFO"
    assert schema.min_length == 30
    assert schema.protocol_version == 2000
    assert schema.strict is False

    # Check has fields
    assert len(schema.fields) > 0

    # Check specific critical fields exist
    field_names = {f.name for f in schema.fields}
    assert "frequency" in field_names
    assert "total_energy" in field_names
    assert "sys_phase_number" in field_names
    assert "phase_0_work_status" in field_names
    assert "phase_0_voltage" in field_names


def test_block_1500_declarative_contract():
    """Test canonical Block 1500 schema contract."""
    from power_sdk.plugins.bluetti.v2.schemas.block_1500_declarative import (
        BLOCK_1500_DECLARATIVE_SCHEMA,
    )

    assert BLOCK_1500_DECLARATIVE_SCHEMA.block_id == 1500
    assert BLOCK_1500_DECLARATIVE_SCHEMA.name == "INV_INV_INFO"
    assert BLOCK_1500_DECLARATIVE_SCHEMA.min_length == 30

    # Verify min_length includes global fields + Phase 0 (single-phase baseline)
    assert BLOCK_1500_DECLARATIVE_SCHEMA.min_length >= 30


def test_block_1500_declarative_field_structure():
    """Test specific field details in declarative Block 1500."""
    from power_sdk.plugins.bluetti.v2.protocol.datatypes import UInt8, UInt16, UInt32
    from power_sdk.plugins.bluetti.v2.schemas.block_1500_declarative import (
        InvInvInfoBlock,
    )

    schema = InvInvInfoBlock.to_schema()
    fields_by_name = {f.name: f for f in schema.fields}

    # Test global parameters
    frequency = fields_by_name["frequency"]
    assert frequency.offset == 0
    assert isinstance(frequency.type, UInt16)
    assert len(frequency.transform) == 1
    assert frequency.transform[0].name == "scale"
    assert frequency.unit == "Hz"
    assert frequency.required is True

    total_energy = fields_by_name["total_energy"]
    assert total_energy.offset == 2
    assert isinstance(total_energy.type, UInt32)
    assert len(total_energy.transform) == 1
    assert total_energy.transform[0].name == "scale"
    assert total_energy.unit == "kWh"
    assert total_energy.required is True

    sys_phase_number = fields_by_name["sys_phase_number"]
    assert sys_phase_number.offset == 17
    assert isinstance(sys_phase_number.type, UInt8)
    assert sys_phase_number.required is True

    phase_0_work_status = fields_by_name["phase_0_work_status"]
    assert phase_0_work_status.offset == 19
    assert isinstance(phase_0_work_status.type, UInt8)

    # Test Phase 0 output fields
    phase_0_power = fields_by_name["phase_0_power"]
    assert phase_0_power.offset == 20
    assert isinstance(phase_0_power.type, UInt16)

    phase_0_voltage = fields_by_name["phase_0_voltage"]
    assert phase_0_voltage.offset == 22
    assert isinstance(phase_0_voltage.type, UInt16)
    assert len(phase_0_voltage.transform) == 1
    assert phase_0_voltage.transform[0].name == "scale"
    assert phase_0_voltage.required is True

    phase_0_current = fields_by_name["phase_0_current"]
    assert phase_0_current.offset == 24
    assert isinstance(phase_0_current.type, UInt16)
    assert len(phase_0_current.transform) == 1
    assert phase_0_current.transform[0].name == "scale"
