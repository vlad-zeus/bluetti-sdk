"""Smoke tests for Wave D Batch 5 blocks - schema availability and basic parsing."""

from power_sdk.plugins.bluetti.v2.protocol.parser import V2Parser
from power_sdk.schemas import (
    BLOCK_18400_SCHEMA,
    BLOCK_18500_SCHEMA,
    BLOCK_18600_SCHEMA,
    BLOCK_29770_SCHEMA,
    BLOCK_29772_SCHEMA,
    new_registry_with_builtins,
)


def test_wave_d_batch5_schemas_available():
    """Verify all Wave D Batch 5 schemas are importable and have correct block IDs."""
    assert BLOCK_18400_SCHEMA.block_id == 18400
    assert BLOCK_18400_SCHEMA.name == "EPAD_LIQUID_POINT1"

    assert BLOCK_18500_SCHEMA.block_id == 18500
    assert BLOCK_18500_SCHEMA.name == "EPAD_LIQUID_POINT2"

    assert BLOCK_18600_SCHEMA.block_id == 18600
    assert BLOCK_18600_SCHEMA.name == "EPAD_LIQUID_POINT3"

    assert BLOCK_29770_SCHEMA.block_id == 29770
    assert BLOCK_29770_SCHEMA.name == "BOOT_UPGRADE_SUPPORT"

    assert BLOCK_29772_SCHEMA.block_id == 29772
    assert BLOCK_29772_SCHEMA.name == "BOOT_SOFTWARE_INFO"


def test_wave_d_batch5_schemas_registered():
    """Verify Wave D Batch 5 schemas are auto-registered in new registries."""
    registry = new_registry_with_builtins()

    # Check all 5 blocks are registered
    assert registry.get(18400) == BLOCK_18400_SCHEMA
    assert registry.get(18500) == BLOCK_18500_SCHEMA
    assert registry.get(18600) == BLOCK_18600_SCHEMA
    assert registry.get(29770) == BLOCK_29770_SCHEMA
    assert registry.get(29772) == BLOCK_29772_SCHEMA

    # Verify total count
    # (20 Wave A/B/C + 20 Wave D Batches 1-4 + 5 Wave D Batch 5 = 45)
    all_blocks = registry.list_blocks()
    assert len(all_blocks) == 45


def test_wave_d_batch5_minimal_parseability():
    """Verify Wave D Batch 5 blocks can be parsed by V2Parser with minimal payloads."""
    parser = V2Parser()
    for schema in [
        BLOCK_18400_SCHEMA,
        BLOCK_18500_SCHEMA,
        BLOCK_18600_SCHEMA,
        BLOCK_29770_SCHEMA,
        BLOCK_29772_SCHEMA,
    ]:
        parser.register_schema(schema)

    for schema in [
        BLOCK_18400_SCHEMA,
        BLOCK_18500_SCHEMA,
        BLOCK_18600_SCHEMA,
        BLOCK_29770_SCHEMA,
        BLOCK_29772_SCHEMA,
    ]:
        payload = bytes([0] * schema.min_length)
        parsed = parser.parse_block(schema.block_id, payload, validate=True)
        assert parsed.block_id == schema.block_id
        assert parsed.name == schema.name

