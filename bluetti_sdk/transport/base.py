"""Transport layer base protocol.

DEPRECATED: This module is deprecated. Import from bluetti_sdk.contracts instead.
Kept for backward compatibility.
"""

# Re-export from contracts for backward compatibility
from ..contracts.transport import TransportProtocol

__all__ = ['TransportProtocol']
