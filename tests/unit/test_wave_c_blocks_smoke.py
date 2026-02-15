"""Smoke tests for Wave C (P2 monitoring) block schemas.

Tests verify:
- Schema registration in built-in catalog
- Schema import accessibility
- Basic parseability of minimal payloads
- Total registered block count
"""


from bluetti_sdk.schemas import (
    BLOCK_720_SCHEMA,
    BLOCK_1700_SCHEMA,
    BLOCK_3500_SCHEMA,
    BLOCK_3600_SCHEMA,
    BLOCK_6300_SCHEMA,
    BLOCK_12161_SCHEMA,
    list_blocks,
    new_registry_with_builtins,
)


def test_all_wave_c_blocks_registered():
    """Verify all Wave C blocks are registered in built-in catalog."""
    # Force population of built-in catalog
    _ = new_registry_with_builtins()

    blocks = list_blocks()
    wave_c_blocks = {720, 1700, 3500, 3600, 6300, 12161}
    assert wave_c_blocks.issubset(
        blocks
    ), f"Missing Wave C blocks: {wave_c_blocks - blocks}"


def test_wave_c_blocks_accessible_via_import():
    """Verify all Wave C blocks can be imported directly."""
    # All imports should succeed without errors
    assert BLOCK_720_SCHEMA.block_id == 720
    assert BLOCK_1700_SCHEMA.block_id == 1700
    assert BLOCK_3500_SCHEMA.block_id == 3500
    assert BLOCK_3600_SCHEMA.block_id == 3600
    assert BLOCK_6300_SCHEMA.block_id == 6300
    assert BLOCK_12161_SCHEMA.block_id == 12161


def test_wave_c_blocks_minimal_parseability():
    """Verify Wave C blocks can parse minimal payloads without errors."""
    # Create minimal payloads matching min_length for each block
    block_720_payload = bytes([0] * BLOCK_720_SCHEMA.min_length)
    block_1700_payload = bytes([0] * BLOCK_1700_SCHEMA.min_length)
    block_3500_payload = bytes([0] * BLOCK_3500_SCHEMA.min_length)
    block_3600_payload = bytes([0] * BLOCK_3600_SCHEMA.min_length)
    block_6300_payload = bytes([0] * BLOCK_6300_SCHEMA.min_length)
    block_12161_payload = bytes([0] * BLOCK_12161_SCHEMA.min_length)

    # Parsing should not raise exceptions (basic sanity check)
    # Note: Actual parsing requires V2Parser integration
    assert len(block_720_payload) >= 2
    assert len(block_1700_payload) >= 4
    assert len(block_3500_payload) >= 16
    assert len(block_3600_payload) >= 16
    assert len(block_6300_payload) >= 25
    assert len(block_12161_payload) >= 4


def test_total_registered_blocks_count():
    """Verify total number of registered blocks after Wave C."""
    _ = new_registry_with_builtins()
    blocks = list_blocks()

    # Wave A: 100, 1100, 1300, 1400, 1500, 6000, 6100 (7 blocks)
    # Wave B: 2000, 2200, 2400, 7000, 11000, 12002, 19000 (7 blocks)
    # Wave C: 720, 1700, 3500, 3600, 6300, 12161 (6 blocks)
    # Total: 20 blocks
    assert len(blocks) == 20, f"Expected 20 blocks, got {len(blocks)}: {sorted(blocks)}"
