"""Unit tests for Schema Registry."""

import dataclasses
from concurrent.futures import ThreadPoolExecutor

import pytest
from power_sdk.plugins.bluetti.v2.protocol.datatypes import UInt16
from power_sdk.plugins.bluetti.v2.protocol.schema import BlockSchema, Field
from power_sdk.plugins.bluetti.v2.schemas import SchemaRegistry, registry


@pytest.fixture
def test_registry():
    """Create a fresh instance-scoped registry for testing.

    Returns:
        SchemaRegistry instance for isolated testing
    """
    return SchemaRegistry()


# Backward compatibility alias - tests using clean_registry get instance registry
@pytest.fixture
def clean_registry(test_registry):
    """Backward compatibility fixture - returns instance registry.

    This allows existing tests to work without changes while encouraging
    migration to instance-scoped registries.
    """
    return test_registry


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
        ],
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
        ],
    )


def test_register_schema(clean_registry, test_schema_1):
    """Test registering a single schema."""
    clean_registry.register(test_schema_1)

    # Should be retrievable
    retrieved = clean_registry.get(9001)
    assert retrieved is not None
    assert retrieved.name == "TEST_BLOCK_1"


def test_register_duplicate_schema(clean_registry, test_schema_1):
    """Test registering the same schema twice."""
    clean_registry.register(test_schema_1)

    # Second registration should be silently skipped
    clean_registry.register(test_schema_1)

    # Should still have only one
    assert len(clean_registry.list_blocks()) == 1


def test_register_conflicting_schema(clean_registry, test_schema_1):
    """Test registering different schema with same block_id (different name)."""
    clean_registry.register(test_schema_1)

    # Different schema with same block_id but different name
    conflicting = BlockSchema(
        block_id=9001,
        name="DIFFERENT_NAME",
        description="Different",
        min_length=4,
        fields=[],
    )

    # Should raise error
    with pytest.raises(ValueError, match="already registered"):
        clean_registry.register(conflicting)


def test_register_conflicting_structure(clean_registry, test_schema_1):
    """Test registering schema with same block_id and name but different fields."""
    clean_registry.register(test_schema_1)

    # Same block_id and name, but different fields
    conflicting = BlockSchema(
        block_id=9001,
        name="TEST_BLOCK_1",  # Same name
        description="Different structure",
        min_length=4,
        fields=[
            Field(name="different_field", offset=0, type=UInt16()),
        ],
    )

    # Should raise error about structure conflict
    with pytest.raises(ValueError, match="structure conflict"):
        clean_registry.register(conflicting)


def test_register_conflicting_offset(clean_registry):
    """Test detecting offset changes in field."""
    schema1 = BlockSchema(
        block_id=9003,
        name="TEST",
        description="Test",
        min_length=4,
        fields=[
            Field(name="field1", offset=0, type=UInt16()),
        ],
    )
    clean_registry.register(schema1)

    # Same field name, different offset
    schema2 = BlockSchema(
        block_id=9003,
        name="TEST",
        description="Test",
        min_length=4,
        fields=[
            Field(name="field1", offset=2, type=UInt16()),  # Changed offset
        ],
    )

    with pytest.raises(ValueError, match="offset changed"):
        clean_registry.register(schema2)


def test_register_conflicting_type(clean_registry):
    """Test detecting type changes in field."""
    from power_sdk.plugins.bluetti.v2.protocol.datatypes import UInt8

    schema1 = BlockSchema(
        block_id=9004,
        name="TEST",
        description="Test",
        min_length=4,
        fields=[
            Field(name="field1", offset=0, type=UInt16()),
        ],
    )
    clean_registry.register(schema1)

    # Same field name, different type
    schema2 = BlockSchema(
        block_id=9004,
        name="TEST",
        description="Test",
        min_length=4,
        fields=[
            Field(name="field1", offset=0, type=UInt8()),  # Changed type
        ],
    )

    with pytest.raises(ValueError, match="type changed"):
        clean_registry.register(schema2)


