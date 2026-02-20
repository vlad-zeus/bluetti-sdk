"""Shared test helpers — plain functions, not fixtures.

Import directly in test modules::

    from tests.helpers import make_parsed_block
"""

from power_sdk.contracts.types import ParsedRecord


def make_parsed_block(block_id: int, **overrides: object) -> ParsedRecord:
    """Create a minimal ParsedRecord stub for unit tests."""
    defaults: dict = dict(
        block_id=block_id,
        name=f"BLOCK_{block_id}",
        values={"ok": True},
        raw=b"",
        length=0,
        protocol_version=None,
        schema_version="1.0.0",
        timestamp=0.0,
    )
    defaults.update(overrides)
    return ParsedRecord(**defaults)
