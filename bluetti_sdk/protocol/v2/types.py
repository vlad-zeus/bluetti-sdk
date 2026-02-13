"""V2 protocol types."""

from dataclasses import dataclass
from typing import Any, Dict, Optional, Type, TypeVar

T = TypeVar("T")


@dataclass
class ParsedBlock:
    """Parsed block result.

    This is the CONTRACT between parser and device model.

    Parser outputs this, device model consumes it.
    """

    # Identity
    block_id: int
    name: str

    # Parsed data (flat dict)
    values: Dict[str, Any]

    # Metadata
    raw: bytes = b""
    length: int = 0
    protocol_version: int = 2000
    schema_version: str = "1.0.0"
    timestamp: float = 0.0

    # Validation result
    validation: Optional[Any] = None  # ValidationResult

    def to_dict(self) -> dict:
        """Export for JSON/MQTT.

        Returns:
            Flat dictionary of field values
        """
        return self.values.copy()

    def to_model(self, model_class: Type[T]) -> T:
        """Convert to dataclass.

        Args:
            model_class: Dataclass type to instantiate

        Returns:
            Instance of model_class with values from parsed data

        Example:
            >>> home_data = parsed.to_model(HomeData)
            >>> print(home_data.soc)
        """
        return model_class(**self.values)