def test_register_conflicting_required(clean_registry):
    """Test detecting required flag changes."""
    schema1 = BlockSchema(
        block_id=9005,
        name="TEST",
        description="Test",
        min_length=4,
        fields=[
            Field(name="field1", offset=0, type=UInt16(), required=True),
        ],
    )
    clean_registry.register(schema1)

    # Same field, different required flag
    schema2 = BlockSchema(
        block_id=9005,
        name="TEST",
        description="Test",
        min_length=4,
        fields=[
            Field(name="field1", offset=0, type=UInt16(), required=False),
        ],
    )

    with pytest.raises(ValueError, match="required changed"):
        clean_registry.register(schema2)


def test_register_conflicting_transform(clean_registry):
    """Test detecting transform changes."""
    schema1 = BlockSchema(
        block_id=9006,
        name="TEST",
        description="Test",
        min_length=4,
        fields=[
            Field(name="field1", offset=0, type=UInt16(), transform=["scale:0.1"]),
        ],
    )
    clean_registry.register(schema1)

    # Same field, different transform
    schema2 = BlockSchema(
        block_id=9006,
        name="TEST",
        description="Test",
        min_length=4,
        fields=[
            Field(name="field1", offset=0, type=UInt16(), transform=["scale:0.01"]),
        ],
    )

    with pytest.raises(ValueError, match="transform changed"):
        clean_registry.register(schema2)


def test_register_conflicting_string_length(clean_registry):
    """Test detecting String type parameter changes (length)."""
    from power_sdk.plugins.bluetti.v2.protocol.datatypes import String

    schema1 = BlockSchema(
        block_id=9007,
        name="TEST",
        description="Test",
        min_length=10,
        fields=[
            Field(name="device_model", offset=0, type=String(length=8)),
        ],
    )
    clean_registry.register(schema1)

    # Same field name and type class, but different length
    schema2 = BlockSchema(
        block_id=9007,
        name="TEST",
        description="Test",
        min_length=14,
        fields=[
            Field(name="device_model", offset=0, type=String(length=12)),
        ],
    )

    # Should detect String(length=8) vs String(length=12) as different
    with pytest.raises(ValueError, match=r"type changed.*String"):
        clean_registry.register(schema2)


def test_register_conflicting_bitmap_bits(clean_registry):
    """Test detecting Bitmap type parameter changes (bits)."""
    from power_sdk.plugins.bluetti.v2.protocol.datatypes import Bitmap

    schema1 = BlockSchema(
        block_id=9008,
        name="TEST",
        description="Test",
        min_length=4,
        fields=[
            Field(name="status", offset=0, type=Bitmap(bits=16)),
        ],
    )
    clean_registry.register(schema1)

    # Same field name and type class, but different bits
    schema2 = BlockSchema(
        block_id=9008,
        name="TEST",
        description="Test",
        min_length=4,
        fields=[
            Field(name="status", offset=0, type=Bitmap(bits=32)),
        ],
    )

    # Should detect Bitmap(bits=16) vs Bitmap(bits=32) as different
    with pytest.raises(ValueError, match=r"type changed.*Bitmap"):
        clean_registry.register(schema2)


def test_register_conflicting_enum_mapping(clean_registry):
    """Test detecting Enum type mapping changes."""
    from power_sdk.plugins.bluetti.v2.protocol.datatypes import Enum

    # Two enums with same number of values but different mappings
    schema1 = BlockSchema(
        block_id=9009,
        name="TEST",
        description="Test",
        min_length=4,
        fields=[
            Field(
                name="mode",
                offset=0,
                type=Enum(
                    mapping={
                        0: "OFF",
                        1: "ON",
                        2: "AUTO",
                    }
                ),
            ),
        ],
    )
    clean_registry.register(schema1)

    # Same number of values (3), but different mapping
    schema2 = BlockSchema(
        block_id=9009,
        name="TEST",
        description="Test",
        min_length=4,
        fields=[
            Field(
                name="mode",
                offset=0,
                type=Enum(
                    mapping={
                        0: "DISABLED",  # Different name for 0
                        1: "ENABLED",  # Different name for 1
                        2: "STANDBY",  # Different name for 2
                    }
                ),
            ),
        ],
    )

    # Should detect different mapping content, not just size
    with pytest.raises(ValueError, match=r"type changed.*Enum"):
        clean_registry.register(schema2)


