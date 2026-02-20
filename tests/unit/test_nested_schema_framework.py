"""Unit tests for the nested declarative schema framework.

Tests cover:
- FieldGroup: offset/size/parse behavior
- NestedGroupSpec + nested_group(): declarative creation
- _generate_schema(): collects nested groups from class attributes
- V2Parser: parses FieldGroup into sub-dict in values
- Backward compatibility: existing flat schemas unchanged
"""

from power_sdk.plugins.bluetti.v2.protocol.datatypes import UInt8, UInt16
from power_sdk.plugins.bluetti.v2.protocol.parser import V2Parser
from power_sdk.plugins.bluetti.v2.protocol.schema import Field, FieldGroup
from power_sdk.plugins.bluetti.v2.schemas import block_field, block_schema, nested_group
from power_sdk.plugins.bluetti.v2.schemas.declarative import NestedGroupSpec

# ---------------------------------------------------------------------------
# FieldGroup unit tests
# ---------------------------------------------------------------------------


class TestFieldGroup:
    """Tests for FieldGroup behavior."""

    def test_empty_group_offset_and_size(self):
        group = FieldGroup(name="empty", fields=())
        assert group.offset == 0
        assert group.size() == 0

    def test_single_field_group_offset(self):
        f = Field("val", offset=10, type=UInt16())
        group = FieldGroup(name="g", fields=(f,))
        assert group.offset == 10

    def test_single_field_group_size(self):
        f = Field("val", offset=10, type=UInt16())
        group = FieldGroup(name="g", fields=(f,))
        assert group.size() == 2  # UInt16 = 2 bytes

    def test_multi_field_group_offset_is_minimum(self):
        f1 = Field("a", offset=20, type=UInt16())
        f2 = Field("b", offset=10, type=UInt8())
        group = FieldGroup(name="g", fields=(f1, f2))
        assert group.offset == 10

    def test_multi_field_group_size_spans_all_fields(self):
        f1 = Field("a", offset=10, type=UInt8())  # ends at 11
        f2 = Field("b", offset=20, type=UInt16())  # ends at 22
        group = FieldGroup(name="g", fields=(f1, f2))
        # size = max_end - min_offset = 22 - 10 = 12
        assert group.size() == 12

    def test_parse_returns_dict(self):
        data = bytes(200)
        f = Field("x", offset=10, type=UInt16())
        group = FieldGroup(name="grp", fields=(f,))
        result = group.parse(data)
        assert isinstance(result, dict)
        assert "x" in result

    def test_parse_reads_correct_offset(self):
        data = bytearray(200)
        data[10] = 0x00
        data[11] = 0x2A  # 42 as big-endian UInt16
        f = Field("value", offset=10, type=UInt16())
        group = FieldGroup(name="g", fields=(f,))
        result = group.parse(bytes(data))
        assert result["value"] == 42

    def test_parse_returns_none_for_out_of_bounds_field(self):
        data = bytes(10)  # Only 10 bytes
        f = Field("big", offset=8, type=UInt16())  # needs bytes 8-9, ok
        f_oob = Field("oob", offset=9, type=UInt16())  # needs bytes 9-10, out of bounds
        group = FieldGroup(name="g", fields=(f, f_oob))
        result = group.parse(data)
        assert result["big"] == 0
        assert result["oob"] is None

    def test_parse_applies_transforms(self):
        data = bytearray(10)
        data[0] = 0x00
        data[1] = 0x07  # 7 as big-endian UInt16
        f = Field("masked", offset=0, type=UInt16(), transform=("bitmask:0x3",))
        group = FieldGroup(name="g", fields=(f,))
        result = group.parse(bytes(data))
        assert result["masked"] == 7 & 0x3  # = 3

    def test_name_is_group_key(self):
        group = FieldGroup(name="config_grid", fields=())
        assert group.name == "config_grid"

    def test_fields_immutable_tuple(self):
        f = Field("x", offset=0, type=UInt8())
        group = FieldGroup(name="g", fields=[f])  # pass list, should become tuple
        assert isinstance(group.fields, tuple)

    def test_evidence_status_stored(self):
        group = FieldGroup(
            name="g",
            fields=(),
            evidence_status="verified_reference",
        )
        assert group.evidence_status == "verified_reference"


# ---------------------------------------------------------------------------
# nested_group() function tests
# ---------------------------------------------------------------------------


