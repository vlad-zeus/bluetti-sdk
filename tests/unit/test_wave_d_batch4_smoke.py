"""Smoke tests for Wave D Batch 4 blocks - schema availability and basic parsing."""

from power_sdk.plugins.bluetti.v2.protocol.parser import V2Parser
from power_sdk.plugins.bluetti.v2.schemas import (
    BLOCK_15700_SCHEMA,
    BLOCK_17400_SCHEMA,
    BLOCK_18000_SCHEMA,
    BLOCK_18300_SCHEMA,
    BLOCK_26001_SCHEMA,
    new_registry_with_builtins,
)


def test_wave_d_batch4_schemas_available():
    """Verify all Wave D Batch 4 schemas are importable and have correct block IDs."""
    assert BLOCK_15700_SCHEMA.block_id == 15700
    assert BLOCK_15700_SCHEMA.name == "DC_HUB_INFO"

    assert BLOCK_17400_SCHEMA.block_id == 17400
    assert BLOCK_17400_SCHEMA.name == "ATS_EVENT_EXT"

    assert BLOCK_18000_SCHEMA.block_id == 18000
    assert BLOCK_18000_SCHEMA.name == "EPAD_INFO"

    assert BLOCK_18300_SCHEMA.block_id == 18300
    assert BLOCK_18300_SCHEMA.name == "EPAD_SETTINGS"

    assert BLOCK_26001_SCHEMA.block_id == 26001
    assert BLOCK_26001_SCHEMA.name == "TOU_TIME_INFO"


def test_wave_d_batch4_schemas_registered():
    """Verify Wave D Batch 4 schemas are auto-registered in new registries."""
    registry = new_registry_with_builtins()

    # Check all 5 blocks are registered
    assert registry.get(15700) == BLOCK_15700_SCHEMA
    assert registry.get(17400) == BLOCK_17400_SCHEMA
    assert registry.get(18000) == BLOCK_18000_SCHEMA
    assert registry.get(18300) == BLOCK_18300_SCHEMA
    assert registry.get(26001) == BLOCK_26001_SCHEMA

    # Verify total count
    # Wave A/B/C: 20 + Wave D Batches 1-5: 25 = 45
    all_blocks = registry.list_blocks()
    assert len(all_blocks) == 45


def test_wave_d_batch4_minimal_parseability():
    """Verify Wave D Batch 4 blocks can be parsed by V2Parser with minimal payloads."""
    parser = V2Parser()
    for schema in [
        BLOCK_15700_SCHEMA,
        BLOCK_17400_SCHEMA,
        BLOCK_18000_SCHEMA,
        BLOCK_18300_SCHEMA,
        BLOCK_26001_SCHEMA,
    ]:
        parser.register_schema(schema)

    for schema in [
        BLOCK_15700_SCHEMA,
        BLOCK_17400_SCHEMA,
        BLOCK_18000_SCHEMA,
        BLOCK_18300_SCHEMA,
        BLOCK_26001_SCHEMA,
    ]:
        payload = bytes([0] * schema.min_length)
        parsed = parser.parse_block(schema.block_id, payload, validate=True)
        assert parsed.block_id == schema.block_id
        assert parsed.name == schema.name

