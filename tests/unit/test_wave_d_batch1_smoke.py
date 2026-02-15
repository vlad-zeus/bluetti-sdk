"""Smoke tests for Wave D Batch 1 blocks - schema availability and basic parsing."""

from bluetti_sdk.protocol.v2.parser import V2Parser
from bluetti_sdk.schemas import (
    BLOCK_19100_SCHEMA,
    BLOCK_19200_SCHEMA,
    BLOCK_19300_SCHEMA,
    BLOCK_19305_SCHEMA,
    BLOCK_40127_SCHEMA,
    new_registry_with_builtins,
)


def test_wave_d_batch1_schemas_available():
    """Verify all Wave D Batch 1 schemas are importable and have correct block IDs."""
    assert BLOCK_19100_SCHEMA.block_id == 19100
    assert BLOCK_19100_SCHEMA.name == "COMM_DELAY_SETTINGS"

    assert BLOCK_19200_SCHEMA.block_id == 19200
    assert BLOCK_19200_SCHEMA.name == "SCHEDULED_BACKUP"

    assert BLOCK_19300_SCHEMA.block_id == 19300
    assert BLOCK_19300_SCHEMA.name == "TIMER_SETTINGS"

    assert BLOCK_19305_SCHEMA.block_id == 19305
    assert BLOCK_19305_SCHEMA.name == "TIMER_TASK_LIST"

    assert BLOCK_40127_SCHEMA.block_id == 40127
    assert BLOCK_40127_SCHEMA.name == "HOME_STORAGE_SETTINGS"


def test_wave_d_batch1_schemas_registered():
    """Verify Wave D Batch 1 schemas are auto-registered in new registries."""
    registry = new_registry_with_builtins()

    # Check all 5 blocks are registered
    assert registry.get(19100) == BLOCK_19100_SCHEMA
    assert registry.get(19200) == BLOCK_19200_SCHEMA
    assert registry.get(19300) == BLOCK_19300_SCHEMA
    assert registry.get(19305) == BLOCK_19305_SCHEMA
    assert registry.get(40127) == BLOCK_40127_SCHEMA

    # Verify total count (20 Wave A/B/C + 5 Wave D Batch 1 = 25)
    all_blocks = registry.list_blocks()
    assert len(all_blocks) == 25


def test_wave_d_batch1_minimal_parseability():
    """Verify Wave D Batch 1 blocks can be parsed by V2Parser with minimal payloads."""
    parser = V2Parser()
    for schema in [
        BLOCK_19100_SCHEMA,
        BLOCK_19200_SCHEMA,
        BLOCK_19300_SCHEMA,
        BLOCK_19305_SCHEMA,
        BLOCK_40127_SCHEMA,
    ]:
        parser.register_schema(schema)

    for schema in [
        BLOCK_19100_SCHEMA,
        BLOCK_19200_SCHEMA,
        BLOCK_19300_SCHEMA,
        BLOCK_19305_SCHEMA,
        BLOCK_40127_SCHEMA,
    ]:
        payload = bytes([0] * schema.min_length)
        parsed = parser.parse_block(schema.block_id, payload, validate=True)
        assert parsed.block_id == schema.block_id
        assert parsed.name == schema.name
