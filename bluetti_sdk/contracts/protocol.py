"""Protocol layer contract."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .transport import TransportProtocol


@dataclass
class NormalizedPayload:
    """Normalized payload ready for parsing.

    This is the CONTRACT between protocol layer and parser.
    """

    block_id: int
    data: bytes  # Big-endian, no framing
    device_address: int
    protocol_version: int = 2000


class ProtocolLayerInterface(ABC):
    """Protocol layer interface.

    Responsibilities:
    - Modbus framing/unframing
    - CRC validation
    - Byte normalization (big-endian)

    Does NOT know about:
    - Block schemas
    - Field parsing
    - Device models
    """

    @abstractmethod
    def read_block(
        self,
        transport: "TransportProtocol",
        device_address: int,
        block_id: int,
        register_count: int,
    ) -> NormalizedPayload:
        """Read a V2 block via Modbus.

        Args:
            transport: Transport layer to use
            device_address: Modbus device address
            block_id: V2 block address
            register_count: Number of registers to read

        Returns:
            NormalizedPayload with clean bytes

        Raises:
            ProtocolError: If Modbus error or CRC mismatch
        """
