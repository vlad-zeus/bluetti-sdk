"""Schema contract for the parser layer."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class SchemaProtocol(Protocol):
    """Minimum interface a block schema must satisfy.

    Any object that exposes these attributes can be registered with a
    ``ParserInterface`` implementation.  The protocol is intentionally
    narrow — it captures only the properties the parser needs to operate,
    not the full ``BlockSchema`` data model.

    Attributes:
        block_id:       Unique integer identifier for this block.
        name:           Human-readable block name (e.g. "APP_HOME_DATA").
        min_length:     Minimum byte length of a valid payload for this block.
        max_field_end:  Byte offset past the last field, or ``None`` when not
                        applicable (e.g. variable-length blocks).
    """

    block_id: int
    name: str
    min_length: int
    max_field_end: int | None
