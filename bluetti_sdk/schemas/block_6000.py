"""Block 6000 - PACK_MAIN_INFO Schema (Legacy Import)

DEPRECATED: This module provides backward compatibility only.
Use block_6000_declarative for new code.

Battery pack main information and status.
Detailed battery health, temperature, and protection status.
"""

# Import from declarative version (canonical source)
from .block_6000_declarative import BLOCK_6000_DECLARATIVE_SCHEMA as BLOCK_6000_SCHEMA

__all__ = ["BLOCK_6000_SCHEMA"]
