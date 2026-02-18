"""Client service modules (internal orchestration).

This package contains internal service modules that handle specific
orchestration concerns extracted from Client to reduce complexity.

Services:
    - GroupReader: Group-level block read orchestration
"""

from .group_reader import GroupReader

__all__ = ["GroupReader"]

