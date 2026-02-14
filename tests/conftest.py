"""Pytest configuration and fixtures.

This module provides test infrastructure including:
- Windows-specific temp directory cleanup handling
- Shared fixtures for integration and unit tests
"""

import gc
import sys

import pytest


@pytest.fixture(autouse=True)
def _cleanup_after_test():
    """Force garbage collection after each test to release file handles.

    On Windows, file handles can remain open longer due to OS behavior,
    causing pytest temp directory cleanup to fail with WinError 5.
    This fixture forces garbage collection to release handles promptly.
    """
    yield
    # Force garbage collection to release any lingering file handles
    gc.collect()
    gc.collect()  # Call twice to handle cyclic references


if sys.platform == "win32":

    @pytest.fixture(scope="session", autouse=True)
    def _windows_temp_cleanup():
        """Additional cleanup handling for Windows platform.

        Windows file locking can prevent pytest from cleaning up temp
        directories. This fixture ensures aggressive cleanup at session end.
        """
        yield
        # Force final garbage collection before pytest temp cleanup
        gc.collect()
        gc.collect()
