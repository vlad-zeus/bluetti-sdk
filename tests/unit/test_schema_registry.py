"""Unit tests for Schema Registry."""

import dataclasses
import pytest
from bluetti_sdk.schemas import registry
from bluetti_sdk.protocol.v2.schema import BlockSchema, Field
from bluetti_sdk.protocol.v2.datatypes import UInt16


@pytest.fixture
def clean_registry():
    """Clear registry before and after test.

    Use this fixture explicitly in tests that need a clean registry.
    """
    registry._clear_for_testing()
    yield
    registry._clear_for_testing()


@pytest.fixture
def test_schema_1():
    """Create test schema 1."""
    return BlockSchema(
        block_id=9001,
        name="TEST_BLOCK_1",
        description="Test block 1",
        min_length=4,
        fields=[
            Field(name="field1", offset=0, type=UInt16()),
        ]
    )


@pytest.fixture
def test_schema_2():
    """Create test schema 2."""
    return BlockSchema(
        block_id=9002,
        name="TEST_BLOCK_2",
        description="Test block 2",
        min_length=4,
        fields=[
            Field(name="field2", offset=0, type=UInt16()),
        ]
    )


def test_register_schema(clean_registry, test_schema_1):
    """Test registering a single schema."""
    registry.register(test_schema_1)

    # Should be retrievable
    retrieved = registry.get(9001)
    assert retrieved is not None
    assert retrieved.name == "TEST_BLOCK_1"


def test_register_duplicate_schema(clean_registry, test_schema_1):
    """Test registering the same schema twice."""
    registry.register(test_schema_1)

    # Second registration should be silently skipped
    registry.register(test_schema_1)

    # Should still have only one
    assert len(registry.list_blocks()) == 1


def test_register_conflicting_schema(clean_registry, test_schema_1):
    """Test registering different schema with same block_id (different name)."""
    registry.register(test_schema_1)

    # Different schema with same block_id but different name
    conflicting = BlockSchema(
        block_id=9001,
        name="DIFFERENT_NAME",
        description="Different",
        min_length=4,
        fields=[]
    )

    # Should raise error
    with pytest.raises(ValueError, match="already registered"):
        registry.register(conflicting)


def test_register_conflicting_structure(clean_registry, test_schema_1):
    """Test registering schema with same block_id and name but different fields."""
    registry.register(test_schema_1)

    # Same block_id and name, but different fields
    conflicting = BlockSchema(
        block_id=9001,
        name="TEST_BLOCK_1",  # Same name
        description="Different structure",
        min_length=4,
        fields=[
            Field(name="different_field", offset=0, type=UInt16()),
        ]
    )

    # Should raise error about structure conflict
    with pytest.raises(ValueError, match="structure conflict"):
        registry.register(conflicting)


def test_register_conflicting_offset(clean_registry):
    """Test detecting offset changes in field."""
    schema1 = BlockSchema(
        block_id=9003,
        name="TEST",
        description="Test",
        min_length=4,
        fields=[
            Field(name="field1", offset=0, type=UInt16()),
        ]
    )
    registry.register(schema1)

    # Same field name, different offset
    schema2 = BlockSchema(
        block_id=9003,
        name="TEST",
        description="Test",
        min_length=4,
        fields=[
            Field(name="field1", offset=2, type=UInt16()),  # Changed offset
        ]
    )

    with pytest.raises(ValueError, match="offset changed"):
        registry.register(schema2)


def test_register_conflicting_type(clean_registry):
    """Test detecting type changes in field."""
    from bluetti_sdk.protocol.v2.datatypes import UInt8

    schema1 = BlockSchema(
        block_id=9004,
        name="TEST",
        description="Test",
        min_length=4,
        fields=[
            Field(name="field1", offset=0, type=UInt16()),
        ]
    )
    registry.register(schema1)

    # Same field name, different type
    schema2 = BlockSchema(
        block_id=9004,
        name="TEST",
        description="Test",
        min_length=4,
        fields=[
            Field(name="field1", offset=0, type=UInt8()),  # Changed type
        ]
    )

    with pytest.raises(ValueError, match="type changed"):
        registry.register(schema2)


def test_register_conflicting_required(clean_registry):
    """Test detecting required flag changes."""
    schema1 = BlockSchema(
        block_id=9005,
        name="TEST",
        description="Test",
        min_length=4,
        fields=[
            Field(name="field1", offset=0, type=UInt16(), required=True),
        ]
    )
    registry.register(schema1)

    # Same field, different required flag
    schema2 = BlockSchema(
        block_id=9005,
        name="TEST",
        description="Test",
        min_length=4,
        fields=[
            Field(name="field1", offset=0, type=UInt16(), required=False),
        ]
    )

    with pytest.raises(ValueError, match="required changed"):
        registry.register(schema2)


