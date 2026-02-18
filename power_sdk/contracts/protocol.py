"""Protocol layer contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .transport import TransportProtocol


@dataclass
class NormalizedPayload:
    """Normalized payload — contract between protocol layer and parser.

    Big-endian bytes, framing stripped. Protocol-agnostic.
    """

    block_id: int
    data: bytes  # Big-endian, no framing
    device_address: int
    protocol_version: int | None = None


class ProtocolLayerInterface(ABC):
    """Protocol layer interface.

    Responsibilities:
    - Build wire request from logical read params
    - Validate and decode raw transport response
    - Return normalized payload for parser

    Does NOT know about:
    - Block schemas
    - Field parsing
    - Device models
    """

    @abstractmethod
    def read_block(
        self,
        transport: TransportProtocol,
        device_address: int,
        block_id: int,
        register_count: int,
    ) -> NormalizedPayload:
        """Read a block via transport and return normalized payload.

        Args:
            transport: Transport layer to use
            device_address: Device address on the bus
            block_id: Block address to read
            register_count: Number of registers to read

        Returns:
            NormalizedPayload with clean bytes

        Raises:
            ProtocolError: On framing error or CRC mismatch
        """
