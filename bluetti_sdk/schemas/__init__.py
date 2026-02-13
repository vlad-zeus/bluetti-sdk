"""Schema Registry and Definitions

This module provides:
- SchemaRegistry: Central storage for BlockSchema instances
- Pre-defined schemas for common blocks (100, 1300, 6000, etc.)
- Lazy registration to avoid import side-effects

Schemas are registered lazily via ensure_registered() to avoid
mutating global state on import. This improves testability and
makes behavior more predictable.
"""

# Import schema definitions (but don't register yet)
from .block_100 import BLOCK_100_SCHEMA
from .block_1300 import BLOCK_1300_SCHEMA
from .block_6000 import BLOCK_6000_SCHEMA
from .registry import (
    get,
    list_blocks,
    register,
    register_many,
    resolve_blocks,
)

# Track if schemas have been registered
_registered = False


def ensure_registered() -> None:
    """Ensure all schemas are registered (idempotent).

    This function can be called multiple times safely.
    Schemas are only registered once on first call.

    This lazy approach avoids import side-effects.
    """
    global _registered
    if _registered:
        return

    register_many(
        [
            BLOCK_100_SCHEMA,
            BLOCK_1300_SCHEMA,
            BLOCK_6000_SCHEMA,
        ]
    )
    _registered = True


def _reset_registration_flag() -> None:
    """Reset registration flag (testing only).

    WARNING: For testing only. Use with _clear_for_testing() from registry.
    """
    global _registered
    _registered = False


__all__ = [
    "BLOCK_100_SCHEMA",
    "BLOCK_1300_SCHEMA",
    "BLOCK_6000_SCHEMA",
    "ensure_registered",
    "get",
    "list_blocks",
    "register",
    "register_many",
    "resolve_blocks",
]