def test_register_conflicting_transform(clean_registry):
    """Test detecting transform changes."""
    schema1 = BlockSchema(
        block_id=9006,
        name="TEST",
        description="Test",
        min_length=4,
        fields=[
            Field(name="field1", offset=0, type=UInt16(), transform=["scale:0.1"]),
        ]
    )
    registry.register(schema1)

    # Same field, different transform
    schema2 = BlockSchema(
        block_id=9006,
        name="TEST",
        description="Test",
        min_length=4,
        fields=[
            Field(name="field1", offset=0, type=UInt16(), transform=["scale:0.01"]),
        ]
    )

    with pytest.raises(ValueError, match="transform changed"):
        registry.register(schema2)


def test_register_conflicting_string_length(clean_registry):
    """Test detecting String type parameter changes (length)."""
    from bluetti_sdk.protocol.v2.datatypes import String

    schema1 = BlockSchema(
        block_id=9007,
        name="TEST",
        description="Test",
        min_length=10,
        fields=[
            Field(name="device_model", offset=0, type=String(length=8)),
        ]
    )
    registry.register(schema1)

    # Same field name and type class, but different length
    schema2 = BlockSchema(
        block_id=9007,
        name="TEST",
        description="Test",
        min_length=14,
        fields=[
            Field(name="device_model", offset=0, type=String(length=12)),
        ]
    )

    # Should detect String(length=8) vs String(length=12) as different
    with pytest.raises(ValueError, match="type changed.*String"):
        registry.register(schema2)


def test_register_conflicting_bitmap_bits(clean_registry):
    """Test detecting Bitmap type parameter changes (bits)."""
    from bluetti_sdk.protocol.v2.datatypes import Bitmap

    schema1 = BlockSchema(
        block_id=9008,
        name="TEST",
        description="Test",
        min_length=4,
        fields=[
            Field(name="status", offset=0, type=Bitmap(bits=16)),
        ]
    )
    registry.register(schema1)

    # Same field name and type class, but different bits
    schema2 = BlockSchema(
        block_id=9008,
        name="TEST",
        description="Test",
        min_length=4,
        fields=[
            Field(name="status", offset=0, type=Bitmap(bits=32)),
        ]
    )

    # Should detect Bitmap(bits=16) vs Bitmap(bits=32) as different
    with pytest.raises(ValueError, match="type changed.*Bitmap"):
        registry.register(schema2)


def test_register_conflicting_enum_mapping(clean_registry):
    """Test detecting Enum type mapping changes."""
    from bluetti_sdk.protocol.v2.datatypes import Enum

    # Two enums with same number of values but different mappings
    schema1 = BlockSchema(
        block_id=9009,
        name="TEST",
        description="Test",
        min_length=4,
        fields=[
            Field(name="mode", offset=0, type=Enum(mapping={
                0: "OFF",
                1: "ON",
                2: "AUTO",
            })),
        ]
    )
    registry.register(schema1)

    # Same number of values (3), but different mapping
    schema2 = BlockSchema(
        block_id=9009,
        name="TEST",
        description="Test",
        min_length=4,
        fields=[
            Field(name="mode", offset=0, type=Enum(mapping={
                0: "DISABLED",  # Different name for 0
                1: "ENABLED",   # Different name for 1
                2: "STANDBY",   # Different name for 2
            })),
        ]
    )

    # Should detect different mapping content, not just size
    with pytest.raises(ValueError, match="type changed.*Enum"):
        registry.register(schema2)


def test_register_many(clean_registry, test_schema_1, test_schema_2):
    """Test registering multiple schemas at once."""
    registry.register_many([test_schema_1, test_schema_2])

    assert len(registry.list_blocks()) == 2
    assert registry.get(9001) is not None
    assert registry.get(9002) is not None


def test_get_nonexistent_schema(clean_registry):
    """Test getting a schema that doesn't exist."""
    result = registry.get(99999)
    assert result is None


def test_list_blocks(clean_registry, test_schema_1, test_schema_2):
    """Test listing registered block IDs."""
    registry.register_many([test_schema_1, test_schema_2])

    blocks = registry.list_blocks()
    assert blocks == [9001, 9002]  # Should be sorted


def test_resolve_blocks_strict(clean_registry, test_schema_1, test_schema_2):
    """Test resolving schemas in strict mode."""
    registry.register_many([test_schema_1, test_schema_2])

    # All schemas available
    resolved = registry.resolve_blocks([9001, 9002], strict=True)
    assert len(resolved) == 2
    assert 9001 in resolved
    assert 9002 in resolved

    # Missing schema should raise error
    with pytest.raises(ValueError, match="Missing schemas"):
        registry.resolve_blocks([9001, 99999], strict=True)


def test_resolve_blocks_lenient(clean_registry, test_schema_1):
    """Test resolving schemas in lenient mode."""
    registry.register(test_schema_1)

    # Should return only found schemas, skip missing
    resolved = registry.resolve_blocks([9001, 99999], strict=False)
    assert len(resolved) == 1
    assert 9001 in resolved
    assert 99999 not in resolved


