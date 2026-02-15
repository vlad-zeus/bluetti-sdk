"""Resilience utilities for retry logic and error handling.

Provides configurable retry policies with exponential backoff.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator


@dataclass(frozen=True)
class RetryPolicy:
    """Configurable retry policy with exponential backoff.

    Defines retry behavior for transient errors:
    - How many attempts to make
    - Initial delay between attempts
    - Backoff factor for exponential growth
    - Maximum delay cap

    Example:
        # Default: 3 attempts, 0.5s initial, 2x backoff, 5s max
        policy = RetryPolicy()

        # Custom: aggressive retry
        policy = RetryPolicy(
            max_attempts=5,
            initial_delay=0.1,
            backoff_factor=1.5,
            max_delay=10.0
        )

    Attributes:
        max_attempts: Total attempts including initial try (minimum 1)
        initial_delay: Delay after first failure in seconds (must be > 0)
        backoff_factor: Multiplier for exponential backoff (must be >= 1.0)
        max_delay: Maximum delay cap in seconds (must be >= initial_delay)
    """

    max_attempts: int = 3
    initial_delay: float = 0.5
    backoff_factor: float = 2.0
    max_delay: float = 5.0

    def __post_init__(self) -> None:
        """Validate retry policy parameters.

        Raises:
            ValueError: If any parameter is invalid
        """
        if self.max_attempts < 1:
            raise ValueError(
                f"max_attempts must be >= 1, got {self.max_attempts}"
            )

        if self.initial_delay <= 0:
            raise ValueError(
                f"initial_delay must be > 0, got {self.initial_delay}"
            )

        if self.backoff_factor < 1.0:
            raise ValueError(
                f"backoff_factor must be >= 1.0, got {self.backoff_factor}"
            )

        if self.max_delay < self.initial_delay:
            raise ValueError(
                f"max_delay ({self.max_delay}) must be >= "
                f"initial_delay ({self.initial_delay})"
            )


def iter_delays(policy: RetryPolicy) -> Iterator[float]:
    """Generate delay sequence with exponential backoff.

    Yields delay values for each retry attempt according to the policy.
    Number of delays = max_attempts - 1 (no delay before first attempt).

    Args:
        policy: Retry policy configuration

    Yields:
        Delay in seconds for each retry (capped by max_delay)

    Raises:
        AssertionError: If policy parameters violate invariants

    Example:
        >>> policy = RetryPolicy(max_attempts=3, initial_delay=1.0, backoff_factor=2.0)
        >>> list(iter_delays(policy))
        [1.0, 2.0]  # 2 delays for 3 total attempts

    Notes:
        Defensive assertions verify policy invariants even though
        RetryPolicy.__post_init__ validates on construction. This prevents
        silent bugs if policy is corrupted or validation is bypassed.
    """
    # Defensive assertions: Verify policy invariants at API boundary
    # These prevent silent bugs from invalid inputs (mocks, manual construction, etc)
    import math

    assert policy.max_attempts >= 1, (
        f"max_attempts must be >= 1, got {policy.max_attempts}"
    )
    assert policy.initial_delay > 0, (
        f"initial_delay must be > 0, got {policy.initial_delay}"
    )
    assert math.isfinite(policy.initial_delay), (
        f"initial_delay must be finite, got {policy.initial_delay}"
    )
    assert policy.backoff_factor >= 1.0, (
        f"backoff_factor must be >= 1.0, got {policy.backoff_factor}"
    )
    assert policy.max_delay >= policy.initial_delay, (
        f"max_delay ({policy.max_delay}) must be >= "
        f"initial_delay ({policy.initial_delay})"
    )

    delay = policy.initial_delay

    # Generate delays for retries (max_attempts - 1)
    for _ in range(policy.max_attempts - 1):
        yield min(delay, policy.max_delay)
        delay *= policy.backoff_factor
