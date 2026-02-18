"""Unit tests for Wave D Batch 5 block schemas (18400, 18500, 18600, 29770, 29772)."""

from power_sdk.plugins.bluetti.v2.schemas import (
    BLOCK_18400_SCHEMA,
    BLOCK_18500_SCHEMA,
    BLOCK_18600_SCHEMA,
    BLOCK_29770_SCHEMA,
    BLOCK_29772_SCHEMA,
)


def test_block_18400_contract():
    """Verify Block 18400 (EPAD_LIQUID_POINT1) schema contract."""
    assert BLOCK_18400_SCHEMA.block_id == 18400
    assert BLOCK_18400_SCHEMA.name == "EPAD_LIQUID_POINT1"
    assert BLOCK_18400_SCHEMA.min_length == 2  # First item only (smali verified)
    assert BLOCK_18400_SCHEMA.protocol_version == 2000
    assert BLOCK_18400_SCHEMA.strict is False
    assert BLOCK_18400_SCHEMA.verification_status == "smali_verified"


def test_block_18400_field_structure():
    """Verify Block 18400 field structure and types (smali verified)."""
    fields = {f.name: f for f in BLOCK_18400_SCHEMA.fields}

    # Smali-verified structure: 2 bytes per calibration point
    # Source: EpadParser.baseLiquidPointParse, EpadLiquidCalibratePoint bean
    assert "volume" in fields
    assert fields["volume"].offset == 0
    assert fields["volume"].required is False
    assert fields["volume"].type.__class__.__name__ == "UInt8"

    assert "liquid" in fields
    assert fields["liquid"].offset == 1
    assert fields["liquid"].required is False
    assert fields["liquid"].type.__class__.__name__ == "UInt8"

    # Only 2 fields in the verified structure (first item only)
    assert len(fields) == 2


def test_block_18500_contract():
    """Verify Block 18500 (EPAD_LIQUID_POINT2) schema contract."""
    assert BLOCK_18500_SCHEMA.block_id == 18500
    assert BLOCK_18500_SCHEMA.name == "EPAD_LIQUID_POINT2"
    assert BLOCK_18500_SCHEMA.min_length == 2  # First item only (smali verified)
    assert BLOCK_18500_SCHEMA.protocol_version == 2000
    assert BLOCK_18500_SCHEMA.strict is False
    assert BLOCK_18500_SCHEMA.verification_status == "smali_verified"


def test_block_18500_field_structure():
    """Verify Block 18500 field structure and types (smali verified)."""
    fields = {f.name: f for f in BLOCK_18500_SCHEMA.fields}

    # Same smali-verified structure as 18400 (shared parser)
    assert "volume" in fields
    assert fields["volume"].offset == 0
    assert fields["volume"].required is False
    assert fields["volume"].type.__class__.__name__ == "UInt8"

    assert "liquid" in fields
    assert fields["liquid"].offset == 1
    assert fields["liquid"].required is False
    assert fields["liquid"].type.__class__.__name__ == "UInt8"

    # Only 2 fields in the verified structure (first item only)
    assert len(fields) == 2


def test_block_18600_contract():
    """Verify Block 18600 (EPAD_LIQUID_POINT3) schema contract."""
    assert BLOCK_18600_SCHEMA.block_id == 18600
    assert BLOCK_18600_SCHEMA.name == "EPAD_LIQUID_POINT3"
    assert BLOCK_18600_SCHEMA.min_length == 2  # First item only (smali verified)
    assert BLOCK_18600_SCHEMA.protocol_version == 2000
    assert BLOCK_18600_SCHEMA.strict is False
    assert BLOCK_18600_SCHEMA.verification_status == "smali_verified"


def test_block_18600_field_structure():
    """Verify Block 18600 field structure and types (smali verified)."""
    fields = {f.name: f for f in BLOCK_18600_SCHEMA.fields}

    # Same smali-verified structure as 18400/18500 (shared parser)
    assert "volume" in fields
    assert fields["volume"].offset == 0
    assert fields["volume"].required is False
    assert fields["volume"].type.__class__.__name__ == "UInt8"

    assert "liquid" in fields
    assert fields["liquid"].offset == 1
    assert fields["liquid"].required is False
    assert fields["liquid"].type.__class__.__name__ == "UInt8"

    # Only 2 fields in the verified structure (first item only)
    assert len(fields) == 2


def test_block_29770_contract():
    """Verify Block 29770 (BOOT_UPGRADE_SUPPORT) schema contract."""
    assert BLOCK_29770_SCHEMA.block_id == 29770
    assert BLOCK_29770_SCHEMA.name == "BOOT_UPGRADE_SUPPORT"
    assert BLOCK_29770_SCHEMA.min_length == 4
    assert BLOCK_29770_SCHEMA.protocol_version == 2000
    assert BLOCK_29770_SCHEMA.strict is False


def test_block_29770_field_structure():
    """Verify Block 29770 field structure and types (smali-verified)."""
    fields = {f.name: f for f in BLOCK_29770_SCHEMA.fields}

    # Boot upgrade support values (from BootUpgradeSupport bean)
    assert "is_supported" in fields
    assert fields["is_supported"].offset == 0
    assert fields["is_supported"].required is False

    assert "software_version_total" in fields
    assert fields["software_version_total"].offset == 2
    assert fields["software_version_total"].required is False


def test_block_29772_contract():
    """Verify Block 29772 (BOOT_SOFTWARE_INFO) schema contract."""
    assert BLOCK_29772_SCHEMA.block_id == 29772
    assert BLOCK_29772_SCHEMA.name == "BOOT_SOFTWARE_INFO"
    assert BLOCK_29772_SCHEMA.min_length == 10
    assert BLOCK_29772_SCHEMA.protocol_version == 2000
    assert BLOCK_29772_SCHEMA.strict is False


def test_block_29772_field_structure():
    """Verify Block 29772 field structure (smali-verified item structure)."""
    fields = {f.name: f for f in BLOCK_29772_SCHEMA.fields}

    # First component item (10 bytes, from BootSoftwareItem bean)
    assert "software_type" in fields
    assert fields["software_type"].offset == 0
    assert fields["software_type"].required is False

    assert "software_version" in fields
    assert fields["software_version"].offset == 2

    assert "unused_byte_0" in fields
    assert fields["unused_byte_0"].offset == 6

    assert "unused_byte_3" in fields
    assert fields["unused_byte_3"].offset == 9

