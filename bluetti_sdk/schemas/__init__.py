"""Schema Registry and Definitions

This module provides:
- SchemaRegistry: Instance-scoped schema storage
- Pre-defined schemas for common blocks (100, 1300, 6000, etc.)
- Declarative schema definition API (@block_schema decorator)
- Read-only access to built-in schema catalog

Architecture:
- Built-in catalog: Module-level immutable registry of standard schemas
- Instance registries: Created via new_registry_with_builtins()
- No global mutable state: V2Client uses instance-scoped registries

Recommended Usage:
    from bluetti_sdk.schemas import new_registry_with_builtins

    # Create instance-scoped registry for V2Client
    registry = new_registry_with_builtins()
    client = V2Client(transport, profile, schema_registry=registry)

Declarative API Example:
    from bluetti_sdk.schemas import block_schema, block_field

    @block_schema(block_id=100, name="APP_HOME_DATA")
    @dataclass
    class AppHomeData:
        voltage: float = block_field(offset=0, type=UInt16(), unit="V")
        soc: int = block_field(offset=4, type=UInt16(), unit="%")
"""

# Import schema definitions (all declarative)
from .block_100_declarative import BLOCK_100_DECLARATIVE_SCHEMA as BLOCK_100_SCHEMA
from .block_1100_declarative import BLOCK_1100_DECLARATIVE_SCHEMA as BLOCK_1100_SCHEMA
from .block_1300_declarative import BLOCK_1300_DECLARATIVE_SCHEMA as BLOCK_1300_SCHEMA
from .block_1400_declarative import BLOCK_1400_DECLARATIVE_SCHEMA as BLOCK_1400_SCHEMA
from .block_1500_declarative import BLOCK_1500_DECLARATIVE_SCHEMA as BLOCK_1500_SCHEMA
from .block_2000_declarative import BLOCK_2000_SCHEMA
from .block_2200_declarative import BLOCK_2200_SCHEMA
from .block_2400_declarative import BLOCK_2400_SCHEMA
from .block_6000_declarative import BLOCK_6000_DECLARATIVE_SCHEMA as BLOCK_6000_SCHEMA
from .block_6100_declarative import BLOCK_6100_DECLARATIVE_SCHEMA as BLOCK_6100_SCHEMA
from .block_7000_declarative import BLOCK_7000_SCHEMA
from .block_11000_declarative import BLOCK_11000_SCHEMA
from .block_12002_declarative import BLOCK_12002_SCHEMA
from .block_19000_declarative import BLOCK_19000_SCHEMA
from .declarative import block_field, block_schema

# Import registry (only instance class and read-only functions)
# Testing-only imports - not in __all__, but accessible
from .registry import (
    SchemaRegistry,  # Instance class
    _clear_builtin_catalog_for_testing,  # noqa: F401
    _register_many_builtins,  # PRIVATE: initialization only
    get,  # Read-only: get from built-in catalog
    list_blocks,  # Read-only: list built-in catalog
    resolve_blocks,  # Read-only: resolve from built-in catalog
)
from .registry import new_registry_with_builtins as _new_registry_with_builtins

# Track if built-in catalog has been populated
_builtin_catalog_populated = False


def _populate_builtin_catalog() -> None:
    """Populate built-in catalog with standard schemas (INTERNAL USE ONLY).

    This is called automatically by new_registry_with_builtins().
    Idempotent - safe to call multiple times.
    """
    global _builtin_catalog_populated
    if _builtin_catalog_populated:
        return

    _register_many_builtins(
        [
            BLOCK_100_SCHEMA,
            BLOCK_1100_SCHEMA,
            BLOCK_1300_SCHEMA,
            BLOCK_1400_SCHEMA,
            BLOCK_1500_SCHEMA,
            BLOCK_2000_SCHEMA,
            BLOCK_2200_SCHEMA,
            BLOCK_2400_SCHEMA,
            BLOCK_6000_SCHEMA,
            BLOCK_6100_SCHEMA,
            BLOCK_7000_SCHEMA,
            BLOCK_11000_SCHEMA,
            BLOCK_12002_SCHEMA,
            BLOCK_19000_SCHEMA,
        ]
    )
    _builtin_catalog_populated = True


def new_registry_with_builtins() -> SchemaRegistry:
    """Create a new instance-scoped registry preloaded with built-in schemas.

    Returns:
        SchemaRegistry instance containing copies of all built-in schemas.

    Usage:
        registry = new_registry_with_builtins()
        client = V2Client(transport, profile, schema_registry=registry)
    """
    _populate_builtin_catalog()
    return _new_registry_with_builtins()


def _reset_builtin_catalog_for_testing() -> None:
    """Reset built-in catalog population flag (TESTING ONLY).

    WARNING: For test isolation only. Use with _clear_builtin_catalog_for_testing().
    """
    global _builtin_catalog_populated
    _builtin_catalog_populated = False


__all__ = [
    # Schema definitions
    "BLOCK_100_SCHEMA",
    "BLOCK_1100_SCHEMA",
    "BLOCK_1300_SCHEMA",
    "BLOCK_1400_SCHEMA",
    "BLOCK_1500_SCHEMA",
    "BLOCK_2000_SCHEMA",
    "BLOCK_2200_SCHEMA",
    "BLOCK_2400_SCHEMA",
    "BLOCK_6000_SCHEMA",
    "BLOCK_6100_SCHEMA",
    "BLOCK_7000_SCHEMA",
    "BLOCK_11000_SCHEMA",
    "BLOCK_12002_SCHEMA",
    "BLOCK_19000_SCHEMA",
    # Registry class and instance creation
    "SchemaRegistry",
    # Declarative API
    "block_field",
    "block_schema",
    # Read-only access to built-in catalog
    "get",
    "list_blocks",
    "new_registry_with_builtins",
    "resolve_blocks",
]