def test_register_many(clean_registry, test_schema_1, test_schema_2):
    """Test registering multiple schemas at once."""
    clean_registry.register_many([test_schema_1, test_schema_2])

    assert len(clean_registry.list_blocks()) == 2
    assert clean_registry.get(9001) is not None
    assert clean_registry.get(9002) is not None


def test_get_nonexistent_schema(clean_registry):
    """Test getting a schema that doesn't exist."""
    result = clean_registry.get(99999)
    assert result is None


def test_list_blocks(clean_registry, test_schema_1, test_schema_2):
    """Test listing registered block IDs."""
    clean_registry.register_many([test_schema_1, test_schema_2])

    blocks = clean_registry.list_blocks()
    assert blocks == [9001, 9002]  # Should be sorted


def test_resolve_blocks_strict(clean_registry, test_schema_1, test_schema_2):
    """Test resolving schemas in strict mode."""
    clean_registry.register_many([test_schema_1, test_schema_2])

    # All schemas available
    resolved = clean_registry.resolve_blocks([9001, 9002], strict=True)
    assert len(resolved) == 2
    assert 9001 in resolved
    assert 9002 in resolved

    # Missing schema should raise error
    with pytest.raises(ValueError, match="Missing schemas"):
        clean_registry.resolve_blocks([9001, 99999], strict=True)


def test_resolve_blocks_lenient(clean_registry, test_schema_1):
    """Test resolving schemas in lenient mode."""
    clean_registry.register(test_schema_1)

    # Should return only found schemas, skip missing
    resolved = clean_registry.resolve_blocks([9001, 99999], strict=False)
    assert len(resolved) == 1
    assert 9001 in resolved
    assert 99999 not in resolved


def test_resolve_empty_list(clean_registry):
    """Test resolving empty block list."""
    resolved = clean_registry.resolve_blocks([], strict=True)
    assert resolved == {}


def test_clear(clean_registry):
    """Test clearing the registry (testing only)."""
    schema = BlockSchema(
        block_id=9001, name="TEST", description="Test", min_length=4, fields=[]
    )
    clean_registry.register(schema)
    assert len(clean_registry.list_blocks()) == 1

    # Clear instance registry (testing method)
    clean_registry.clear()
    assert len(clean_registry.list_blocks()) == 0
    assert clean_registry.get(9001) is None


def test_lazy_registration():
    """Test lazy built-in catalog population.

    Built-in catalog should NOT be populated on import,
    only when new_registry_with_builtins() is called.
    """
    # Clear built-in catalog and reset population flag
    registry._clear_builtin_catalog_for_testing()

    import power_sdk.plugins.bluetti.v2.schemas as _schemas

    _schemas._reset_builtin_catalog_for_testing()

    # After clearing, built-in catalog should be empty
    blocks = registry.list_blocks()
    assert len(blocks) == 0

    # Call new_registry_with_builtins to trigger catalog population
    instance_registry = _schemas.new_registry_with_builtins()

    # Now built-in catalog should be populated
    blocks = _schemas.list_blocks()
    assert 100 in blocks  # BLOCK_100_SCHEMA
    assert 1100 in blocks  # BLOCK_1100_SCHEMA
    assert 1300 in blocks  # BLOCK_1300_SCHEMA
    assert 1400 in blocks  # BLOCK_1400_SCHEMA
    assert 1500 in blocks  # BLOCK_1500_SCHEMA
    assert 6000 in blocks  # BLOCK_6000_SCHEMA
    assert 6100 in blocks  # BLOCK_6100_SCHEMA

    # Verify they're retrievable from built-in catalog
    assert _schemas.get(100).name == "APP_HOME_DATA"
    assert _schemas.get(1300).name == "INV_GRID_INFO"
    assert _schemas.get(6000).name == "PACK_MAIN_INFO"

    # Verify instance registry also has them
    assert instance_registry.get(100).name == "APP_HOME_DATA"
    assert instance_registry.get(1300).name == "INV_GRID_INFO"
    assert instance_registry.get(6000).name == "PACK_MAIN_INFO"

    # Calling new_registry_with_builtins() again should be idempotent
    instance_registry2 = _schemas.new_registry_with_builtins()
    # Wave A: 100, 1100, 1300, 1400, 1500, 6000, 6100 (7 blocks)
    # Wave B: 2000, 2200, 2400, 7000, 11000, 12002, 19000 (7 blocks)
    # Wave C: 720, 1700, 3500, 3600, 6300, 12161 (6 blocks)
    # Wave D Batch 1: 19100, 19200, 19300, 19305, 40127 (5 blocks)
    # Wave D Batch 2: 15750, 17000, 19365, 19425, 19485 (5 blocks)
    # Wave D Batch 3: 14500, 14700, 15500, 15600, 17100 (5 blocks)
    # Wave D Batch 4: 15700, 17400, 18000, 18300, 26001 (5 blocks)
    # Wave D Batch 5: 18400, 18500, 18600, 29770, 29772 (5 blocks)
    assert len(instance_registry2.list_blocks()) >= 45  # All built-in schemas


