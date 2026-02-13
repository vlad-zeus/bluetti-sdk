"""Device model layer contract."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from ..models.types import BlockGroup
    from ..protocol.v2.types import ParsedBlock


class DeviceModelInterface(ABC):
    """Device model interface.

    Responsibilities:
    - Store device state
    - Map ParsedBlock → device attributes
    - Provide high-level API

    Does NOT know about:
    - Byte offsets
    - Transforms
    - Modbus framing
    """

    @abstractmethod
    def update_from_block(self, parsed: "ParsedBlock") -> None:
        """Update device state from parsed block.

        Args:
            parsed: ParsedBlock from V2 parser

        This method knows how to map block data to device attributes.
        """

    @abstractmethod
    def get_state(self) -> Dict[str, Any]:
        """Get complete device state as dict."""

    @abstractmethod
    def get_group_state(self, group: "BlockGroup") -> Dict[str, Any]:
        """Get state for specific block group."""