def test_resolve_empty_list(clean_registry):
    """Test resolving empty block list."""
    resolved = registry.resolve_blocks([], strict=True)
    assert resolved == {}


def test_clear(clean_registry):
    """Test clearing the registry (testing only)."""
    schema = BlockSchema(
        block_id=9001,
        name="TEST",
        description="Test",
        min_length=4,
        fields=[]
    )
    registry.register(schema)
    assert len(registry.list_blocks()) == 1

    registry._clear_for_testing()
    assert len(registry.list_blocks()) == 0
    assert registry.get(9001) is None


def test_lazy_registration():
    """Test lazy registration via ensure_registered().

    Schemas should NOT be registered on import, only when ensure_registered() is called.
    """
    # Clear registry and reset registration flag
    registry._clear_for_testing()

    import bluetti_sdk.schemas
    bluetti_sdk.schemas._reset_registration_flag()

    # After clearing, schemas should NOT be registered yet
    blocks = registry.list_blocks()
    assert len(blocks) == 0

    # Call ensure_registered to trigger lazy registration
    bluetti_sdk.schemas.ensure_registered()

    # Now schemas should be registered
    blocks = bluetti_sdk.schemas.list_blocks()
    assert 100 in blocks  # BLOCK_100_SCHEMA
    assert 1300 in blocks  # BLOCK_1300_SCHEMA
    assert 6000 in blocks  # BLOCK_6000_SCHEMA

    # Verify they're retrievable
    assert bluetti_sdk.schemas.get(100).name == "APP_HOME_DATA"
    assert bluetti_sdk.schemas.get(1300).name == "INV_GRID_INFO"
    assert bluetti_sdk.schemas.get(6000).name == "PACK_MAIN_INFO"

    # Calling ensure_registered() again should be idempotent
    bluetti_sdk.schemas.ensure_registered()
    assert len(bluetti_sdk.schemas.list_blocks()) == 3  # Still 3 schemas


def test_schema_immutability(clean_registry):
    """Test that BlockSchema and Field are immutable (frozen).

    This prevents post-registration mutations that would break wire-format safety.
    """
    schema = BlockSchema(
        block_id=9010,
        name="TEST_IMMUTABLE",
        description="Test immutability",
        min_length=4,
        fields=[
            Field(name="field1", offset=0, type=UInt16()),
        ]
    )

    # Register schema
    registry.register(schema)

    # Attempt to modify BlockSchema - should raise FrozenInstanceError
    with pytest.raises(dataclasses.FrozenInstanceError):
        schema.name = "MODIFIED"

    # Attempt to modify Field - should raise FrozenInstanceError
    field = schema.fields[0]
    with pytest.raises(dataclasses.FrozenInstanceError):
        field.offset = 999

    # Verify schema in registry is still intact
    retrieved = registry.get(9010)
    assert retrieved.name == "TEST_IMMUTABLE"
    assert retrieved.fields[0].offset == 0


def test_datatype_immutability(clean_registry):
    """Test that DataType objects (String, Bitmap, Enum) are immutable.

    This ensures wire-format safety even if types are modified after registration.
    """
    from bluetti_sdk.protocol.v2.datatypes import String, Bitmap, Enum

    # Test String immutability
    string_type = String(length=8)
    with pytest.raises(dataclasses.FrozenInstanceError):
        string_type.length = 16

    # Test Bitmap immutability
    bitmap_type = Bitmap(bits=16)
    with pytest.raises(dataclasses.FrozenInstanceError):
        bitmap_type.bits = 32

    # Test Enum immutability
    enum_type = Enum(mapping={0: "OFF", 1: "ON"})
    with pytest.raises(dataclasses.FrozenInstanceError):
        enum_type.mapping = {0: "DISABLED", 1: "ENABLED"}

    # Test that Enum mapping is truly immutable (MappingProxyType)
    with pytest.raises(TypeError):  # MappingProxyType raises TypeError on mutation
        enum_type.mapping[2] = "AUTO"

    # Verify in a registered schema context
    schema = BlockSchema(
        block_id=9011,
        name="TEST_DATATYPE_IMMUTABLE",
        description="Test DataType immutability",
        min_length=10,
        fields=[
            Field(name="device_model", offset=0, type=string_type),
            Field(name="status", offset=8, type=bitmap_type),
        ]
    )

    registry.register(schema)

    # Retrieved schema should have the same immutable types
    retrieved = registry.get(9011)
    assert retrieved.fields[0].type.length == 8
    assert retrieved.fields[1].type.bits == 16

    # Attempt to modify types after registration - should still fail
    with pytest.raises(dataclasses.FrozenInstanceError):
        retrieved.fields[0].type.length = 999
