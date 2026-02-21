# Defensive tests for RetryPolicy mutation bypass (post-__post_init__ state corruption).
# Basic constructor validation is covered in test_resilience.py.

import math
from unittest.mock import Mock

import pytest
from power_sdk.utils.resilience import RetryPolicy, iter_delays


def test_iter_delays_defensive_max_attempts():
    """Test iter_delays fails fast if policy.max_attempts is invalid.

    P1 hardening: Even though RetryPolicy.__post_init__ validates,
    defensive assertions prevent silent bugs if:
    - Someone bypasses validation (mock, manual construction)
    - Policy is corrupted after creation
    - API contract is violated by duck-typed object
    """
    # Mock policy with invalid max_attempts
    bad_policy = Mock(spec=RetryPolicy)
    bad_policy.max_attempts = 0
    bad_policy.initial_delay = 1.0
    bad_policy.backoff_factor = 2.0
    bad_policy.max_delay = 5.0

    with pytest.raises(ValueError, match="max_attempts must be >= 1"):
        list(iter_delays(bad_policy))


def test_iter_delays_defensive_initial_delay():
    """Test iter_delays fails fast if policy.initial_delay is invalid."""
    bad_policy = Mock(spec=RetryPolicy)
    bad_policy.max_attempts = 3
    bad_policy.initial_delay = -1.0  # Invalid: negative
    bad_policy.backoff_factor = 2.0
    bad_policy.max_delay = 5.0

    with pytest.raises(ValueError, match="initial_delay must be > 0"):
        list(iter_delays(bad_policy))


def test_iter_delays_defensive_backoff_factor():
    """Test iter_delays fails fast if policy.backoff_factor is invalid."""
    bad_policy = Mock(spec=RetryPolicy)
    bad_policy.max_attempts = 3
    bad_policy.initial_delay = 1.0
    bad_policy.backoff_factor = 0.5  # Invalid: < 1.0
    bad_policy.max_delay = 5.0

    with pytest.raises(ValueError, match=r"backoff_factor must be >= 1\.0"):
        list(iter_delays(bad_policy))


def test_iter_delays_defensive_max_delay():
    """Test iter_delays fails fast if policy.max_delay is invalid."""
    bad_policy = Mock(spec=RetryPolicy)
    bad_policy.max_attempts = 3
    bad_policy.initial_delay = 5.0
    bad_policy.backoff_factor = 2.0
    bad_policy.max_delay = 1.0  # Invalid: < initial_delay

    with pytest.raises(ValueError, match=r"max_delay .* must be >= initial_delay"):
        list(iter_delays(bad_policy))


def test_iter_delays_defensive_infinite_delay():
    """Test iter_delays detects infinite/NaN delays."""
    bad_policy = Mock(spec=RetryPolicy)
    bad_policy.max_attempts = 3
    bad_policy.initial_delay = math.inf  # Invalid: infinite
    bad_policy.backoff_factor = 2.0
    bad_policy.max_delay = math.inf

    with pytest.raises(ValueError, match="initial_delay must be finite"):
        list(iter_delays(bad_policy))


def test_iter_delays_defensive_nan_delay():
    """Test iter_delays detects NaN delays.

    Note: NaN comparisons always return False, so NaN > 0 is False,
    which triggers the > 0 check before the finite check.
    """
    bad_policy = Mock(spec=RetryPolicy)
    bad_policy.max_attempts = 3
    bad_policy.initial_delay = math.nan  # Invalid: NaN
    bad_policy.backoff_factor = 2.0
    bad_policy.max_delay = 5.0

    with pytest.raises(ValueError, match="initial_delay must be finite"):
        list(iter_delays(bad_policy))
