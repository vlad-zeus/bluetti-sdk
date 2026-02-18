"""Tests for schema verification status metadata."""

from power_sdk.schemas import new_registry_with_builtins


def test_all_builtin_schemas_have_verification_status():
    """Verify all builtin schemas include verification_status metadata."""
    registry = new_registry_with_builtins()
    all_block_ids = registry.list_blocks()

    missing_status = []

    for block_id in all_block_ids:
        schema = registry.get(block_id)
        if schema and schema.verification_status is None:
            missing_status.append(block_id)

    assert not missing_status, (
        f"Schemas missing verification_status: {missing_status}. "
        "All schemas must specify verification status."
    )


def test_verification_status_values():
    """Verify all verification_status values are valid."""
    registry = new_registry_with_builtins()
    all_block_ids = registry.list_blocks()

    valid_statuses = {"smali_verified", "device_verified", "inferred", "partial"}
    invalid_schemas = []

    for block_id in all_block_ids:
        schema = registry.get(block_id)
        if schema and schema.verification_status not in valid_statuses:
            invalid_schemas.append((block_id, schema.verification_status))

    assert not invalid_schemas, (
        f"Schemas with invalid verification_status: {invalid_schemas}. "
        f"Valid values: {valid_statuses}"
    )


def test_smali_verified_count():
    """Verify expected number of smali_verified schemas."""
    registry = new_registry_with_builtins()
    all_block_ids = registry.list_blocks()

    smali_verified = [
        block_id
        for block_id in all_block_ids
        if registry.get(block_id).verification_status == "smali_verified"
    ]

    # Wave A/B/C plus upgraded Wave D parsed blocks (14700, 18300, 15500, 17100).
    assert len(smali_verified) == 43, (
        f"Expected 43 smali_verified schemas, "
        f"found {len(smali_verified)}: {sorted(smali_verified)}"
    )


def test_inferred_count():
    """Verify expected number of inferred schemas."""
    registry = new_registry_with_builtins()
    all_block_ids = registry.list_blocks()

    inferred = [
        block_id
        for block_id in all_block_ids
        if registry.get(block_id).verification_status == "inferred"
    ]

    # Remaining inferred blocks after partial/smali upgrades
    assert len(inferred) == 0, (
        f"Expected 0 inferred schemas, found {len(inferred)}"
    )


def test_verification_status_distribution():
    """Verify verification status distribution across all schemas."""
    registry = new_registry_with_builtins()
    all_block_ids = registry.list_blocks()

    status_counts = {}
    for block_id in all_block_ids:
        schema = registry.get(block_id)
        status = schema.verification_status
        status_counts[status] = status_counts.get(status, 0) + 1

    # Expected distribution after Wave D parsed-block upgrades.
    assert status_counts.get("smali_verified", 0) == 43
    assert status_counts.get("inferred", 0) == 0
    assert status_counts.get("device_verified", 0) == 0  # None yet
    # Remaining partial blocks: 15600, 17400 (14700, 18300, 15500, 17100 upgraded)
    assert status_counts.get("partial", 0) == 2


def test_wave_a_blocks_smali_verified():
    """Verify Wave A blocks are marked smali_verified."""
    registry = new_registry_with_builtins()

    # Wave A blocks
    wave_a_blocks = [100, 720, 1100, 1300, 1400, 1500, 1700, 2000, 2200, 2400]

    for block_id in wave_a_blocks:
        schema = registry.get(block_id)
        assert schema is not None, f"Block {block_id} not registered"
        assert schema.verification_status == "smali_verified", (
            f"Block {block_id} should be smali_verified, "
            f"got {schema.verification_status}"
        )


def test_wave_d_blocks_inferred():
    """Verify no Wave D blocks remain in inferred status."""
    registry = new_registry_with_builtins()

    inferred_blocks = [
        block_id
        for block_id in registry.list_blocks()
        if registry.get(block_id).verification_status == "inferred"
    ]
    assert not inferred_blocks, (
        f"Inferred blocks should be empty, got {inferred_blocks}"
    )


def test_partial_blocks():
    """Verify blocks upgraded to partial status (Commit 3)."""
    registry = new_registry_with_builtins()

    # Blocks with partial verification:
    # parse method confirmed, semantics/offsets deferred.
    # Note: 18000 upgraded to smali_verified after Agent B verification
    # Note: 18400/18500/18600/26001 are smali_verified after Agent C verification
    # Note: 14700 upgraded to smali_verified after Agent D deep dive
    # Note: 18300 upgraded to smali_verified after Agent G deep dive
    # Note: 15500, 17100 upgraded to smali_verified after Final Closure Sprint
    partial_blocks = [
        15600, 17400,
    ]

    for block_id in partial_blocks:
        schema = registry.get(block_id)
        assert schema is not None, f"Block {block_id} not registered"
        assert schema.verification_status == "partial", (
            f"Block {block_id} should be partial, got {schema.verification_status}"
        )


def test_agent_c_blocks_smali_verified():
    """Verify Agent C blocks (18400/18500/18600/26001) are smali_verified."""
    registry = new_registry_with_builtins()

    # Blocks verified by Agent C (field structure proven from smali)
    agent_c_blocks = [18400, 18500, 18600, 26001]

    for block_id in agent_c_blocks:
        schema = registry.get(block_id)
        assert schema is not None, f"Block {block_id} not registered"
        assert schema.verification_status == "smali_verified", (
            "Block "
            f"{block_id} should be smali_verified, "
            f"got {schema.verification_status}"
        )

