"""Device model layer contract."""

from abc import ABC, abstractmethod
from typing import Any, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from ..protocol.v2.types import ParsedBlock
    from ..models.types import BlockGroup


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
    def update_from_block(self, parsed: 'ParsedBlock'):
        """Update device state from parsed block.

        Args:
            parsed: ParsedBlock from V2 parser

        This method knows how to map block data to device attributes.
        """
        pass

    @abstractmethod
    def get_state(self) -> Dict[str, Any]:
        """Get complete device state as dict."""
        pass

    @abstractmethod
    def get_group_state(self, group: 'BlockGroup') -> Dict[str, Any]:
        """Get state for specific block group."""
        pass