class TestNestedGroupFunction:
    """Tests for nested_group() factory function."""

    def test_returns_nested_group_spec(self):
        spec = nested_group("test", sub_fields=[])
        assert isinstance(spec, NestedGroupSpec)

    def test_name_stored(self):
        spec = nested_group("my_group", sub_fields=[])
        assert spec.name == "my_group"

    def test_sub_fields_stored_as_tuple(self):
        f = Field("x", offset=0, type=UInt8())
        spec = nested_group("g", sub_fields=[f])
        assert isinstance(spec.sub_fields, tuple)
        assert len(spec.sub_fields) == 1

    def test_defaults(self):
        spec = nested_group("g", sub_fields=[])
        assert spec.required is False
        assert spec.description is None
        assert spec.evidence_status is None

    def test_optional_params(self):
        spec = nested_group(
            "g",
            sub_fields=[],
            required=True,
            description="Test group",
            evidence_status="partial",
        )
        assert spec.required is True
        assert spec.description == "Test group"
        assert spec.evidence_status == "partial"


# ---------------------------------------------------------------------------
# _generate_schema() nested group collection tests
# ---------------------------------------------------------------------------


class TestGenerateSchemaWithNestedGroups:
    """Tests for _generate_schema() collecting nested groups."""

    def test_flat_schema_unchanged(self):
        """Flat schemas with only block_field() still work identically."""
        from dataclasses import dataclass

        @block_schema(block_id=99999, name="FLAT_TEST")
        @dataclass
        class FlatBlock:
            value: int = block_field(offset=0, type=UInt16())

        schema = FlatBlock.to_schema()
        assert len(schema.fields) == 1
        assert schema.fields[0].name == "value"

    def test_nested_group_added_to_schema_fields(self):
        """nested_group() class attributes become FieldGroup in schema.fields."""
        from dataclasses import dataclass

        @block_schema(block_id=99998, name="NESTED_TEST")
        @dataclass
        class NestedBlock:
            my_group = nested_group(
                "my_group",
                sub_fields=[Field("x", offset=10, type=UInt8())],
            )

        schema = NestedBlock.to_schema()
        group_fields = [f for f in schema.fields if isinstance(f, FieldGroup)]
        assert len(group_fields) == 1
        assert group_fields[0].name == "my_group"

    def test_mixed_flat_and_nested_fields(self):
        """Schema with both block_field and nested_group has both in fields."""
        from dataclasses import dataclass

        @block_schema(block_id=99997, name="MIXED_TEST")
        @dataclass
        class MixedBlock:
            flat_val: int = block_field(offset=0, type=UInt8())
            group_a = nested_group(
                "group_a",
                sub_fields=[Field("sub", offset=4, type=UInt16())],
            )

        schema = MixedBlock.to_schema()
        names = {f.name for f in schema.fields}
        assert "flat_val" in names
        assert "group_a" in names

    def test_multiple_nested_groups_collected(self):
        """All nested_group() class attributes are collected."""
        from dataclasses import dataclass

        @block_schema(block_id=99996, name="MULTI_NESTED_TEST")
        @dataclass
        class MultiNestedBlock:
            g1 = nested_group("g1", sub_fields=[])
            g2 = nested_group("g2", sub_fields=[])
            g3 = nested_group("g3", sub_fields=[])

        schema = MultiNestedBlock.to_schema()
        group_names = {f.name for f in schema.fields if isinstance(f, FieldGroup)}
        assert "g1" in group_names
        assert "g2" in group_names
        assert "g3" in group_names

    def test_nested_group_preserves_evidence_status(self):
        """evidence_status propagates from nested_group() to FieldGroup."""
        from dataclasses import dataclass

        @block_schema(block_id=99995, name="EVIDENCE_TEST")
        @dataclass
        class EvidenceBlock:
            g = nested_group(
                "g",
                sub_fields=[],
                evidence_status="verified_reference",
            )

        schema = EvidenceBlock.to_schema()
        group = next(f for f in schema.fields if isinstance(f, FieldGroup))
        assert group.evidence_status == "verified_reference"


# ---------------------------------------------------------------------------
# V2Parser integration tests for FieldGroup
# ---------------------------------------------------------------------------