def test_new_registry_with_builtins_thread_safe_population():
    """Concurrent bootstrap calls should not double-register built-ins."""
    registry._clear_builtin_catalog_for_testing()
    import power_sdk.plugins.bluetti.v2.schemas as _schemas

    _schemas._reset_builtin_catalog_for_testing()

    def _create_count() -> int:
        return len(_schemas.new_registry_with_builtins().list_blocks())

    with ThreadPoolExecutor(max_workers=8) as ex:
        results = list(ex.map(lambda _i: _create_count(), range(16)))

    assert all(n >= 45 for n in results)


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
        ],
    )

    # Register schema
    clean_registry.register(schema)

    # Attempt to modify BlockSchema - should raise FrozenInstanceError
    with pytest.raises(dataclasses.FrozenInstanceError):
        schema.name = "MODIFIED"

    # Attempt to modify Field - should raise FrozenInstanceError
    field = schema.fields[0]
    with pytest.raises(dataclasses.FrozenInstanceError):
        field.offset = 999

    # Verify schema in registry is still intact
    retrieved = clean_registry.get(9010)
    assert retrieved.name == "TEST_IMMUTABLE"
    assert retrieved.fields[0].offset == 0


def test_datatype_immutability(clean_registry):
    """Test that DataType objects (String, Bitmap, Enum) are immutable.

    This ensures wire-format safety even if types are modified after registration.
    """
    from power_sdk.plugins.bluetti.v2.protocol.datatypes import Bitmap, Enum, String

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
        ],
    )

    clean_registry.register(schema)

    # Retrieved schema should have the same immutable types
    retrieved = clean_registry.get(9011)
    assert retrieved.fields[0].type.length == 8
    assert retrieved.fields[1].type.bits == 16

    # Attempt to modify types after registration - should still fail
    with pytest.raises(dataclasses.FrozenInstanceError):
        retrieved.fields[0].type.length = 999


def test_enum_base_type_immutability():
    """Test that Enum validates base_type is immutable (strict contract).

    This prevents architectural bypass via mutable custom DataType subclasses.
    Enforces strict whitelist: only SDK built-in types or frozen dataclasses.
    """
    from dataclasses import dataclass
    from typing import Any

    from power_sdk.plugins.bluetti.v2.protocol.datatypes import (
        DataType,
        Enum,
        Int8,
        UInt8,
        UInt16,
    )

    # 1. SDK built-in immutable types should work
    Enum(mapping={0: "OFF"}, base_type=UInt8())  # OK - whitelist
    Enum(mapping={0: "OFF"}, base_type=UInt16())  # OK - whitelist
    Enum(mapping={0: "OFF"}, base_type=Int8())  # OK - whitelist

    # 2. Frozen custom dataclass should work
    @dataclass(frozen=True)
    class FrozenCustomType(DataType):
        def parse(self, data: bytes, offset: int) -> Any:
            return 0

        def size(self) -> int:
            return 1

        def encode(self, value: Any) -> bytes:
            return b"\x00"

    Enum(mapping={0: "X"}, base_type=FrozenCustomType())  # OK - frozen dataclass

    # 3. Mutable dataclass should be rejected
    @dataclass  # NOT frozen
    class MutableDataclassType(DataType):
        value: int = 0

        def parse(self, data: bytes, offset: int) -> Any:
            return 0

        def size(self) -> int:
            return 1

        def encode(self, value: Any) -> bytes:
            return b"\x00"

    with pytest.raises(ValueError, match=r"must be immutable.*MutableDataclassType"):
        Enum(mapping={0: "X"}, base_type=MutableDataclassType())

    # 4. Non-dataclass mutable class should be rejected (edge case)
    class MutableNonDataclass(DataType):
        def __init__(self):
            self.value = 0  # mutable state

        def parse(self, data: bytes, offset: int) -> Any:
            return 0

        def size(self) -> int:
            return 1

        def encode(self, value: Any) -> bytes:
            return b"\x00"

    with pytest.raises(ValueError, match=r"must be immutable.*MutableNonDataclass"):
        Enum(mapping={0: "X"}, base_type=MutableNonDataclass())


