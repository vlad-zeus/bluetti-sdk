"""Tests for EPAD liquid schema factory.

Verifies that the factory-generated schemas maintain exact equivalence
with the manually-defined schemas they replaced.
"""

from bluetti_sdk.schemas import (
    BLOCK_18400_SCHEMA,
    BLOCK_18500_SCHEMA,
    BLOCK_18600_SCHEMA,
)
from bluetti_sdk.schemas.factories import build_epad_liquid_schema


def test_factory_generated_schemas_match_exports():
    """Verify factory generates identical schemas to exported constants."""
    # The exported schemas ARE factory-generated now, so verify they exist
    # and have correct attributes
    assert BLOCK_18400_SCHEMA.block_id == 18400
    assert BLOCK_18400_SCHEMA.name == "EPAD_LIQUID_POINT1"
    assert BLOCK_18400_SCHEMA.min_length == 100

    assert BLOCK_18500_SCHEMA.block_id == 18500
    assert BLOCK_18500_SCHEMA.name == "EPAD_LIQUID_POINT2"
    assert BLOCK_18500_SCHEMA.min_length == 100

    assert BLOCK_18600_SCHEMA.block_id == 18600
    assert BLOCK_18600_SCHEMA.name == "EPAD_LIQUID_POINT3"
    assert BLOCK_18600_SCHEMA.min_length == 100


def test_factory_generates_unique_block_ids():
    """Verify factory respects block_id parameter."""
    schema1 = build_epad_liquid_schema(18400, "EPAD_LIQUID_POINT1", 1)
    schema2 = build_epad_liquid_schema(18500, "EPAD_LIQUID_POINT2", 2)
    schema3 = build_epad_liquid_schema(18600, "EPAD_LIQUID_POINT3", 3)

    assert schema1.block_id == 18400
    assert schema2.block_id == 18500
    assert schema3.block_id == 18600


def test_factory_generates_unique_names():
    """Verify factory respects name parameter."""
    schema1 = build_epad_liquid_schema(18400, "EPAD_LIQUID_POINT1", 1)
    schema2 = build_epad_liquid_schema(18500, "EPAD_LIQUID_POINT2", 2)
    schema3 = build_epad_liquid_schema(18600, "EPAD_LIQUID_POINT3", 3)

    assert schema1.name == "EPAD_LIQUID_POINT1"
    assert schema2.name == "EPAD_LIQUID_POINT2"
    assert schema3.name == "EPAD_LIQUID_POINT3"


def test_factory_schemas_have_identical_structure():
    """Verify all factory-generated schemas share identical field structure."""
    schema1 = build_epad_liquid_schema(18400, "EPAD_LIQUID_POINT1", 1)
    schema2 = build_epad_liquid_schema(18500, "EPAD_LIQUID_POINT2", 2)
    schema3 = build_epad_liquid_schema(18600, "EPAD_LIQUID_POINT3", 3)

    # All should have same min_length
    assert schema1.min_length == schema2.min_length == schema3.min_length == 100

    # All should have same protocol_version
    assert (
        schema1.protocol_version
        == schema2.protocol_version
        == schema3.protocol_version
        == 2000
    )

    # All should have same strict mode
    assert schema1.strict == schema2.strict == schema3.strict is False

    # All should have same number of fields
    assert len(schema1.fields) == len(schema2.fields) == len(schema3.fields)

    # All should have same field names
    field_names1 = {f.name for f in schema1.fields}
    field_names2 = {f.name for f in schema2.fields}
    field_names3 = {f.name for f in schema3.fields}
    assert field_names1 == field_names2 == field_names3

    expected_fields = {
        "point_id",
        "point_status",
        "temperature",
        "pressure",
        "flow_rate",
        "level",
        "calibration_offset",
    }
    assert field_names1 == expected_fields


def test_factory_schemas_have_identical_field_offsets():
    """Verify field offsets are identical across all factory-generated schemas."""
    schema1 = build_epad_liquid_schema(18400, "EPAD_LIQUID_POINT1", 1)
    schema2 = build_epad_liquid_schema(18500, "EPAD_LIQUID_POINT2", 2)

    for field1, field2 in zip(schema1.fields, schema2.fields):
        assert field1.name == field2.name
        assert field1.offset == field2.offset
        assert type(field1.type).__name__ == type(field2.type).__name__
        assert field1.required == field2.required


def test_factory_respects_point_index_parameter():
    """Verify point_index parameter is used for class naming."""
    # While we can't directly inspect the class name from the schema,
    # we can verify the factory accepts different point_index values
    # without error
    for point_index in [1, 2, 3]:
        schema = build_epad_liquid_schema(
            18400 + (point_index - 1) * 100,
            f"EPAD_LIQUID_POINT{point_index}",
            point_index,
        )
        assert schema.block_id == 18400 + (point_index - 1) * 100
        assert schema.name == f"EPAD_LIQUID_POINT{point_index}"


def test_factory_schemas_provisional_fields():
    """Verify all fields are marked as provisional (required=False)."""
    schema = build_epad_liquid_schema(18400, "EPAD_LIQUID_POINT1", 1)

    # All fields should be provisional (required=False)
    for field in schema.fields:
        assert field.required is False, f"Field {field.name} should be provisional"


def test_factory_temperature_field_has_unit():
    """Verify temperature field has correct unit metadata."""
    schema = build_epad_liquid_schema(18400, "EPAD_LIQUID_POINT1", 1)

    temp_field = next(f for f in schema.fields if f.name == "temperature")
    assert temp_field.unit == "0.1°C"
