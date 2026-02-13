"""V2 Parser layer contract."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..protocol.v2.types import ParsedBlock


class V2ParserInterface(ABC):
    """V2 Parser interface.

    Responsibilities:
    - Parse normalized bytes using schemas
    - Apply transform pipelines
    - Validate against schema

    Does NOT know about:
    - Modbus
    - Transport
    - Device state management
    """

    @abstractmethod
    def parse_block(
        self,
        block_id: int,
        data: bytes,
        validate: bool = True,
        protocol_version: int = 2000,
    ) -> "ParsedBlock":
        """Parse a V2 block.

        Args:
            block_id: Block ID
            data: Normalized byte buffer (big-endian, no framing)
            validate: Whether to validate against schema
            protocol_version: Device protocol version

        Returns:
            ParsedBlock with parsed values

        Raises:
            ValueError: If block_id not registered or parsing fails
        """

    @abstractmethod
    def register_schema(self, schema: Any) -> None:
        """Register a block schema."""