def test_enum_defensive_copy(clean_registry):
    """Test that Enum makes defensive copy of mapping to prevent external mutation.

    This ensures that mutating the original dict after Enum creation does not
    affect the Enum's internal mapping (defensive copy protection).
    """
    from types import MappingProxyType

    from power_sdk.plugins.bluetti.v2.protocol.datatypes import Enum

    # Test 1: Defensive copy from regular dict
    original_mapping = {0: "OFF", 1: "ON", 2: "AUTO"}
    enum_type = Enum(mapping=original_mapping)

    # Verify initial state
    assert enum_type.mapping[0] == "OFF"
    assert enum_type.mapping[1] == "ON"
    assert enum_type.mapping[2] == "AUTO"

    # Mutate the ORIGINAL dict (external reference)
    original_mapping[0] = "DISABLED"
    original_mapping[3] = "MANUAL"
    del original_mapping[2]

    # Enum's mapping should be UNCHANGED (defensive copy)
    assert enum_type.mapping[0] == "OFF"  # not "DISABLED"
    assert enum_type.mapping[1] == "ON"
    assert enum_type.mapping[2] == "AUTO"  # not deleted
    assert 3 not in enum_type.mapping  # "MANUAL" not added

    # Test 2: Defensive copy from MappingProxyType wrapping mutable dict
    # This is the edge case: if someone passes MappingProxyType(mutable_dict),
    # we still need to make a defensive copy
    external_dict = {0: "ENABLED", 1: "DISABLED"}
    proxy = MappingProxyType(external_dict)
    enum_from_proxy = Enum(mapping=proxy)

    # Verify initial state
    assert enum_from_proxy.mapping[0] == "ENABLED"
    assert enum_from_proxy.mapping[1] == "DISABLED"

    # Mutate the UNDERLYING dict (external reference)
    external_dict[0] = "HACKED"
    external_dict[2] = "INJECTED"

    # Enum's mapping should be UNCHANGED (defensive copy even from MappingProxyType)
    assert enum_from_proxy.mapping[0] == "ENABLED"  # not "HACKED"
    assert enum_from_proxy.mapping[1] == "DISABLED"
    assert 2 not in enum_from_proxy.mapping  # "INJECTED" not added

    # Test in registered schema context
    schema = BlockSchema(
        block_id=9012,
        name="TEST_ENUM_DEFENSIVE_COPY",
        description="Test Enum defensive copy",
        min_length=4,
        fields=[
            Field(name="mode", offset=0, type=enum_type),
        ],
    )

    clean_registry.register(schema)

    # Retrieved Enum should still have original values
    retrieved_enum = clean_registry.get(9012).fields[0].type
    assert retrieved_enum.mapping[0] == "OFF"
    assert retrieved_enum.mapping[2] == "AUTO"
    assert 3 not in retrieved_enum.mapping


# === Instance-Scoped Registry Isolation Tests ===


