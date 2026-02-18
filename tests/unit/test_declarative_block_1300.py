"""Test declarative Block 1300 definition."""

import pytest


def _get_type_fingerprint(field_type) -> str:
    """Get type fingerprint including parameters.

    This ensures we catch differences like String(length=8) vs String(length=12).
    Similar to SchemaRegistry._get_type_fingerprint().
    """
    type_name = type(field_type).__name__
    params = []

    if hasattr(field_type, "length"):
        params.append(f"length={field_type.length}")

    if hasattr(field_type, "bits"):
        params.append(f"bits={field_type.bits}")

    if hasattr(field_type, "mapping") and field_type.mapping is not None:
        mapping_items = sorted(field_type.mapping.items())
        mapping_repr = repr(tuple(mapping_items))
        params.append(f"mapping={mapping_repr}")

    return f"{type_name}({', '.join(params)})" if params else type_name


def test_block_1300_declarative_schema_generation():
    """Test that InvGridInfoBlock generates valid BlockSchema."""
    from power_sdk.plugins.bluetti.v2.schemas.block_1300_declarative import InvGridInfoBlock

    schema = InvGridInfoBlock.to_schema()

    # Check basic properties
    assert schema.block_id == 1300
    assert schema.name == "INV_GRID_INFO"
    assert schema.min_length == 32
    assert schema.protocol_version == 2000
    assert schema.strict is True

    # Check has fields
    assert len(schema.fields) > 0

    # Check specific critical fields exist
    field_names = {f.name for f in schema.fields}
    assert "frequency" in field_names
    assert "phase_0_voltage" in field_names
    assert "phase_0_current" in field_names
    assert "phase_0_power" in field_names


def test_block_1300_declarative_contract():
    """Test canonical Block 1300 schema contract."""
    from power_sdk.plugins.bluetti.v2.schemas.block_1300_declarative import BLOCK_1300_DECLARATIVE_SCHEMA

    assert BLOCK_1300_DECLARATIVE_SCHEMA.block_id == 1300
    assert BLOCK_1300_DECLARATIVE_SCHEMA.name == "INV_GRID_INFO"
    assert BLOCK_1300_DECLARATIVE_SCHEMA.min_length == 32
    assert BLOCK_1300_DECLARATIVE_SCHEMA.strict is True
    assert len(BLOCK_1300_DECLARATIVE_SCHEMA.fields) == 8

    field_names = {f.name for f in BLOCK_1300_DECLARATIVE_SCHEMA.fields}
    expected_names = {
        "frequency",
        "phase_1_voltage",
        "phase_2_voltage",
        "total_charge_energy",
        "total_feedback_energy",
        "phase_0_power",
        "phase_0_voltage",
        "phase_0_current",
    }
    assert field_names == expected_names


def test_block_1300_declarative_field_details():
    """Test specific field details in declarative Block 1300."""
    from power_sdk.protocol.v2.transforms import TransformStep
    from power_sdk.plugins.bluetti.v2.schemas.block_1300_declarative import InvGridInfoBlock

    schema = InvGridInfoBlock.to_schema()
    fields_by_name = {f.name: f for f in schema.fields}

    # Test frequency - typed transform instead of string DSL
    frequency = fields_by_name["frequency"]
    assert frequency.offset == 0
    assert frequency.unit == "Hz"
    assert len(frequency.transform) == 1
    assert isinstance(frequency.transform[0], TransformStep)
    assert frequency.transform[0].name == "scale"
    assert frequency.required is True

    # Test phase_0_voltage - typed transform
    phase_0_voltage = fields_by_name["phase_0_voltage"]
    assert phase_0_voltage.offset == 28
    assert phase_0_voltage.unit == "V"
    assert len(phase_0_voltage.transform) == 1
    assert isinstance(phase_0_voltage.transform[0], TransformStep)
    assert phase_0_voltage.transform[0].name == "scale"
    assert phase_0_voltage.required is True

    # Test phase_0_current (has compound typed transform: abs + scale)
    phase_0_current = fields_by_name["phase_0_current"]
    assert phase_0_current.offset == 30
    assert phase_0_current.unit == "A"
    assert len(phase_0_current.transform) == 2
    assert isinstance(phase_0_current.transform[0], TransformStep)
    assert isinstance(phase_0_current.transform[1], TransformStep)
    assert phase_0_current.transform[0].name == "abs"
    assert phase_0_current.transform[1].name == "scale"
    assert phase_0_current.required is True

    # Test phase_0_power (uses typed abs transform)
    phase_0_power = fields_by_name["phase_0_power"]
    assert phase_0_power.offset == 26
    assert phase_0_power.unit == "W"
    assert len(phase_0_power.transform) == 1
    assert isinstance(phase_0_power.transform[0], TransformStep)
    assert phase_0_power.transform[0].name == "abs"
    assert phase_0_power.required is True
    from power_sdk.protocol.v2.datatypes import Int16

    assert isinstance(phase_0_power.type, Int16)

    # Test optional fields
    total_charge_energy = fields_by_name["total_charge_energy"]
    assert total_charge_energy.required is False
    from power_sdk.protocol.v2.datatypes import UInt32

    assert isinstance(total_charge_energy.type, UInt32)


def test_block_1300_declarative_immutability():
    """Test that declarative Block 1300 schema is immutable."""
    import dataclasses

    from power_sdk.plugins.bluetti.v2.schemas.block_1300_declarative import InvGridInfoBlock

    schema = InvGridInfoBlock.to_schema()

    # Schema should be frozen
    with pytest.raises(dataclasses.FrozenInstanceError):
        schema.name = "HACKED"

    # Fields should be immutable tuples
    with pytest.raises(AttributeError):
        schema.fields.append(None)  # tuple has no append

