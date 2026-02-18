"""Client layer contract."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List

if TYPE_CHECKING:
    from ..models.types import BlockGroup
    from ..protocol.v2.types import ParsedBlock


class ClientInterface(ABC):
    """High-level client interface.

    Responsibilities:
    - Orchestrate layers: transport → protocol → parser → device
    - Device discovery
    - Polling loops
    - Error handling

    This is the PUBLIC API for applications.
    """

    @abstractmethod
    def connect(self) -> None:
        """Connect to device."""

    @abstractmethod
    def read_block(self, block_id: int) -> "ParsedBlock":
        """Read and parse a V2 block.

        Args:
            block_id: Block ID to read

        Returns:
            ParsedBlock with parsed data

        Flow:
            1. Build Modbus request (protocol layer)
            2. Send via transport
            3. Normalize response (protocol layer)
            4. Parse (v2_parser)
            5. Update device model
            6. Return ParsedBlock
        """

    @abstractmethod
    def read_group(
        self, group: "BlockGroup", partial_ok: bool = True
    ) -> List["ParsedBlock"]:
        """Read a block group.

        Args:
            group: BlockGroup to read
            partial_ok: If True (default), return partial results on failures.
                       If False, fail fast on first error.

        Returns:
            List of ParsedBlock (one per block in group)
        """

    @abstractmethod
    def get_device_state(self) -> Dict[str, Any]:
        """Get current device state."""

