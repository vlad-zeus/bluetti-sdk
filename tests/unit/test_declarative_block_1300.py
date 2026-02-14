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
    from bluetti_sdk.schemas.block_1300_declarative import InvGridInfoBlock

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


def test_block_1300_declarative_vs_imperative():
    """Test declarative and imperative Block 1300 schemas are equivalent."""
    from bluetti_sdk.schemas.block_1300 import BLOCK_1300_SCHEMA
    from bluetti_sdk.schemas.block_1300_declarative import (
        BLOCK_1300_DECLARATIVE_SCHEMA,
    )

    # Both schemas should have same basic properties
    assert BLOCK_1300_SCHEMA.block_id == BLOCK_1300_DECLARATIVE_SCHEMA.block_id
    assert BLOCK_1300_SCHEMA.name == BLOCK_1300_DECLARATIVE_SCHEMA.name
    assert BLOCK_1300_SCHEMA.min_length == BLOCK_1300_DECLARATIVE_SCHEMA.min_length
    assert BLOCK_1300_SCHEMA.strict == BLOCK_1300_DECLARATIVE_SCHEMA.strict

    # Both should have same number of fields
    assert len(BLOCK_1300_SCHEMA.fields) == len(BLOCK_1300_DECLARATIVE_SCHEMA.fields)

    # Build field maps for comparison
    imperative_fields = {f.name: f for f in BLOCK_1300_SCHEMA.fields}
    declarative_fields = {f.name: f for f in BLOCK_1300_DECLARATIVE_SCHEMA.fields}

    # Check all field names match
    assert set(imperative_fields.keys()) == set(declarative_fields.keys())

    # Check key field properties match
    for name in imperative_fields:
        imp_field = imperative_fields[name]
        dec_field = declarative_fields[name]

        # Check offsets match
        assert imp_field.offset == dec_field.offset, f"Field '{name}': offset mismatch"

        # Check types match (fingerprint comparison includes parameters)
        imp_fingerprint = _get_type_fingerprint(imp_field.type)
        dec_fingerprint = _get_type_fingerprint(dec_field.type)
        assert imp_fingerprint == dec_fingerprint, (
            f"Field '{name}': type mismatch - "
            f"imperative={imp_fingerprint}, declarative={dec_fingerprint}"
        )

        # Check units match
        assert imp_field.unit == dec_field.unit, f"Field '{name}': unit mismatch"

        # Check required flag matches
        assert imp_field.required == dec_field.required, (
            f"Field '{name}': required mismatch"
        )

        # Check transforms match (both should be tuples or None)
        if imp_field.transform or dec_field.transform:
            imp_xform = tuple(imp_field.transform) if imp_field.transform else None
            dec_xform = tuple(dec_field.transform) if dec_field.transform else None
            assert imp_xform == dec_xform, f"Field '{name}': transform mismatch"


def test_block_1300_declarative_field_details():
    """Test specific field details in declarative Block 1300."""
    from bluetti_sdk.schemas.block_1300_declarative import InvGridInfoBlock

    schema = InvGridInfoBlock.to_schema()
    fields_by_name = {f.name: f for f in schema.fields}

    # Test frequency
    frequency = fields_by_name["frequency"]
    assert frequency.offset == 0
    assert frequency.unit == "Hz"
    assert frequency.transform == ("scale:0.1",)
    assert frequency.required is True

    # Test phase_0_voltage
    phase_0_voltage = fields_by_name["phase_0_voltage"]
    assert phase_0_voltage.offset == 28
    assert phase_0_voltage.unit == "V"
    assert phase_0_voltage.transform == ("scale:0.1",)
    assert phase_0_voltage.required is True

    # Test phase_0_current (has compound transform)
    phase_0_current = fields_by_name["phase_0_current"]
    assert phase_0_current.offset == 30
    assert phase_0_current.unit == "A"
    assert phase_0_current.transform == ("abs", "scale:0.1")
    assert phase_0_current.required is True

    # Test phase_0_power (uses abs transform)
    phase_0_power = fields_by_name["phase_0_power"]
    assert phase_0_power.offset == 26
    assert phase_0_power.unit == "W"
    assert phase_0_power.transform == ("abs",)
    assert phase_0_power.required is True
    from bluetti_sdk.protocol.v2.datatypes import Int16

    assert isinstance(phase_0_power.type, Int16)

    # Test optional fields
    total_charge_energy = fields_by_name["total_charge_energy"]
    assert total_charge_energy.required is False
    from bluetti_sdk.protocol.v2.datatypes import UInt32

    assert isinstance(total_charge_energy.type, UInt32)


def test_block_1300_declarative_immutability():
    """Test that declarative Block 1300 schema is immutable."""
    import dataclasses

    from bluetti_sdk.schemas.block_1300_declarative import InvGridInfoBlock

    schema = InvGridInfoBlock.to_schema()

    # Schema should be frozen
    with pytest.raises(dataclasses.FrozenInstanceError):
        schema.name = "HACKED"

    # Fields should be immutable tuples
    with pytest.raises(AttributeError):
        schema.fields.append(None)  # tuple has no append
