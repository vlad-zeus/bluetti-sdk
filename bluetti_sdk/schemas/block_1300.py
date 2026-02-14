"""Block 1300 - INV_GRID_INFO Schema (Legacy Import)

DEPRECATED: This module provides backward compatibility only.
Use block_1300_declarative for new code.

Grid input monitoring data.
Tracks grid voltage, frequency, current, and power.
"""

# Import from declarative version (canonical source)
from .block_1300_declarative import BLOCK_1300_DECLARATIVE_SCHEMA as BLOCK_1300_SCHEMA

__all__ = ["BLOCK_1300_SCHEMA"]
