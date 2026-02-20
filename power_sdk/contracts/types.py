"""Core contract types shared across all layers."""

from __future__ import annotations

from dataclasses import dataclass, field
from inspect import signature
from typing import Any, TypeVar

T = TypeVar("T")


@dataclass
class ParsedRecord:
    """Parsed record result — contract between parser and device model.

    Protocol-agnostic DTO. The parser produces it; the device model consumes it.
    """

    # Identity
    block_id: int
    name: str

    # Parsed data (flat dict of field_name → value)
    values: dict[str, Any]

    # Metadata
    raw: bytes = field(default=b"")
    length: int = 0
    protocol_version: int | None = None
    schema_version: str = "1.0.0"
    timestamp: float = 0.0

    # Validation result (ValidationResult or None)
    validation: Any | None = None

    def to_dict(self) -> dict[str, Any]:
        """Export as flat dict (for JSON/MQTT)."""
        return self.values.copy()

    def to_model(self, model_class: type[T]) -> T:
        """Instantiate a dataclass from parsed values.

        Example:
            home = record.to_model(HomeData)
        """
        params = signature(model_class).parameters
        kwargs = {k: v for k, v in self.values.items() if k in params}
        return model_class(**kwargs)
