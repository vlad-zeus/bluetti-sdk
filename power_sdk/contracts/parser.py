"""Parser layer contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .types import ParsedRecord


class ParserInterface(ABC):
    """Parser interface — protocol-agnostic.

    Responsibilities:
    - Parse normalized bytes using schemas
    - Apply transform pipelines
    - Validate against schema

    Does NOT know about:
    - Transport
    - Modbus framing
    - Device state management
    """

    @abstractmethod
    def parse_block(
        self,
        block_id: int,
        data: bytes,
        validate: bool = True,
        protocol_version: int | None = None,
    ) -> ParsedRecord:
        """Parse a block.

        Args:
            block_id: Block identifier
            data: Normalized byte buffer (big-endian, no framing)
            validate: Whether to validate against schema
            protocol_version: Protocol version hint (None = use parser default)

        Returns:
            ParsedRecord with parsed values

        Raises:
            ParserError: If block_id not registered or parsing fails
        """

    @abstractmethod
    def register_schema(self, schema: Any) -> None:
        """Register a block schema."""

    @abstractmethod
    def get_schema(self, block_id: int) -> Any | None:
        """Get schema for block ID. Returns None if not registered."""

    @abstractmethod
    def list_schemas(self) -> dict[int, str]:
        """List all registered schemas as {block_id: schema_name}."""
