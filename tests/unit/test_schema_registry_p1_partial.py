"""Tests for P1 edge case: partial registration atomicity."""

import pytest
from power_sdk.plugins.bluetti.v2.protocol.datatypes import UInt16, UInt32
from power_sdk.plugins.bluetti.v2.protocol.schema import BlockSchema, Field
from power_sdk.plugins.bluetti.v2.schemas import SchemaRegistry


def test_register_many_atomic_rollback_on_conflict():
    """Test that register_many is atomic - no partial registration on conflict.

    Scenario:
    - Batch of 3 schemas: [valid1, conflicting2, valid3]
    - Schema2 conflicts with already-registered schema
    - Expected: ValueError raised, NO schemas from batch registered
    - Bug: First schema gets registered before conflict detected
    """
    registry = SchemaRegistry()

    # Pre-register a schema that will conflict with schema2
    existing_schema = BlockSchema(
        block_id=9002,
        name="EXISTING_BLOCK",
        description="Already registered",
        min_length=4,
        fields=[Field(name="old_field", offset=0, type=UInt16())],
    )
    registry.register(existing_schema)

    # Create batch of 3 schemas where second one conflicts
    schema1 = BlockSchema(
        block_id=9001,
        name="BATCH_SCHEMA_1",
        description="First in batch",
        min_length=4,
        fields=[Field(name="field1", offset=0, type=UInt16())],
    )

    # This conflicts with existing_schema (same block_id, different structure)
    schema2_conflicting = BlockSchema(
        block_id=9002,
        name="EXISTING_BLOCK",  # Same name
        description="Conflicting structure",
        min_length=8,  # Different structure
        fields=[
            Field(name="new_field", offset=0, type=UInt32()),  # Different field
        ],
    )

    schema3 = BlockSchema(
        block_id=9003,
        name="BATCH_SCHEMA_3",
        description="Third in batch",
        min_length=4,
        fields=[Field(name="field3", offset=0, type=UInt16())],
    )

    # Capture initial state
    initial_blocks = set(registry.list_blocks())
    assert 9002 in initial_blocks  # Existing schema present
    assert 9001 not in initial_blocks
    assert 9003 not in initial_blocks

    # Attempt batch registration - should fail on schema2
    with pytest.raises(ValueError, match="structure conflict"):
        registry.register_many([schema1, schema2_conflicting, schema3])

    # Verify ATOMICITY: registry state unchanged (no partial registration)
    final_blocks = set(registry.list_blocks())

    # BUG: Without atomicity, schema1 would be registered before conflict
    assert final_blocks == initial_blocks, (
        "Registry state changed despite batch conflict! "
        f"Initial: {initial_blocks}, Final: {final_blocks}"
    )

    # Specifically verify schema1 was NOT registered
    assert registry.get(9001) is None, (
        "Schema1 should not be registered after batch failure"
    )
    assert registry.get(9003) is None, (
        "Schema3 should not be registered after batch failure"
    )

    # Existing schema should remain unchanged
    retrieved = registry.get(9002)
    assert retrieved is not None
    assert retrieved.fields[0].name == "old_field"  # Original field preserved


def test_register_many_idempotent_with_duplicates():
    """Test that register_many is idempotent when batch contains duplicates.

    Scenario:
    - Batch contains same schema multiple times
    - Expected: No error, schema registered once
    """
    registry = SchemaRegistry()

    schema = BlockSchema(
        block_id=9001,
        name="DUPLICATE_TEST",
        description="Test duplicate handling",
        min_length=4,
        fields=[Field(name="value", offset=0, type=UInt16())],
    )

    # Register same schema 3 times in one batch
    registry.register_many([schema, schema, schema])

    # Should succeed and be registered exactly once
    assert 9001 in registry.list_blocks()
    assert registry.get(9001).name == "DUPLICATE_TEST"


def test_register_many_success_after_failed_batch():
    """Test that registry remains usable after a failed batch registration.

    Scenario:
    - Batch1 fails due to conflict
    - Batch2 with valid schemas should succeed
    - Expected: Batch2 schemas registered successfully
    """
    registry = SchemaRegistry()

    # Pre-register conflicting schema
    existing = BlockSchema(
        block_id=9002,
        name="EXISTING",
        description="Pre-existing",
        min_length=4,
        fields=[Field(name="field", offset=0, type=UInt16())],
    )
    registry.register(existing)

    # Batch1: Contains conflict
    bad_batch = [
        BlockSchema(
            block_id=9001,
            name="GOOD1",
            description="Would be valid",
            min_length=4,
            fields=[Field(name="f1", offset=0, type=UInt16())],
        ),
        BlockSchema(
            block_id=9002,
            name="EXISTING",
            description="Conflicts",
            min_length=8,
            fields=[Field(name="different", offset=0, type=UInt32())],
        ),
    ]

    with pytest.raises(ValueError):
        registry.register_many(bad_batch)

    # Verify first batch did NOT register anything
    assert registry.get(9001) is None

    # Batch2: All valid schemas
    good_batch = [
        BlockSchema(
            block_id=9001,
            name="GOOD1",
            description="Valid schema 1",
            min_length=4,
            fields=[Field(name="f1", offset=0, type=UInt16())],
        ),
        BlockSchema(
            block_id=9003,
            name="GOOD3",
            description="Valid schema 3",
            min_length=4,
            fields=[Field(name="f3", offset=0, type=UInt16())],
        ),
    ]

    # Should succeed
    registry.register_many(good_batch)

    # Verify batch2 schemas registered
    assert registry.get(9001) is not None
    assert registry.get(9001).name == "GOOD1"
    assert registry.get(9003) is not None
    assert registry.get(9003).name == "GOOD3"

    # Original schema should remain unchanged
    assert registry.get(9002).fields[0].name == "field"
