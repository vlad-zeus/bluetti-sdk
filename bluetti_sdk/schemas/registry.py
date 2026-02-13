"""Schema Registry - Central schema storage and resolution.

Responsibilities:
- Store BlockSchema instances by block_id
- Resolve schemas for device profiles
- Provide fail-fast or lenient lookup
- Validate schema consistency (prevent conflicting registrations)

This is a MODULE-LEVEL registry (singleton pattern).

Registration Strategy:
- Schemas are registered LAZILY via ensure_registered() from schemas/__init__.py
- This avoids import side-effects and improves testability
- Registration is idempotent (safe to call multiple times)
- V2Client automatically calls ensure_registered() during initialization
"""

import logging
from typing import Dict, List, Optional

# Forward declare for type hints
from ..protocol.v2.schema import BlockSchema

logger = logging.getLogger(__name__)


class _SchemaRegistry:
    """Internal schema registry implementation."""

    def __init__(self) -> None:
        self._schemas: Dict[int, BlockSchema] = {}

    def register(self, schema: BlockSchema) -> None:
        """Register a schema.

        Args:
            schema: BlockSchema to register

        Raises:
            ValueError: If block_id already registered with different schema
        """
        if schema.block_id in self._schemas:
            existing = self._schemas[schema.block_id]

            # Check if it's truly the same schema (not just same name)
            if existing.name != schema.name:
                raise ValueError(
                    f"Block {schema.block_id} already registered as "
                    f"'{existing.name}', cannot re-register as '{schema.name}'"
                )

            # Full structure validation: check field fingerprints
            # Compare: name, offset, type, required, transform
            conflicts = self._check_field_conflicts(existing, schema)
            if conflicts:
                raise ValueError(
                    f"Block {schema.block_id} ({schema.name}) structure conflict:\n"
                    + "\n".join(conflicts)
                )

            # Same block_id, same name, same structure → safe to skip
            logger.debug(f"Block {schema.block_id} already registered, skipping")
            return

        self._schemas[schema.block_id] = schema
        logger.debug(f"Registered schema: Block {schema.block_id} ({schema.name})")

    def _check_field_conflicts(
        self, existing: BlockSchema, new: BlockSchema
    ) -> List[str]:
        """Check for field-level conflicts between schemas.

        Compares field names, offsets, types, required flags, and transforms.

        Args:
            existing: Currently registered schema
            new: New schema to register

        Returns:
            List of conflict descriptions (empty if no conflicts)
        """
        conflicts = []

        # Build field maps
        existing_fields = {f.name: f for f in existing.fields}
        new_fields = {f.name: f for f in new.fields}

        # Check for added/removed fields
        existing_names = set(existing_fields.keys())
        new_names = set(new_fields.keys())

        if existing_names != new_names:
            added = new_names - existing_names
            removed = existing_names - new_names
            if added:
                conflicts.append(f"  Added fields: {sorted(added)}")
            if removed:
                conflicts.append(f"  Removed fields: {sorted(removed)}")

        # Check common fields for structural changes
        for name in existing_names & new_names:
            existing_field = existing_fields[name]
            new_field = new_fields[name]

            # Compare offset
            if existing_field.offset != new_field.offset:
                conflicts.append(
                    f"  Field '{name}': offset changed from "
                    f"{existing_field.offset} to {new_field.offset}"
                )

            # Compare type (class name + parameters)
            existing_type_repr = self._get_type_fingerprint(existing_field.type)
            new_type_repr = self._get_type_fingerprint(new_field.type)

            if existing_type_repr != new_type_repr:
                conflicts.append(
                    f"  Field '{name}': type changed from "
                    f"{existing_type_repr} to {new_type_repr}"
                )

            # Compare required flag
            if existing_field.required != new_field.required:
                conflicts.append(
                    f"  Field '{name}': required changed from "
                    f"{existing_field.required} to {new_field.required}"
                )

            # Compare transform
            if existing_field.transform != new_field.transform:
                conflicts.append(
                    f"  Field '{name}': transform changed from "
                    f"{existing_field.transform} to {new_field.transform}"
                )

        return conflicts

    def _get_type_fingerprint(self, field_type: object) -> str:
        """Get a unique fingerprint for a field type.

        Includes both the type class name and its parameters (length, bits, etc).

        Args:
            field_type: DataType instance

        Returns:
            String representation like "String(length=8)" or "Bitmap(bits=16)"
        """
        type_name = type(field_type).__name__

        # Extract relevant parameters based on type
        params = []

        # String types have length attribute
        if hasattr(field_type, "length"):
            params.append(f"length={field_type.length}")

        # Bitmap types have bits attribute
        if hasattr(field_type, "bits"):
            params.append(f"bits={field_type.bits}")

        # Enum types have mapping attribute
        if hasattr(field_type, "mapping") and field_type.mapping is not None:
            # For enums, include full mapping as fingerprint (sorted for stability)
            # Convert to sorted tuple of (value, name) pairs
            mapping_items = sorted(field_type.mapping.items())
            mapping_repr = repr(tuple(mapping_items))
            params.append(f"mapping={mapping_repr}")

        # Build fingerprint
        if params:
            return f"{type_name}({', '.join(params)})"
        else:
            return type_name

    def register_many(self, schemas: List[BlockSchema]) -> None:
        """Register multiple schemas at once.

        Args:
            schemas: List of BlockSchema to register
        """
        for schema in schemas:
            self.register(schema)

    def get(self, block_id: int) -> Optional[BlockSchema]:
        """Get schema by block_id.

        Args:
            block_id: Block ID to look up

        Returns:
            BlockSchema or None if not found
        """
        return self._schemas.get(block_id)

    def list_blocks(self) -> List[int]:
        """List all registered block IDs.

        Returns:
            Sorted list of registered block IDs
        """
        return sorted(self._schemas.keys())

    def resolve_blocks(
        self, block_ids: List[int], strict: bool = True
    ) -> Dict[int, BlockSchema]:
        """Resolve schemas for a list of block IDs.

        Args:
            block_ids: List of block IDs to resolve
            strict: If True, raise error for missing schemas.
                   If False, skip missing schemas and log warning.

        Returns:
            Dict mapping block_id → BlockSchema (only found schemas)

        Raises:
            ValueError: If strict=True and any schema is missing
        """
        resolved = {}
        missing = []

        for block_id in block_ids:
            schema = self.get(block_id)
            if schema:
                resolved[block_id] = schema
            else:
                missing.append(block_id)

        if missing:
            msg = f"Missing schemas for blocks: {missing}"
            if strict:
                raise ValueError(f"{msg}. Available blocks: {self.list_blocks()}")
            else:
                logger.warning(msg)

        return resolved

    def clear(self) -> None:
        """Clear all registered schemas.

        WARNING: This is intended for testing only.
        """
        self._schemas.clear()


# Module-level singleton instance
_registry = _SchemaRegistry()

# Public API (module-level functions that delegate to singleton)


def register(schema: BlockSchema) -> None:
    """Register a schema in the global registry."""
    _registry.register(schema)


def register_many(schemas: List[BlockSchema]) -> None:
    """Register multiple schemas in the global registry."""
    _registry.register_many(schemas)


def get(block_id: int) -> Optional[BlockSchema]:
    """Get schema from global registry."""
    return _registry.get(block_id)


def list_blocks() -> List[int]:
    """List all registered block IDs."""
    return _registry.list_blocks()


def resolve_blocks(block_ids: List[int], strict: bool = True) -> Dict[int, BlockSchema]:
    """Resolve schemas for block IDs from global registry."""
    return _registry.resolve_blocks(block_ids, strict)


def _clear_for_testing() -> None:
    """Clear global registry.

    WARNING: This is for testing only. Do not use in production code.
    Clearing the registry at runtime will break all schema resolution.
    """
    _registry.clear()
