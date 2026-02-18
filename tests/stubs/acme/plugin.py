"""ACME stub plugin — used exclusively in conformance tests.

Implements the minimum PluginManifest contract for a fictional 'acme/v1' vendor.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from power_sdk.contracts.parser import ParserInterface
from power_sdk.contracts.protocol import NormalizedPayload, ProtocolLayerInterface
from power_sdk.contracts.types import ParsedRecord
from power_sdk.devices.types import BlockGroupDefinition, DeviceProfile
from power_sdk.plugins.manifest import PluginManifest

# ---------------------------------------------------------------------------
# Stub DeviceProfile
# ---------------------------------------------------------------------------

ACME_PROFILE = DeviceProfile(
    model="ACME_DEV1",
    type_id="acme_dev1",
    protocol="acme_v1",
    description="ACME stub device (conformance testing only)",
    protocol_version=1,
    groups={
        "core": BlockGroupDefinition(
            name="core",
            blocks=[1],
            description="Core data block",
            poll_interval=30,
        )
    },
)


# ---------------------------------------------------------------------------
# Minimal schema stub
# ---------------------------------------------------------------------------


@dataclass
class _AcmeSchema:
    block_id: int
    name: str
    min_length: int = 0


# ---------------------------------------------------------------------------
# Stub Parser
# ---------------------------------------------------------------------------


class _StubParser(ParserInterface):
    """Minimal parser: knows one block (id=1)."""

    def get_schema(self, block_id: int) -> Any:
        if block_id == 1:
            return _AcmeSchema(block_id=1, name="ACME_BLOCK_1")
        return None

    def list_schemas(self) -> dict[int, str]:
        return {1: "ACME_BLOCK_1"}

    def register_schema(self, schema: Any) -> None:
        pass

    def parse_block(
        self,
        block_id: int,
        data: bytes,
        validate: bool = True,
        protocol_version: int | None = None,
    ) -> ParsedRecord:
        return ParsedRecord(
            block_id=block_id,
            name="ACME_BLOCK_1",
            values={},
            raw=data,
            length=len(data),
            protocol_version=protocol_version,
            schema_version="0.1.0",
            timestamp=0.0,
        )


# ---------------------------------------------------------------------------
# Stub Protocol Layer
# ---------------------------------------------------------------------------


class _StubProtocol(ProtocolLayerInterface):
    """Returns a fixed two-byte payload."""

    def read_block(
        self,
        transport: Any,
        device_address: int,
        block_id: int,
        register_count: int,
    ) -> NormalizedPayload:
        return NormalizedPayload(
            block_id=block_id,
            data=b"\x00\x00",
            device_address=device_address,
        )


# ---------------------------------------------------------------------------
# Profile loader
# ---------------------------------------------------------------------------


def _profile_loader(profile_id: str) -> DeviceProfile:
    if profile_id == "ACME_DEV1":
        return ACME_PROFILE
    raise ValueError(f"Unknown ACME profile: {profile_id!r}")


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------

ACME_V1_MANIFEST = PluginManifest(
    vendor="acme",
    protocol="v1",
    version="0.1.0",
    description="ACME stub plugin (conformance testing only)",
    profile_ids=("ACME_DEV1",),
    transport_keys=("mqtt",),
    schema_pack_version="0.1.0",
    capabilities=("read",),
    parser_factory=_StubParser,
    protocol_layer_factory=_StubProtocol,
    profile_loader=_profile_loader,
    schema_loader=lambda profile, parser: None,
)
