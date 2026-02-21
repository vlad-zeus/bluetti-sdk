"""Parser contract conformance tests.

Any class that claims to implement ParserInterface must pass these tests.
Run with: pytest tests/conformance/test_parser_conformance.py
"""

from __future__ import annotations

from collections.abc import Callable

import pytest
from power_sdk.contracts.parser import ParserInterface
from power_sdk.contracts.types import ParsedRecord

# ---------------------------------------------------------------------------
# Minimal schema helper — builds the simplest possible BlockSchema
# that V2Parser can register and parse.
# ---------------------------------------------------------------------------


def _make_minimal_schema() -> object:
    """Build a minimal BlockSchema for block_id=9999."""
    from power_sdk.plugins.bluetti.v2.protocol.schema import BlockSchema

    return BlockSchema(
        block_id=9999,
        name="CONFORMANCE_TEST",
        description="Conformance test block",
        min_length=0,
        protocol_version=2000,
        strict=False,
        fields=[],
    )


# ---------------------------------------------------------------------------
# Build a V2Parser instance with one registered schema
# ---------------------------------------------------------------------------


def make_v2_parser() -> ParserInterface:
    from power_sdk.plugins.bluetti.v2.protocol.parser import V2Parser

    parser = V2Parser()
    parser.register_schema(_make_minimal_schema())
    return parser


PARSER_FACTORIES: list[tuple[str, Callable[[], ParserInterface]]] = [
    ("v2_parser", make_v2_parser),
]


@pytest.fixture(params=[name for name, _ in PARSER_FACTORIES])
def parser(request: pytest.FixtureRequest) -> ParserInterface:
    factory_map = dict(PARSER_FACTORIES)
    return factory_map[request.param]()


REGISTERED_BLOCK_ID = 9999
UNREGISTERED_BLOCK_ID = 8888


# ---------------------------------------------------------------------------
# Conformance tests
# ---------------------------------------------------------------------------


class TestParserConformance:
    """Parameterized conformance suite for ParserInterface implementations."""

    def test_implements_interface(self, parser: ParserInterface) -> None:
        assert isinstance(parser, ParserInterface)

    def test_get_schema_unknown_returns_none(self, parser: ParserInterface) -> None:
        """get_schema() must return None for unregistered block IDs."""
        assert parser.get_schema(UNREGISTERED_BLOCK_ID) is None

    def test_get_schema_known_returns_schema(self, parser: ParserInterface) -> None:
        """get_schema() must return the schema for a registered block ID."""
        schema = parser.get_schema(REGISTERED_BLOCK_ID)
        assert schema is not None

    def test_list_schemas_includes_registered(self, parser: ParserInterface) -> None:
        """list_schemas() must include the registered block ID."""
        schemas = parser.list_schemas()
        assert isinstance(schemas, dict)
        assert REGISTERED_BLOCK_ID in schemas

    def test_list_schemas_maps_id_to_name(self, parser: ParserInterface) -> None:
        """list_schemas() values must be non-empty strings."""
        schemas = parser.list_schemas()
        for block_id, name in schemas.items():
            assert isinstance(block_id, int)
            assert isinstance(name, str) and name

    def test_parse_block_returns_parsed_record(self, parser: ParserInterface) -> None:
        """parse_block() must return a ParsedRecord."""
        result = parser.parse_block(REGISTERED_BLOCK_ID, b"", validate=False)
        assert isinstance(result, ParsedRecord)

    def test_parse_block_block_id_matches(self, parser: ParserInterface) -> None:
        """ParsedRecord.block_id must match the requested block_id."""
        result = parser.parse_block(REGISTERED_BLOCK_ID, b"", validate=False)
        assert result.block_id == REGISTERED_BLOCK_ID

    def test_parse_block_name_is_string(self, parser: ParserInterface) -> None:
        """ParsedRecord.name must be a non-empty string."""
        result = parser.parse_block(REGISTERED_BLOCK_ID, b"", validate=False)
        assert isinstance(result.name, str) and result.name

    def test_parse_block_values_is_dict(self, parser: ParserInterface) -> None:
        """ParsedRecord.values must be a dict."""
        result = parser.parse_block(REGISTERED_BLOCK_ID, b"", validate=False)
        assert isinstance(result.values, dict)

    def test_parse_block_protocol_version_is_int_or_none(
        self, parser: ParserInterface
    ) -> None:
        """ParsedRecord.protocol_version must be int or None."""
        result = parser.parse_block(REGISTERED_BLOCK_ID, b"", validate=False)
        assert result.protocol_version is None or isinstance(
            result.protocol_version, int
        )

    def test_parse_block_unregistered_raises_value_error(
        self, parser: ParserInterface
    ) -> None:
        """parse_block() raises ParserError/ValueError/KeyError for unknown blocks."""
        from power_sdk.errors import ParserError

        with pytest.raises((ParserError, ValueError, KeyError)):
            parser.parse_block(UNREGISTERED_BLOCK_ID, b"\x00" * 4, validate=False)

    def test_parse_block_with_protocol_version_none(
        self, parser: ParserInterface
    ) -> None:
        """parse_block() must accept protocol_version=None."""
        result = parser.parse_block(
            REGISTERED_BLOCK_ID, b"", validate=False, protocol_version=None
        )
        assert isinstance(result, ParsedRecord)

    def test_parse_block_with_explicit_protocol_version(
        self, parser: ParserInterface
    ) -> None:
        """parse_block() must accept an explicit protocol_version int."""
        result = parser.parse_block(
            REGISTERED_BLOCK_ID, b"", validate=False, protocol_version=2000
        )
        assert isinstance(result, ParsedRecord)

    def test_register_schema_same_name_is_idempotent(
        self, parser: ParserInterface
    ) -> None:
        """Re-registering same block_id + same name must be a no-op."""
        schema = _make_minimal_schema()
        parser.register_schema(schema)  # already registered in fixture — must not raise

    def test_register_schema_conflict_raises(self, parser: ParserInterface) -> None:
        """Registering same block_id with a different name must raise ValueError."""
        from power_sdk.plugins.bluetti.v2.protocol.schema import BlockSchema

        conflicting = BlockSchema(
            block_id=REGISTERED_BLOCK_ID,
            name="DIFFERENT_NAME",
            description="Conflict",
            min_length=0,
            fields=[],
        )
        with pytest.raises((ValueError, KeyError)):
            parser.register_schema(conflicting)