def test_new_registry_with_builtins_isolated_instances():
    """Test that new_registry_with_builtins() creates isolated instances.

    Each registry instance should be independent - custom schemas registered
    in one instance should not appear in other instances.
    """
    from power_sdk.plugins.bluetti.v2.protocol.datatypes import UInt16
    from power_sdk.plugins.bluetti.v2.protocol.schema import BlockSchema, Field
    from power_sdk.plugins.bluetti.v2.schemas import new_registry_with_builtins

    # Create two independent registry instances
    r1 = new_registry_with_builtins()
    r2 = new_registry_with_builtins()

    # Verify they are different objects
    assert r1 is not r2

    # Verify both have built-in schemas
    assert r1.get(100) is not None  # BLOCK_100_SCHEMA
    assert r1.get(1300) is not None  # BLOCK_1300_SCHEMA
    assert r1.get(6000) is not None  # BLOCK_6000_SCHEMA

    assert r2.get(100) is not None
    assert r2.get(1300) is not None
    assert r2.get(6000) is not None

    # Register a custom schema ONLY in r1
    custom_schema = BlockSchema(
        block_id=9999,
        name="CUSTOM_R1_ONLY",
        description="Custom schema for r1 only",
        min_length=4,
        fields=[Field(name="value", offset=0, type=UInt16())],
    )
    r1.register(custom_schema)

    # Verify custom schema is in r1 but NOT in r2 (isolation)
    assert r1.get(9999) is not None
    assert r1.get(9999).name == "CUSTOM_R1_ONLY"
    assert r2.get(9999) is None  # Not visible in r2

    # Register a different custom schema in r2
    custom_schema_r2 = BlockSchema(
        block_id=8888,
        name="CUSTOM_R2_ONLY",
        description="Custom schema for r2 only",
        min_length=4,
        fields=[Field(name="data", offset=0, type=UInt16())],
    )
    r2.register(custom_schema_r2)

    # Verify each registry only sees its own custom schema
    assert r1.get(8888) is None  # r2's schema not visible in r1
    assert r2.get(9999) is None  # r1's schema not visible in r2


def test_builtin_schemas_available_in_new_registry():
    """Test that factory-created registry contains all built-in schemas.

    new_registry_with_builtins() should provide access to all standard
    block schemas (100, 1300, 6000).
    """
    from power_sdk.plugins.bluetti.v2.schemas import new_registry_with_builtins

    registry = new_registry_with_builtins()

    # Verify built-in schemas are present
    block_100 = registry.get(100)
    assert block_100 is not None
    assert block_100.name == "APP_HOME_DATA"

    block_1300 = registry.get(1300)
    assert block_1300 is not None
    assert block_1300.name == "INV_GRID_INFO"

    block_6000 = registry.get(6000)
    assert block_6000 is not None
    assert block_6000.name == "PACK_MAIN_INFO"

    # Verify at least these built-ins are in the list
    registered_blocks = registry.list_blocks()
    assert 100 in registered_blocks
    assert 1300 in registered_blocks
    assert 6000 in registered_blocks


def test_no_global_mutation_api_exposed():
    """Test that public API does not expose unsafe global mutators.

    The power_sdk.schemas module should not export register(), clear(),
    or other mutation functions that could affect global state.
    """
    import power_sdk.plugins.bluetti.v2.schemas as schemas

    # Safe read-only functions should be available
    assert hasattr(schemas, "get")
    assert hasattr(schemas, "list_blocks")
    assert hasattr(schemas, "resolve_blocks")
    assert hasattr(schemas, "new_registry_with_builtins")

    # SchemaRegistry class should be available (for custom instances)
    assert hasattr(schemas, "SchemaRegistry")

    # Unsafe global mutators should NOT be in public API
    assert "register" not in schemas.__all__
    assert "register_many" not in schemas.__all__
    assert "clear" not in schemas.__all__

    # Even if accessible (for backwards compat), not in __all__
    # This prevents them from being imported via "from schemas import *"


def test_register_many_handles_name_conflicts(clean_registry):
    """Test that register_many detects and rejects name conflicts atomically.

    When attempting batch registration with a conflicting schema name,
    the operation should fail atomically without partial registration.
    """
    # Register first schema
    schema_a = BlockSchema(
        block_id=100,
        name="SCHEMA_A",
        description="Original schema",
        min_length=4,
        fields=[Field(name="field1", offset=0, type=UInt16())],
    )
    clean_registry.register(schema_a)

    # Attempt to register conflicting schema (same block_id, different name)
    schema_b = BlockSchema(
        block_id=100,
        name="SCHEMA_B",  # Conflict: different name for same block
        description="Conflicting schema",
        min_length=4,
        fields=[Field(name="field1", offset=0, type=UInt16())],
    )

    # Batch registration should fail on name conflict
    with pytest.raises(ValueError, match="already registered as 'SCHEMA_A'"):
        clean_registry.register_many([schema_b])

    # Verify registry state unchanged (atomic failure)
    assert clean_registry.get(100).name == "SCHEMA_A"
    assert len(clean_registry.list_blocks()) == 1


