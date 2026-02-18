"""Schema factory functions for generating parameterized schemas.

This package contains factory functions that reduce code duplication
by generating multiple similar schemas from a single template.
"""

from .epad_liquid import build_epad_liquid_schema

__all__ = [
    "build_epad_liquid_schema",
]
