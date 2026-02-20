"""Schema Registry and Definitions

This module provides:
- SchemaRegistry: Instance-scoped schema storage
- Pre-defined schemas for common blocks (100, 1300, 6000, etc.)
- Declarative schema definition API (@block_schema decorator)
- Read-only access to built-in schema catalog

Architecture:
- Built-in catalog: Module-level immutable registry of standard schemas
- Instance registries: Created via new_registry_with_builtins()
- No global mutable state: Client uses instance-scoped registries

Recommended Usage:
    from power_sdk.plugins.bluetti.v2.schemas import new_registry_with_builtins

    # Create instance-scoped registry and register needed schemas on parser
    registry = new_registry_with_builtins()
    for schema in registry.resolve_blocks([100, 1300], strict=False).values():
        parser.register_schema(schema)

Declarative API Example:
    from power_sdk.plugins.bluetti.v2.schemas import block_schema, block_field

    @block_schema(block_id=100, name="APP_HOME_DATA")
    @dataclass
    class AppHomeData:
        voltage: float = block_field(offset=0, type=UInt16(), unit="V")
        soc: int = block_field(offset=4, type=UInt16(), unit="%")
"""

from threading import Lock

# Import schema definitions (all declarative)
from .block_100_declarative import BLOCK_100_DECLARATIVE_SCHEMA as BLOCK_100_SCHEMA
from .block_720_declarative import BLOCK_720_SCHEMA
from .block_1100_declarative import BLOCK_1100_DECLARATIVE_SCHEMA as BLOCK_1100_SCHEMA
from .block_1300_declarative import BLOCK_1300_DECLARATIVE_SCHEMA as BLOCK_1300_SCHEMA
from .block_1400_declarative import BLOCK_1400_DECLARATIVE_SCHEMA as BLOCK_1400_SCHEMA
from .block_1500_declarative import BLOCK_1500_DECLARATIVE_SCHEMA as BLOCK_1500_SCHEMA
from .block_1700_declarative import BLOCK_1700_SCHEMA
from .block_2000_declarative import BLOCK_2000_SCHEMA
from .block_2200_declarative import BLOCK_2200_SCHEMA
from .block_2400_declarative import BLOCK_2400_SCHEMA
from .block_3500_declarative import BLOCK_3500_SCHEMA
from .block_3600_declarative import BLOCK_3600_SCHEMA
from .block_6000_declarative import BLOCK_6000_DECLARATIVE_SCHEMA as BLOCK_6000_SCHEMA
from .block_6100_declarative import BLOCK_6100_DECLARATIVE_SCHEMA as BLOCK_6100_SCHEMA
from .block_6300_declarative import BLOCK_6300_SCHEMA
from .block_7000_declarative import BLOCK_7000_SCHEMA
from .block_11000_declarative import BLOCK_11000_SCHEMA
from .block_12002_declarative import BLOCK_12002_SCHEMA
from .block_12161_declarative import BLOCK_12161_SCHEMA
from .block_14500_declarative import BLOCK_14500_SCHEMA
from .block_14700_declarative import BLOCK_14700_SCHEMA
from .block_15500_declarative import BLOCK_15500_SCHEMA
from .block_15600_declarative import BLOCK_15600_SCHEMA
from .block_15700_declarative import BLOCK_15700_SCHEMA
from .block_15750_declarative import BLOCK_15750_SCHEMA
from .block_17000_declarative import BLOCK_17000_SCHEMA
from .block_17100_declarative import BLOCK_17100_SCHEMA
from .block_17400_declarative import BLOCK_17400_SCHEMA
from .block_18000_declarative import BLOCK_18000_SCHEMA
from .block_18300_declarative import BLOCK_18300_SCHEMA
from .block_18400_declarative import BLOCK_18400_SCHEMA
from .block_18500_declarative import BLOCK_18500_SCHEMA
from .block_18600_declarative import BLOCK_18600_SCHEMA
from .block_19000_declarative import BLOCK_19000_SCHEMA
from .block_19100_declarative import BLOCK_19100_SCHEMA
from .block_19200_declarative import BLOCK_19200_SCHEMA
from .block_19300_declarative import BLOCK_19300_SCHEMA
from .block_19305_declarative import BLOCK_19305_SCHEMA
from .block_19365_declarative import BLOCK_19365_SCHEMA
from .block_19425_declarative import BLOCK_19425_SCHEMA
from .block_19485_declarative import BLOCK_19485_SCHEMA
from .block_26001_declarative import BLOCK_26001_SCHEMA
from .block_29770_declarative import BLOCK_29770_SCHEMA
from .block_29772_declarative import BLOCK_29772_SCHEMA
from .block_40127_declarative import BLOCK_40127_SCHEMA
from .declarative import block_field, block_schema, nested_group

# Import registry (only instance class and read-only functions)
from .registry import (
    SchemaRegistry,  # Instance class
    _register_many_builtins,  # PRIVATE: initialization only
    get,  # Read-only: get from built-in catalog
    list_blocks,  # Read-only: list built-in catalog
    resolve_blocks,  # Read-only: resolve from built-in catalog
)

# _clear_builtin_catalog_for_testing: not re-exported — import from .registry in tests
from .registry import new_registry_with_builtins as _new_registry_with_builtins

# Track if built-in catalog has been populated
_builtin_catalog_populated = False
_builtin_catalog_lock = Lock()