class TestParserWithFieldGroup:
    """Tests for V2Parser handling FieldGroup in parse_block()."""

    def _make_schema(self, block_id, name, field_group):
        """Create a minimal BlockSchema containing a FieldGroup."""
        from power_sdk.plugins.bluetti.v2.protocol.schema import BlockSchema

        return BlockSchema(
            block_id=block_id,
            name=name,
            description="Test schema",
            min_length=10,
            fields=[field_group],
            strict=False,
        )

    def test_parser_produces_sub_dict_for_field_group(self):
        data = bytearray(200)
        data[10] = 0x00
        data[11] = 0x05  # 5 as UInt16 at offset 10

        group = FieldGroup(
            name="my_group",
            fields=(Field("val", offset=10, type=UInt16()),),
        )
        schema = self._make_schema(88880, "TEST", group)

        parser = V2Parser()
        parser.register_schema(schema)
        parsed = parser.parse_block(88880, bytes(data))

        assert "my_group" in parsed.values
        assert isinstance(parsed.values["my_group"], dict)
        assert parsed.values["my_group"]["val"] == 5

    def test_parser_handles_empty_field_group(self):
        data = bytes(20)
        group = FieldGroup(name="empty", fields=())
        schema = self._make_schema(88879, "EMPTY_GRP", group)

        parser = V2Parser()
        parser.register_schema(schema)
        parsed = parser.parse_block(88879, data)

        assert "empty" in parsed.values
        assert parsed.values["empty"] == {}

    def test_parser_handles_multiple_field_groups(self):
        data = bytearray(200)
        data[0] = 42  # UInt8 at offset 0
        data[10] = 0x01  # UInt8 at offset 10

        from power_sdk.plugins.bluetti.v2.protocol.schema import BlockSchema

        schema = BlockSchema(
            block_id=88878,
            name="MULTI_GRP",
            description="test",
            min_length=20,
            fields=[
                FieldGroup(
                    name="grp_a",
                    fields=(Field("x", offset=0, type=UInt8()),),
                ),
                FieldGroup(
                    name="grp_b",
                    fields=(Field("y", offset=10, type=UInt8()),),
                ),
            ],
            strict=False,
        )

        parser = V2Parser()
        parser.register_schema(schema)
        parsed = parser.parse_block(88878, bytes(data))

        assert parsed.values["grp_a"]["x"] == 42
        assert parsed.values["grp_b"]["y"] == 1

    def test_parser_null_for_oob_sub_fields(self):
        data = bytes(5)  # Only 5 bytes
        group = FieldGroup(
            name="g",
            fields=(Field("far", offset=100, type=UInt8()),),
        )
        schema = self._make_schema(88877, "OOB", group)

        parser = V2Parser()
        parser.register_schema(schema)
        parsed = parser.parse_block(88877, data)

        assert parsed.values["g"]["far"] is None

    def test_flat_field_and_group_coexist_in_parsed_values(self):
        from power_sdk.plugins.bluetti.v2.protocol.schema import BlockSchema

        data = bytearray(200)
        data[0] = 99  # flat field
        data[10] = 55  # group sub-field

        schema = BlockSchema(
            block_id=88876,
            name="COEXIST",
            description="test",
            min_length=20,
            fields=[
                Field("flat", offset=0, type=UInt8()),
                FieldGroup(
                    name="nested",
                    fields=(Field("sub", offset=10, type=UInt8()),),
                ),
            ],
            strict=False,
        )

        parser = V2Parser()
        parser.register_schema(schema)
        parsed = parser.parse_block(88876, bytes(data))

        assert parsed.values["flat"] == 99
        assert parsed.values["nested"]["sub"] == 55


# ---------------------------------------------------------------------------
# Backward compatibility: existing flat schemas unchanged
# ---------------------------------------------------------------------------


class TestBackwardCompatibility:
    """Verify existing flat schemas are completely unchanged."""

    def test_block_100_schema_unaffected(self):
        """Block 100 (APP_HOME_DATA) schema fields are unchanged."""
        from power_sdk.plugins.bluetti.v2.schemas import BLOCK_100_SCHEMA

        # Should have all its flat fields, no FieldGroup
        assert BLOCK_100_SCHEMA.block_id == 100
        for f in BLOCK_100_SCHEMA.fields:
            assert not isinstance(f, FieldGroup)

    def test_block_1300_schema_unaffected(self):
        """Block 1300 (GRID_INFO) schema fields are unchanged."""
        from power_sdk.plugins.bluetti.v2.schemas import BLOCK_1300_SCHEMA

        assert BLOCK_1300_SCHEMA.block_id == 1300
        for f in BLOCK_1300_SCHEMA.fields:
            assert not isinstance(f, FieldGroup)

    def test_block_6000_schema_unaffected(self):
        """Block 6000 (BATTERY_PACK) schema fields are unchanged."""
        from power_sdk.plugins.bluetti.v2.schemas import BLOCK_6000_SCHEMA

        assert BLOCK_6000_SCHEMA.block_id == 6000
        for f in BLOCK_6000_SCHEMA.fields:
            assert not isinstance(f, FieldGroup)

    def test_parser_still_handles_flat_fields(self):
        """Existing flat-schema parse behavior is unchanged."""
        from power_sdk.plugins.bluetti.v2.protocol.schema import BlockSchema

        data = bytearray(10)
        data[0] = 77

        schema = BlockSchema(
            block_id=88875,
            name="FLAT_COMPAT",
            description="compat test",
            min_length=2,
            fields=[Field("val", offset=0, type=UInt8())],
            strict=False,
        )

        parser = V2Parser()
        parser.register_schema(schema)
        parsed = parser.parse_block(88875, bytes(data))

        assert parsed.values["val"] == 77

