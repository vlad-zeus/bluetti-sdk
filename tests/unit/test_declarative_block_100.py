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
    from power_sdk.plugins.bluetti.v2.schemas.block_100_declarative import (
        AppHomeDataBlock,
    )

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


def test_block_100_declarative_contract():
    """Test canonical Block 100 schema contract."""
    from power_sdk.plugins.bluetti.v2.schemas.block_100_declarative import (
        BLOCK_100_DECLARATIVE_SCHEMA,
    )

    assert BLOCK_100_DECLARATIVE_SCHEMA.block_id == 100
    assert BLOCK_100_DECLARATIVE_SCHEMA.name == "APP_HOME_DATA"
    assert BLOCK_100_DECLARATIVE_SCHEMA.min_length == 120
    assert BLOCK_100_DECLARATIVE_SCHEMA.strict is False
    assert len(BLOCK_100_DECLARATIVE_SCHEMA.fields) == 25

    field_names = {f.name for f in BLOCK_100_DECLARATIVE_SCHEMA.fields}
    expected_names = {
        "pack_voltage",
        "pack_current",
        "soc",
        "pack_power",
        "load_power",
        "pack_online",
        "device_model",
        "device_serial",
        "pack_temp_avg",
        "pack_temp_max",
        "pack_temp_min",
        "dc_input_power",
        "ac_input_power",
        "pv_power",
        "grid_power",
        "total_energy_charge",
        "ac_output_power",
        "pv_charge_energy",
        "total_energy_discharge",
        "total_feedback_energy",
        "soh",
        "pv1_voltage",
        "pv1_current",
        "pv2_voltage",
        "pv2_current",
    }
    assert field_names == expected_names


def test_block_100_declarative_field_details():
    """Test specific field details in declarative Block 100."""
    from power_sdk.plugins.bluetti.v2.protocol.transforms import TransformStep
    from power_sdk.plugins.bluetti.v2.schemas.block_100_declarative import (
        AppHomeDataBlock,
    )

    schema = AppHomeDataBlock.to_schema()
    fields_by_name = {f.name: f for f in schema.fields}

    # Test pack_voltage
    pack_voltage = fields_by_name["pack_voltage"]
    assert pack_voltage.offset == 0
    assert pack_voltage.unit == "V"
    # Verify typed transform (no longer string DSL)
    assert len(pack_voltage.transform) == 1
    assert isinstance(pack_voltage.transform[0], TransformStep)
    assert pack_voltage.transform[0].name == "scale"
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
    from power_sdk.plugins.bluetti.v2.protocol.datatypes import Int32

    assert isinstance(grid_power.type, Int32)

    # Test device_model (string)
    device_model = fields_by_name["device_model"]
    assert device_model.offset == 20
    from power_sdk.plugins.bluetti.v2.protocol.datatypes import String

    assert isinstance(device_model.type, String)
    assert device_model.type.length == 12


def test_block_100_declarative_immutability():
    """Test that declarative Block 100 schema is immutable."""
    import dataclasses

    from power_sdk.plugins.bluetti.v2.schemas.block_100_declarative import (
        AppHomeDataBlock,
    )

    schema = AppHomeDataBlock.to_schema()

    # Schema should be frozen
    with pytest.raises(dataclasses.FrozenInstanceError):
        schema.name = "HACKED"

    # Fields should be immutable tuples
    with pytest.raises(AttributeError):
        schema.fields.append(None)  # tuple has no append

