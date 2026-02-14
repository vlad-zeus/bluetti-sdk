"""Test declarative Block 6000 definition."""

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


def test_block_6000_declarative_schema_generation():
    """Test that PackMainInfoBlock generates valid BlockSchema."""
    from bluetti_sdk.schemas.block_6000_declarative import PackMainInfoBlock

    schema = PackMainInfoBlock.to_schema()

    # Check basic properties
    assert schema.block_id == 6000
    assert schema.name == "PACK_MAIN_INFO"
    assert schema.min_length == 64
    assert schema.protocol_version == 2000
    assert schema.strict is False

    # Check has fields
    assert len(schema.fields) > 0

    # Check specific critical fields exist
    field_names = {f.name for f in schema.fields}
    assert "voltage" in field_names
    assert "current" in field_names
    assert "soc" in field_names
    assert "soh" in field_names
    assert "temp_avg" in field_names


def test_block_6000_declarative_vs_imperative():
    """Test declarative and imperative Block 6000 schemas are equivalent."""
    from bluetti_sdk.schemas.block_6000 import BLOCK_6000_SCHEMA
    from bluetti_sdk.schemas.block_6000_declarative import (
        BLOCK_6000_DECLARATIVE_SCHEMA,
    )

    # Both schemas should have same basic properties
    assert BLOCK_6000_SCHEMA.block_id == BLOCK_6000_DECLARATIVE_SCHEMA.block_id
    assert BLOCK_6000_SCHEMA.name == BLOCK_6000_DECLARATIVE_SCHEMA.name
    assert BLOCK_6000_SCHEMA.min_length == BLOCK_6000_DECLARATIVE_SCHEMA.min_length
    assert BLOCK_6000_SCHEMA.strict == BLOCK_6000_DECLARATIVE_SCHEMA.strict

    # Both should have same number of fields
    assert len(BLOCK_6000_SCHEMA.fields) == len(BLOCK_6000_DECLARATIVE_SCHEMA.fields)

    # Build field maps for comparison
    imperative_fields = {f.name: f for f in BLOCK_6000_SCHEMA.fields}
    declarative_fields = {f.name: f for f in BLOCK_6000_DECLARATIVE_SCHEMA.fields}

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


def test_block_6000_declarative_field_details():
    """Test specific field details in declarative Block 6000."""
    from bluetti_sdk.schemas.block_6000_declarative import PackMainInfoBlock

    schema = PackMainInfoBlock.to_schema()
    fields_by_name = {f.name: f for f in schema.fields}

    # Test voltage
    voltage = fields_by_name["voltage"]
    assert voltage.offset == 6
    assert voltage.unit == "V"
    assert voltage.transform == ("scale:0.1",)
    assert voltage.required is True

    # Test soc (UInt8)
    soc = fields_by_name["soc"]
    assert soc.offset == 11
    assert soc.unit == "%"
    assert soc.required is True
    from bluetti_sdk.protocol.v2.datatypes import UInt8

    assert isinstance(soc.type, UInt8)

    # Test temp_avg (uses minus transform)
    temp_avg = fields_by_name["temp_avg"]
    assert temp_avg.offset == 14
    assert temp_avg.unit == "°C"
    assert temp_avg.transform == ("minus:40",)

    # Test max_charge_current
    max_charge_current = fields_by_name["max_charge_current"]
    assert max_charge_current.offset == 22
    assert max_charge_current.unit == "A"
    assert max_charge_current.transform == ("scale:0.1",)
    from bluetti_sdk.protocol.v2.datatypes import UInt16

    assert isinstance(max_charge_current.type, UInt16)

    # Test time_to_full
    time_to_full = fields_by_name["time_to_full"]
    assert time_to_full.offset == 34
    assert time_to_full.unit == "min"


def test_block_6000_declarative_immutability():
    """Test that declarative Block 6000 schema is immutable."""
    import dataclasses

    from bluetti_sdk.schemas.block_6000_declarative import PackMainInfoBlock

    schema = PackMainInfoBlock.to_schema()

    # Schema should be frozen
    with pytest.raises(dataclasses.FrozenInstanceError):
        schema.name = "HACKED"

    # Fields should be immutable tuples
    with pytest.raises(AttributeError):
        schema.fields.append(None)  # tuple has no append