def _populate_builtin_catalog() -> None:
    """Populate built-in catalog with standard schemas (INTERNAL USE ONLY).

    This is called automatically by new_registry_with_builtins().
    Idempotent - safe to call multiple times.
    """
    global _builtin_catalog_populated
    if _builtin_catalog_populated:
        return
    with _builtin_catalog_lock:
        if _builtin_catalog_populated:
            return

        _register_many_builtins(
            [
                BLOCK_100_SCHEMA,
                BLOCK_720_SCHEMA,
                BLOCK_1100_SCHEMA,
                BLOCK_1300_SCHEMA,
                BLOCK_1400_SCHEMA,
                BLOCK_1500_SCHEMA,
                BLOCK_1700_SCHEMA,
                BLOCK_2000_SCHEMA,
                BLOCK_2200_SCHEMA,
                BLOCK_2400_SCHEMA,
                BLOCK_3500_SCHEMA,
                BLOCK_3600_SCHEMA,
                BLOCK_6000_SCHEMA,
                BLOCK_6100_SCHEMA,
                BLOCK_6300_SCHEMA,
                BLOCK_7000_SCHEMA,
                BLOCK_11000_SCHEMA,
                BLOCK_12002_SCHEMA,
                BLOCK_12161_SCHEMA,
                BLOCK_14500_SCHEMA,
                BLOCK_14700_SCHEMA,
                BLOCK_15500_SCHEMA,
                BLOCK_15600_SCHEMA,
                BLOCK_15700_SCHEMA,
                BLOCK_15750_SCHEMA,
                BLOCK_17000_SCHEMA,
                BLOCK_17100_SCHEMA,
                BLOCK_17400_SCHEMA,
                BLOCK_18000_SCHEMA,
                BLOCK_18300_SCHEMA,
                BLOCK_18400_SCHEMA,
                BLOCK_18500_SCHEMA,
                BLOCK_18600_SCHEMA,
                BLOCK_19000_SCHEMA,
                BLOCK_19100_SCHEMA,
                BLOCK_19200_SCHEMA,
                BLOCK_19300_SCHEMA,
                BLOCK_19305_SCHEMA,
                BLOCK_19365_SCHEMA,
                BLOCK_19425_SCHEMA,
                BLOCK_19485_SCHEMA,
                BLOCK_26001_SCHEMA,
                BLOCK_29770_SCHEMA,
                BLOCK_29772_SCHEMA,
                BLOCK_40127_SCHEMA,
            ]
        )
        _builtin_catalog_populated = True


def new_registry_with_builtins() -> SchemaRegistry:
    """Create a new instance-scoped registry preloaded with built-in schemas.

    Returns:
        SchemaRegistry instance containing copies of all built-in schemas.

    Usage:
        registry = new_registry_with_builtins()
        for schema in registry.resolve_blocks([100, 1300], strict=False).values():
            parser.register_schema(schema)
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
    "BLOCK_720_SCHEMA",
    "BLOCK_1100_SCHEMA",
    "BLOCK_1300_SCHEMA",
    "BLOCK_1400_SCHEMA",
    "BLOCK_1500_SCHEMA",
    "BLOCK_1700_SCHEMA",
    "BLOCK_2000_SCHEMA",
    "BLOCK_2200_SCHEMA",
    "BLOCK_2400_SCHEMA",
    "BLOCK_3500_SCHEMA",
    "BLOCK_3600_SCHEMA",
    "BLOCK_6000_SCHEMA",
    "BLOCK_6100_SCHEMA",
    "BLOCK_6300_SCHEMA",
    "BLOCK_7000_SCHEMA",
    "BLOCK_11000_SCHEMA",
    "BLOCK_12002_SCHEMA",
    "BLOCK_12161_SCHEMA",
    "BLOCK_14500_SCHEMA",
    "BLOCK_14700_SCHEMA",
    "BLOCK_15500_SCHEMA",
    "BLOCK_15600_SCHEMA",
    "BLOCK_15700_SCHEMA",
    "BLOCK_15750_SCHEMA",
    "BLOCK_17000_SCHEMA",
    "BLOCK_17100_SCHEMA",
    "BLOCK_17400_SCHEMA",
    "BLOCK_18000_SCHEMA",
    "BLOCK_18300_SCHEMA",
    "BLOCK_18400_SCHEMA",
    "BLOCK_18500_SCHEMA",
    "BLOCK_18600_SCHEMA",
    "BLOCK_19000_SCHEMA",
    "BLOCK_19100_SCHEMA",
    "BLOCK_19200_SCHEMA",
    "BLOCK_19300_SCHEMA",
    "BLOCK_19305_SCHEMA",
    "BLOCK_19365_SCHEMA",
    "BLOCK_19425_SCHEMA",
    "BLOCK_19485_SCHEMA",
    "BLOCK_26001_SCHEMA",
    "BLOCK_29770_SCHEMA",
    "BLOCK_29772_SCHEMA",
    "BLOCK_40127_SCHEMA",
    # Registry class and instance creation
    "SchemaRegistry",
    # Declarative API
    "block_field",
    "block_schema",
    # Read-only access to built-in catalog
    "get",
    "list_blocks",
    "nested_group",
    "new_registry_with_builtins",
    "resolve_blocks",
]
