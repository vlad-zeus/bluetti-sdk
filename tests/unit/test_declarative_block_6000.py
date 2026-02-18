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
    from power_sdk.plugins.bluetti.v2.schemas.block_6000_declarative import PackMainInfoBlock

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


def test_block_6000_declarative_contract():
    """Test canonical Block 6000 schema contract."""
    from power_sdk.plugins.bluetti.v2.schemas.block_6000_declarative import BLOCK_6000_DECLARATIVE_SCHEMA

    assert BLOCK_6000_DECLARATIVE_SCHEMA.block_id == 6000
    assert BLOCK_6000_DECLARATIVE_SCHEMA.name == "PACK_MAIN_INFO"
    assert BLOCK_6000_DECLARATIVE_SCHEMA.min_length == 64
    assert BLOCK_6000_DECLARATIVE_SCHEMA.strict is False
    assert len(BLOCK_6000_DECLARATIVE_SCHEMA.fields) == 22

    field_names = {f.name for f in BLOCK_6000_DECLARATIVE_SCHEMA.fields}
    expected_names = {
        "pack_volt_type",
        "pack_count",
        "pack_online",
        "voltage",
        "current",
        "power",
        "soc",
        "soh",
        "temp_avg",
        "running_status",
        "charging_status",
        "max_charge_voltage",
        "max_charge_current",
        "max_discharge_current",
        "pack_mos",
        "time_to_full",
        "time_to_empty",
        "cell_count",
        "cycles",
        "temp_max",
        "temp_min",
        "pack_fault_bits",
    }
    assert field_names == expected_names


def test_block_6000_declarative_field_details():
    """Test specific field details in declarative Block 6000."""
    from power_sdk.protocol.v2.transforms import TransformStep
    from power_sdk.plugins.bluetti.v2.schemas.block_6000_declarative import PackMainInfoBlock

    schema = PackMainInfoBlock.to_schema()
    fields_by_name = {f.name: f for f in schema.fields}

    # Test voltage - typed transform instead of string DSL
    voltage = fields_by_name["voltage"]
    assert voltage.offset == 6
    assert voltage.unit == "V"
    assert len(voltage.transform) == 1
    assert isinstance(voltage.transform[0], TransformStep)
    assert voltage.transform[0].name == "scale"
    assert voltage.required is True

    # Test soc (UInt8)
    soc = fields_by_name["soc"]
    assert soc.offset == 11
    assert soc.unit == "%"
    assert soc.required is True
    from power_sdk.protocol.v2.datatypes import UInt8

    assert isinstance(soc.type, UInt8)

    # Test temp_avg (uses typed minus transform)
    temp_avg = fields_by_name["temp_avg"]
    assert temp_avg.offset == 14
    assert temp_avg.unit == "°C"
    assert len(temp_avg.transform) == 1
    assert isinstance(temp_avg.transform[0], TransformStep)
    assert temp_avg.transform[0].name == "minus"

    # Test max_charge_current - typed transform
    max_charge_current = fields_by_name["max_charge_current"]
    assert max_charge_current.offset == 22
    assert max_charge_current.unit == "A"
    assert len(max_charge_current.transform) == 1
    assert isinstance(max_charge_current.transform[0], TransformStep)
    assert max_charge_current.transform[0].name == "scale"
    from power_sdk.protocol.v2.datatypes import UInt16

    assert isinstance(max_charge_current.type, UInt16)

    # Test time_to_full
    time_to_full = fields_by_name["time_to_full"]
    assert time_to_full.offset == 34
    assert time_to_full.unit == "min"


def test_block_6000_declarative_immutability():
    """Test that declarative Block 6000 schema is immutable."""
    import dataclasses

    from power_sdk.plugins.bluetti.v2.schemas.block_6000_declarative import PackMainInfoBlock

    schema = PackMainInfoBlock.to_schema()

    # Schema should be frozen
    with pytest.raises(dataclasses.FrozenInstanceError):
        schema.name = "HACKED"

    # Fields should be immutable tuples
    with pytest.raises(AttributeError):
        schema.fields.append(None)  # tuple has no append