def test_check_field_conflicts_with_fieldgroup_no_attribute_error(clean_registry):
    """Regression: _check_field_conflicts must not raise AttributeError on FieldGroup.

    FieldGroup has no .type or .transform attributes — the conflict checker must
    detect this and use FieldGroup-specific comparison logic instead.
    """
    from power_sdk.plugins.bluetti.v2.protocol.schema import FieldGroup

    # Build schema containing a FieldGroup
    schema_v1 = BlockSchema(
        block_id=9100,
        name="TEST_FIELDGROUP",
        description="Schema with FieldGroup",
        min_length=4,
        fields=[
            FieldGroup(
                name="nested_group",
                fields=[
                    Field(name="sub_a", offset=0, type=UInt16()),
                    Field(name="sub_b", offset=2, type=UInt16()),
                ],
                required=False,
            ),
        ],
    )
    clean_registry.register(schema_v1)

    # Re-registering the identical schema must not raise AttributeError
    schema_v1_dup = BlockSchema(
        block_id=9100,
        name="TEST_FIELDGROUP",
        description="Schema with FieldGroup (duplicate)",
        min_length=4,
        fields=[
            FieldGroup(
                name="nested_group",
                fields=[
                    Field(name="sub_a", offset=0, type=UInt16()),
                    Field(name="sub_b", offset=2, type=UInt16()),
                ],
                required=False,
            ),
        ],
    )
    # Must not raise — identical structure is accepted as idempotent
    clean_registry.register(schema_v1_dup)
    assert clean_registry.get(9100) is not None


def test_check_field_conflicts_fieldgroup_nested_name_change(clean_registry):
    """FieldGroup re-registration with changed nested field set is a conflict."""
    from power_sdk.plugins.bluetti.v2.protocol.schema import FieldGroup

    schema_v1 = BlockSchema(
        block_id=9101,
        name="TEST_FG_CONFLICT",
        description="Schema with FieldGroup",
        min_length=4,
        fields=[
            FieldGroup(
                name="grp",
                fields=[Field(name="x", offset=0, type=UInt16())],
                required=False,
            ),
        ],
    )
    clean_registry.register(schema_v1)

    schema_v2 = BlockSchema(
        block_id=9101,
        name="TEST_FG_CONFLICT",
        description="Changed nested fields",
        min_length=4,
        fields=[
            FieldGroup(
                name="grp",
                fields=[
                    Field(name="x", offset=0, type=UInt16()),
                    Field(name="y", offset=2, type=UInt16()),  # added sub-field
                ],
                required=False,
            ),
        ],
    )

    with pytest.raises(ValueError, match="nested field set changed"):
        clean_registry.register(schema_v2)


def test_check_field_conflicts_fieldgroup_vs_plain_field(clean_registry):
    """Replacing a FieldGroup with a plain Field (or vice versa) is a conflict."""
    from power_sdk.plugins.bluetti.v2.protocol.schema import FieldGroup

    schema_v1 = BlockSchema(
        block_id=9102,
        name="TEST_FG_KIND",
        description="Schema with FieldGroup",
        min_length=4,
        fields=[
            FieldGroup(
                name="entry",
                fields=[Field(name="sub", offset=0, type=UInt16())],
                required=False,
            ),
        ],
    )
    clean_registry.register(schema_v1)

    # Replace the FieldGroup with a plain Field of the same name
    schema_v2 = BlockSchema(
        block_id=9102,
        name="TEST_FG_KIND",
        description="Changed to plain Field",
        min_length=4,
        fields=[
            Field(name="entry", offset=0, type=UInt16()),
        ],
    )

    with pytest.raises(ValueError, match="field kind changed"):
        clean_registry.register(schema_v2)
