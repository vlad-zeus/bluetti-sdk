"""Tests for P1 edge case: RetryPolicy defensive assertions."""

import math
from unittest.mock import Mock

import pytest
from power_sdk.utils.resilience import RetryPolicy, iter_delays


def test_retry_policy_validates_max_attempts():
    """Test that RetryPolicy rejects invalid max_attempts."""
    with pytest.raises(ValueError, match="max_attempts must be >= 1"):
        RetryPolicy(max_attempts=0)

    with pytest.raises(ValueError, match="max_attempts must be >= 1"):
        RetryPolicy(max_attempts=-1)


def test_retry_policy_validates_initial_delay():
    """Test that RetryPolicy rejects invalid initial_delay."""
    with pytest.raises(ValueError, match="initial_delay must be > 0"):
        RetryPolicy(initial_delay=0.0)

    with pytest.raises(ValueError, match="initial_delay must be > 0"):
        RetryPolicy(initial_delay=-1.0)


def test_retry_policy_validates_backoff_factor():
    """Test that RetryPolicy rejects invalid backoff_factor."""
    with pytest.raises(ValueError, match=r"backoff_factor must be >= 1\.0"):
        RetryPolicy(backoff_factor=0.9)

    with pytest.raises(ValueError, match=r"backoff_factor must be >= 1\.0"):
        RetryPolicy(backoff_factor=0.0)


def test_retry_policy_validates_max_delay():
    """Test that RetryPolicy rejects max_delay < initial_delay."""
    with pytest.raises(ValueError, match=r"max_delay .* must be >="):
        RetryPolicy(initial_delay=5.0, max_delay=1.0)


def test_iter_delays_with_valid_policy():
    """Test iter_delays with valid policy generates correct sequence."""
    policy = RetryPolicy(
        max_attempts=3, initial_delay=1.0, backoff_factor=2.0, max_delay=10.0
    )

    delays = list(iter_delays(policy))

    # 3 attempts = 2 delays (no delay before first attempt)
    assert len(delays) == 2
    assert delays[0] == 1.0
    assert delays[1] == 2.0


def test_iter_delays_respects_max_delay_cap():
    """Test iter_delays caps delays at max_delay."""
    policy = RetryPolicy(
        max_attempts=5, initial_delay=1.0, backoff_factor=2.0, max_delay=3.0
    )

    delays = list(iter_delays(policy))

    # Sequence without cap: [1.0, 2.0, 4.0, 8.0]
    # With cap of 3.0:      [1.0, 2.0, 3.0, 3.0]
    assert len(delays) == 4
    assert delays == [1.0, 2.0, 3.0, 3.0]


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

    # Should raise assertion error, not infinite loop or negative range
    with pytest.raises(AssertionError, match="max_attempts must be >= 1"):
        list(iter_delays(bad_policy))


def test_iter_delays_defensive_initial_delay():
    """Test iter_delays fails fast if policy.initial_delay is invalid."""
    bad_policy = Mock(spec=RetryPolicy)
    bad_policy.max_attempts = 3
    bad_policy.initial_delay = -1.0  # Invalid: negative
    bad_policy.backoff_factor = 2.0
    bad_policy.max_delay = 5.0

    with pytest.raises(AssertionError, match="initial_delay must be > 0"):
        list(iter_delays(bad_policy))


def test_iter_delays_defensive_backoff_factor():
    """Test iter_delays fails fast if policy.backoff_factor is invalid."""
    bad_policy = Mock(spec=RetryPolicy)
    bad_policy.max_attempts = 3
    bad_policy.initial_delay = 1.0
    bad_policy.backoff_factor = 0.5  # Invalid: < 1.0
    bad_policy.max_delay = 5.0

    with pytest.raises(AssertionError, match=r"backoff_factor must be >= 1\.0"):
        list(iter_delays(bad_policy))


def test_iter_delays_defensive_max_delay():
    """Test iter_delays fails fast if policy.max_delay is invalid."""
    bad_policy = Mock(spec=RetryPolicy)
    bad_policy.max_attempts = 3
    bad_policy.initial_delay = 5.0
    bad_policy.backoff_factor = 2.0
    bad_policy.max_delay = 1.0  # Invalid: < initial_delay

    with pytest.raises(AssertionError, match=r"max_delay .* must be >= initial_delay"):
        list(iter_delays(bad_policy))


def test_iter_delays_defensive_infinite_delay():
    """Test iter_delays detects infinite/NaN delays."""
    bad_policy = Mock(spec=RetryPolicy)
    bad_policy.max_attempts = 3
    bad_policy.initial_delay = math.inf  # Invalid: infinite
    bad_policy.backoff_factor = 2.0
    bad_policy.max_delay = math.inf

    with pytest.raises(AssertionError, match="initial_delay must be finite"):
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

    # NaN fails the > 0 check (NaN > 0 == False)
    with pytest.raises(AssertionError, match="initial_delay must be > 0"):
        list(iter_delays(bad_policy))
