"""Tests for Bluetti manifest wiring behavior."""

from unittest.mock import Mock

import pytest
from power_sdk.devices.types import BlockGroupDefinition, DeviceProfile
from power_sdk.plugins.bluetti.v2.manifest_instance import _load_schemas_for_profile


def _profile_with_blocks(*blocks: int) -> DeviceProfile:
    return DeviceProfile(
        model="TEST",
        type_id="TEST",
        protocol="v2",
        description="test",
        protocol_version=2000,
        groups={
            "core": BlockGroupDefinition(
                name="core",
                blocks=list(blocks),
                description="core",
                poll_interval=5,
            )
        },
    )


def test_schema_loader_fails_fast_on_unknown_block() -> None:
    parser = Mock()
    profile = _profile_with_blocks(100, 999999)
    with pytest.raises(ValueError, match="Missing schemas for blocks"):
        _load_schemas_for_profile(profile, parser)
