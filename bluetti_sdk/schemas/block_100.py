"""Block 100 - APP_HOME_DATA Schema (Legacy Import)

DEPRECATED: This module provides backward compatibility only.
Use block_100_declarative for new code.

Main dashboard data for Elite V2 devices.
Primary data source for monitoring power flows, SOC, and energy totals.
"""

# Import from declarative version (canonical source)
from .block_100_declarative import BLOCK_100_DECLARATIVE_SCHEMA as BLOCK_100_SCHEMA

__all__ = ["BLOCK_100_SCHEMA"]
