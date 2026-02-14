"""Test declarative Block 100 definition."""

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


def test_block_100_declarative_schema_generation():
    """Test that AppHomeDataBlock generates valid BlockSchema."""
    from bluetti_sdk.schemas.block_100_declarative import AppHomeDataBlock

    schema = AppHomeDataBlock.to_schema()

    # Check basic properties
    assert schema.block_id == 100
    assert schema.name == "APP_HOME_DATA"
    assert schema.min_length == 120
    assert schema.protocol_version == 2000
    assert schema.strict is False

    # Check has fields
    assert len(schema.fields) > 0

    # Check specific critical fields exist
    field_names = {f.name for f in schema.fields}
    assert "pack_voltage" in field_names
    assert "soc" in field_names
    assert "device_model" in field_names
    assert "pv_power" in field_names


def test_block_100_declarative_vs_imperative():
    """Test declarative and imperative Block 100 schemas are equivalent."""
    from bluetti_sdk.schemas.block_100 import BLOCK_100_SCHEMA
    from bluetti_sdk.schemas.block_100_declarative import (
        BLOCK_100_DECLARATIVE_SCHEMA,
    )

    # Both schemas should have same basic properties
    assert BLOCK_100_SCHEMA.block_id == BLOCK_100_DECLARATIVE_SCHEMA.block_id
    assert BLOCK_100_SCHEMA.name == BLOCK_100_DECLARATIVE_SCHEMA.name
    assert BLOCK_100_SCHEMA.min_length == BLOCK_100_DECLARATIVE_SCHEMA.min_length
    assert BLOCK_100_SCHEMA.strict == BLOCK_100_DECLARATIVE_SCHEMA.strict

    # Both should have same number of fields
    assert len(BLOCK_100_SCHEMA.fields) == len(
        BLOCK_100_DECLARATIVE_SCHEMA.fields
    )

    # Build field maps for comparison
    imperative_fields = {f.name: f for f in BLOCK_100_SCHEMA.fields}
    declarative_fields = {
        f.name: f for f in BLOCK_100_DECLARATIVE_SCHEMA.fields
    }

    # Check all field names match
    assert set(imperative_fields.keys()) == set(declarative_fields.keys())

    # Check key field properties match
    for name in imperative_fields:
        imp_field = imperative_fields[name]
        dec_field = declarative_fields[name]

        # Check offsets match
        assert imp_field.offset == dec_field.offset, (
            f"Field '{name}': offset mismatch"
        )

        # Check types match (fingerprint comparison includes parameters)
        imp_fingerprint = _get_type_fingerprint(imp_field.type)
        dec_fingerprint = _get_type_fingerprint(dec_field.type)
        assert imp_fingerprint == dec_fingerprint, (
            f"Field '{name}': type mismatch - "
            f"imperative={imp_fingerprint}, declarative={dec_fingerprint}"
        )

        # Check units match
        assert imp_field.unit == dec_field.unit, f"Field '{name}': unit mismatch"

        # Check transforms match (both should be tuples or None)
        if imp_field.transform or dec_field.transform:
            imp_xform = tuple(imp_field.transform) if imp_field.transform else None
            dec_xform = tuple(dec_field.transform) if dec_field.transform else None
            assert imp_xform == dec_xform, (
                f"Field '{name}': transform mismatch"
            )


def test_block_100_declarative_field_details():
    """Test specific field details in declarative Block 100."""
    from bluetti_sdk.schemas.block_100_declarative import AppHomeDataBlock

    schema = AppHomeDataBlock.to_schema()
    fields_by_name = {f.name: f for f in schema.fields}

    # Test pack_voltage
    pack_voltage = fields_by_name["pack_voltage"]
    assert pack_voltage.offset == 0
    assert pack_voltage.unit == "V"
    assert pack_voltage.transform == ("scale:0.1",)
    assert pack_voltage.required is True

    # Test soc
    soc = fields_by_name["soc"]
    assert soc.offset == 4
    assert soc.unit == "%"
    assert soc.required is True

    # Test grid_power (signed int32)
    grid_power = fields_by_name["grid_power"]
    assert grid_power.offset == 92
    assert grid_power.unit == "W"
    assert grid_power.min_protocol_version == 2001
    from bluetti_sdk.protocol.v2.datatypes import Int32
    assert isinstance(grid_power.type, Int32)

    # Test device_model (string)
    device_model = fields_by_name["device_model"]
    assert device_model.offset == 20
    from bluetti_sdk.protocol.v2.datatypes import String
    assert isinstance(device_model.type, String)
    assert device_model.type.length == 12


def test_block_100_declarative_immutability():
    """Test that declarative Block 100 schema is immutable."""
    import dataclasses

    from bluetti_sdk.schemas.block_100_declarative import AppHomeDataBlock

    schema = AppHomeDataBlock.to_schema()

    # Schema should be frozen
    with pytest.raises(dataclasses.FrozenInstanceError):
        schema.name = "HACKED"

    # Fields should be immutable tuples
    with pytest.raises(AttributeError):
        schema.fields.append(None)  # tuple has no append
