"""V2 Protocol Parser

Core parsing engine for V2 protocol blocks.
"""

import logging
import time
from threading import RLock
from typing import Any, cast

from power_sdk.contracts.parser import ParserInterface
from power_sdk.contracts.schema import SchemaProtocol
from power_sdk.contracts.types import ParsedRecord
from power_sdk.errors import ParserError

from .schema import ArrayField, BlockSchema, Field, FieldGroup, PackedField
from .types import V2_PROTOCOL_VERSION

logger = logging.getLogger(__name__)


class V2Parser(ParserInterface):
    """V2 Protocol Parser.

    Parses blocks using declarative schemas.
    """

    def __init__(self) -> None:
        """Initialize V2 parser."""
        self._schemas: dict[int, BlockSchema] = {}
        self._schemas_lock = RLock()

    def register_schema(self, schema: SchemaProtocol) -> None:
        """Register a block schema.

        Accepts any object satisfying SchemaProtocol.  In practice the V2
        parser only works with BlockSchema instances; a TypeError is raised for
        any other type so misconfigurations are caught early.

        Idempotent: re-registering the same object or a structurally identical
        schema is a no-op.  Raises ValueError if block_id is already registered
        with a different name OR different fields (structural conflict).

        Identity check order:
          1. Object identity (``existing is schema``) — fastest path, always safe.
          2. Structural equality (name + fields via frozen-dataclass ``==``) —
             catches separately-constructed but identical schemas.
          3. Name mismatch or structural difference → ValueError.

        Args:
            schema: BlockSchema (or SchemaProtocol-compatible object) to register

        Raises:
            TypeError: If schema is not a BlockSchema instance
            ValueError: If block_id already registered with a conflicting schema
        """
        if not isinstance(schema, BlockSchema):
            raise TypeError(
                f"V2Parser requires a BlockSchema instance, got {type(schema).__name__}"
            )
        with self._schemas_lock:
            existing = self._schemas.get(schema.block_id)
            if existing is not None:
                if existing is schema:
                    return  # same object — definite no-op
                # BlockSchema is a frozen dataclass; == compares all fields.
                if existing.name == schema.name and existing.fields == schema.fields:
                    return  # structurally identical — safe no-op
                raise ValueError(
                    f"Block {schema.block_id} already registered as {existing.name!r}, "
                    f"cannot re-register as {schema.name!r} with different fields"
                )

            self._schemas[schema.block_id] = schema
        logger.debug(f"Registered schema: Block {schema.block_id} ({schema.name})")

    def get_schema(self, block_id: int) -> SchemaProtocol | None:
        """Get schema for block ID.

        Args:
            block_id: Block ID

        Returns:
            BlockSchema (as SchemaProtocol) or None if not registered
        """
        with self._schemas_lock:
            return cast("SchemaProtocol | None", self._schemas.get(block_id))

    def parse_block(
        self,
        block_id: int,
        data: bytes,
        validate: bool = True,
        protocol_version: int | None = None,
    ) -> ParsedRecord:
        """Parse a block.

        Args:
            block_id: Block ID
            data: Normalized byte buffer (big-endian, no framing)
            validate: Whether to validate against schema
            protocol_version: Protocol version hint (None = use V2_PROTOCOL_VERSION)

        Returns:
            ParsedRecord with parsed values and metadata

        Raises:
            ValueError: If block_id not registered or parsing fails
            ParserError: If schema validation fails in strict mode
        """
        # Resolve version: caller hint takes precedence; fall back to V2 default
        _version = (
            protocol_version if protocol_version is not None else V2_PROTOCOL_VERSION
        )

        with self._schemas_lock:
            schema = self._schemas.get(block_id)
        if not schema:
            raise ParserError(f"No schema registered for block {block_id}")

        # Validate data
        validation_result = None
        if validate:
            validation_result = schema.validate(data)

            if not validation_result.valid:
                error_msg = (
                    f"Block {block_id} ({schema.name}) validation failed: "
                    f"{validation_result.errors}"
                )

                if schema.strict:
                    # In strict mode, fail fast
                    raise ParserError(error_msg)
                else:
                    # In non-strict mode, just warn and continue
                    logger.warning(error_msg)

        # Parse all fields
        values: dict[str, Any] = {}

        for field_def in schema.fields:
            try:
                # FieldGroup: parse sub-fields into a nested dict and move on.
                # FieldGroup has no min_protocol_version or flat offset/size contract.
                if isinstance(field_def, FieldGroup):
                    values[field_def.name] = field_def.parse(data)
                    continue

                # Check if field is available (protocol version gate)
                if (
                    field_def.min_protocol_version
                    and _version < field_def.min_protocol_version
                ):
                    logger.debug(
                        f"Skipping field '{field_def.name}' "
                        f"(requires protocol >= {field_def.min_protocol_version})"
                    )
                    values[field_def.name] = None
                    continue

                # Check if field fits in data
                field_end = field_def.offset + field_def.size()
                if field_end > len(data):
                    if field_def.required:
                        logger.warning(
                            f"Required field '{field_def.name}' at offset "
                            f"{field_def.offset} exceeds data length {len(data)}"
                        )
                    values[field_def.name] = None
                    continue

                # Parse based on field type
                if isinstance(field_def, (Field, ArrayField)):
                    values[field_def.name] = field_def.parse(data)

                elif isinstance(field_def, PackedField):
                    # PackedField uses its configured base_type
                    values[field_def.name] = field_def.parse(data)

                else:
                    logger.warning(f"Unknown field type: {type(field_def).__name__}")
                    values[field_def.name] = None

            except Exception as e:
                if field_def.required:
                    logger.error(
                        f"Error parsing required field '{field_def.name}': {e}"
                    )
                    raise ParserError(
                        f"Failed to parse field '{field_def.name}': {e}"
                    ) from e
                else:
                    logger.debug(f"Optional field '{field_def.name}' parse error: {e}")
                    values[field_def.name] = None

        # Create ParsedRecord
        parsed = ParsedRecord(
            block_id=block_id,
            name=schema.name,
            values=values,
            raw=data,
            length=len(data),
            protocol_version=_version,
            schema_version=schema.schema_version,
            timestamp=time.time(),
            validation=validation_result,
        )

        # Log warnings if validation failed
        if validation_result and validation_result.warnings:
            for warning in validation_result.warnings:
                logger.debug(f"Block {block_id} ({schema.name}): {warning}")
        if validation_result and validation_result.missing_fields:
            logger.warning(
                "Block %s (%s): missing %d field(s): %s",
                block_id,
                schema.name,
                len(validation_result.missing_fields),
                ", ".join(validation_result.missing_fields[:8]),
            )

        return parsed

    def list_schemas(self) -> dict[int, str]:
        """List all registered schemas.

        Returns:
            Dictionary mapping block_id → schema_name
        """
        with self._schemas_lock:
            return {
                block_id: schema.name for block_id, schema in self._schemas.items()
            }
