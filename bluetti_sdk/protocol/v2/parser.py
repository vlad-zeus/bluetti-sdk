"""V2 Protocol Parser

Core parsing engine for V2 protocol blocks.
"""

import logging
import time
from typing import Any, Dict, Optional

from ...contracts.parser import V2ParserInterface
from .schema import ArrayField, BlockSchema, Field, PackedField
from .types import ParsedBlock

logger = logging.getLogger(__name__)


class V2Parser(V2ParserInterface):
    """V2 Protocol Parser.

    Parses V2 blocks using declarative schemas.
    """

    def __init__(self) -> None:
        """Initialize V2 parser."""
        self._schemas: Dict[int, BlockSchema] = {}

    def register_schema(self, schema: BlockSchema) -> None:
        """Register a block schema.

        Args:
            schema: BlockSchema to register

        Raises:
            ValueError: If block_id already registered
        """
        if schema.block_id in self._schemas:
            raise ValueError(
                f"Block {schema.block_id} already registered "
                f"(existing: {self._schemas[schema.block_id].name})"
            )

        self._schemas[schema.block_id] = schema
        logger.debug(f"Registered schema: Block {schema.block_id} ({schema.name})")

    def get_schema(self, block_id: int) -> Optional[BlockSchema]:
        """Get schema for block ID.

        Args:
            block_id: Block ID

        Returns:
            BlockSchema or None if not registered
        """
        return self._schemas.get(block_id)

    def parse_block(
        self,
        block_id: int,
        data: bytes,
        validate: bool = True,
        protocol_version: int = 2000,
    ) -> ParsedBlock:
        """Parse a V2 block.

        Args:
            block_id: Block ID
            data: Normalized byte buffer (big-endian, no Modbus framing)
            validate: Whether to validate against schema
            protocol_version: Device protocol version

        Returns:
            ParsedBlock with parsed values and metadata

        Raises:
            ValueError: If block_id not registered or parsing fails
            ParserError: If schema validation fails in strict mode
        """
        schema = self._schemas.get(block_id)
        if not schema:
            raise ValueError(f"No schema registered for block {block_id}")

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
                    from ...errors import ParserError

                    raise ParserError(error_msg)
                else:
                    # In non-strict mode, just warn and continue
                    logger.warning(error_msg)

        # Parse all fields
        values: Dict[str, Any] = {}

        for field_def in schema.fields:
            try:
                # Check if field is available (protocol version gate)
                if (
                    field_def.min_protocol_version
                    and protocol_version < field_def.min_protocol_version
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
                    raise ValueError(
                        f"Failed to parse field '{field_def.name}': {e}"
                    ) from e
                else:
                    logger.debug(f"Optional field '{field_def.name}' parse error: {e}")
                    values[field_def.name] = None

        # Create ParsedBlock
        parsed = ParsedBlock(
            block_id=block_id,
            name=schema.name,
            values=values,
            raw=data,
            length=len(data),
            protocol_version=protocol_version,
            schema_version=schema.schema_version,
            timestamp=time.time(),
            validation=validation_result,
        )

        # Log warnings if validation failed
        if validation_result and validation_result.warnings:
            for warning in validation_result.warnings:
                logger.debug(f"Block {block_id} ({schema.name}): {warning}")

        return parsed

    def list_schemas(self) -> Dict[int, str]:
        """List all registered schemas.

        Returns:
            Dictionary mapping block_id → schema_name
        """
        return {block_id: schema.name for block_id, schema in self._schemas.items()}
