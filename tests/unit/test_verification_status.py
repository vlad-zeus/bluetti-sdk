"""Tests for schema verification status metadata."""

from bluetti_sdk.schemas import new_registry_with_builtins


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

    # Wave A/B/C blocks (20 total)
    assert len(smali_verified) == 20, (
        f"Expected 20 smali_verified schemas (Wave A/B/C), "
        f"found {len(smali_verified)}"
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

    # Wave D blocks (25 total)
    assert len(inferred) == 25, (
        f"Expected 25 inferred schemas (Wave D), found {len(inferred)}"
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

    # Expected distribution
    assert status_counts.get("smali_verified", 0) == 20
    assert status_counts.get("inferred", 0) == 25
    assert status_counts.get("device_verified", 0) == 0  # None yet
    assert status_counts.get("partial", 0) == 0  # None yet


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
    """Verify Wave D blocks are marked inferred."""
    registry = new_registry_with_builtins()

    # Wave D Batch 1-5 blocks (sample)
    wave_d_blocks = [
        14500, 14700, 15500, 15600, 15700,  # Batch 1
        15750, 17000, 19365, 19425, 19485,  # Batch 2
        17100,  # Batch 3
        17400, 18000, 18300, 26001,  # Batch 4
        18400, 18500, 18600, 29770, 29772,  # Batch 5
    ]

    for block_id in wave_d_blocks:
        schema = registry.get(block_id)
        assert schema is not None, f"Block {block_id} not registered"
        assert schema.verification_status == "inferred", (
            f"Block {block_id} should be inferred, got {schema.verification_status}"
        )
