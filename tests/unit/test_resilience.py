"""Unit tests for resilience utilities."""

import pytest
from bluetti_sdk.utils.resilience import RetryPolicy, iter_delays


def test_retry_policy_defaults():
    """Test RetryPolicy with default values."""
    policy = RetryPolicy()
    assert policy.max_attempts == 3
    assert policy.initial_delay == 0.5
    assert policy.backoff_factor == 2.0
    assert policy.max_delay == 5.0


def test_retry_policy_custom_values():
    """Test RetryPolicy with custom values."""
    policy = RetryPolicy(
        max_attempts=5,
        initial_delay=0.1,
        backoff_factor=1.5,
        max_delay=10.0,
    )
    assert policy.max_attempts == 5
    assert policy.initial_delay == 0.1
    assert policy.backoff_factor == 1.5
    assert policy.max_delay == 10.0


def test_retry_policy_validation_max_attempts():
    """Test validation of max_attempts parameter."""
    with pytest.raises(ValueError, match="max_attempts must be >= 1"):
        RetryPolicy(max_attempts=0)

    with pytest.raises(ValueError, match="max_attempts must be >= 1"):
        RetryPolicy(max_attempts=-1)


def test_retry_policy_validation_initial_delay():
    """Test validation of initial_delay parameter."""
    with pytest.raises(ValueError, match="initial_delay must be > 0"):
        RetryPolicy(initial_delay=0)

    with pytest.raises(ValueError, match="initial_delay must be > 0"):
        RetryPolicy(initial_delay=-0.5)


def test_retry_policy_validation_backoff_factor():
    """Test validation of backoff_factor parameter."""
    with pytest.raises(ValueError, match=r"backoff_factor must be >= 1\.0"):
        RetryPolicy(backoff_factor=0.5)

    with pytest.raises(ValueError, match=r"backoff_factor must be >= 1\.0"):
        RetryPolicy(backoff_factor=0)


def test_retry_policy_validation_max_delay():
    """Test validation of max_delay vs initial_delay."""
    with pytest.raises(
        ValueError, match=r"max_delay .* must be >= initial_delay"
    ):
        RetryPolicy(initial_delay=2.0, max_delay=1.0)


def test_backoff_sequence_capped():
    """Test that exponential backoff sequence is capped by max_delay."""
    policy = RetryPolicy(
        max_attempts=5,
        initial_delay=1.0,
        backoff_factor=2.0,
        max_delay=5.0,
    )

    delays = list(iter_delays(policy))

    # Should have max_attempts - 1 delays
    assert len(delays) == 4

    # Delays: 1.0, 2.0, 4.0, 8.0 -> capped at 5.0
    assert delays[0] == 1.0  # 1.0
    assert delays[1] == 2.0  # 1.0 * 2
    assert delays[2] == 4.0  # 2.0 * 2
    assert delays[3] == 5.0  # 4.0 * 2 = 8.0, capped at 5.0


def test_backoff_sequence_no_cap():
    """Test exponential backoff when max_delay is very high."""
    policy = RetryPolicy(
        max_attempts=4,
        initial_delay=1.0,
        backoff_factor=2.0,
        max_delay=100.0,
    )

    delays = list(iter_delays(policy))

    assert len(delays) == 3
    assert delays[0] == 1.0  # 1.0
    assert delays[1] == 2.0  # 1.0 * 2
    assert delays[2] == 4.0  # 2.0 * 2


def test_iter_delays_single_attempt():
    """Test that single attempt policy yields no delays."""
    policy = RetryPolicy(max_attempts=1)
    delays = list(iter_delays(policy))
    assert len(delays) == 0  # No retries, no delays


def test_iter_delays_linear_backoff():
    """Test delays with backoff_factor=1.0 (linear)."""
    policy = RetryPolicy(
        max_attempts=4,
        initial_delay=1.0,
        backoff_factor=1.0,  # Linear, no growth
        max_delay=10.0,
    )

    delays = list(iter_delays(policy))

    assert len(delays) == 3
    assert all(d == 1.0 for d in delays)  # All delays same


def test_retry_policy_immutable():
    """Test that RetryPolicy is frozen (immutable)."""
    policy = RetryPolicy()

    with pytest.raises(AttributeError):
        policy.max_attempts = 10  # type: ignore

    with pytest.raises(AttributeError):
        policy.initial_delay = 2.0  # type: ignore
