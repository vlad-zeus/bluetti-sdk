"""Unit tests for Block 17400 (AT1_SETTINGS) nested schema model.

Tests verify:
- Contract: block_id, name, min_length, verification_status
- Nested groups present: 7x AT1BaseConfigItem + simple_end_fields
- Evidence-accurate structure: only proven fields modeled
- Deferred fields documented (not in schema)
- Parser: nested dict produced for each group
"""

from bluetti_sdk.protocol.v2.schema import FieldGroup
from bluetti_sdk.schemas import BLOCK_17400_SCHEMA


class TestBlock17400Contract:
    """Basic schema contract verification."""

    def test_block_id(self):
        assert BLOCK_17400_SCHEMA.block_id == 17400

    def test_name(self):
        assert BLOCK_17400_SCHEMA.name == "ATS_EVENT_EXT"

    def test_min_length(self):
        assert BLOCK_17400_SCHEMA.min_length == 91

    def test_protocol_version(self):
        assert BLOCK_17400_SCHEMA.protocol_version == 2000

    def test_strict_false(self):
        assert BLOCK_17400_SCHEMA.strict is False

    def test_verification_status_partial(self):
        """Status remains partial until device validation gate."""
        assert BLOCK_17400_SCHEMA.verification_status == "partial"


class TestBlock17400NestedGroups:
    """Verify all 8 expected nested groups are present."""

    def _groups(self):
        return {
            f.name: f
            for f in BLOCK_17400_SCHEMA.fields
            if isinstance(f, FieldGroup)
        }

    def test_all_eight_groups_present(self):
        groups = self._groups()
        expected = {
            "config_grid",
            "config_sl1",
            "config_sl2",
            "config_sl3",
            "config_sl4",
            "config_pcs1",
            "config_pcs2",
            "simple_end_fields",
        }
        assert expected == set(groups.keys()), (
            f"Expected groups {expected}, got {set(groups.keys())}"
        )

    def test_no_flat_fields(self):
        """Block 17400 uses only nested groups (no flat block_field entries)."""
        from bluetti_sdk.protocol.v2.schema import Field
        flat = [
            f for f in BLOCK_17400_SCHEMA.fields
            if isinstance(f, Field)
        ]
        assert flat == [], f"Expected no flat fields, got: {[f.name for f in flat]}"

    def test_schema_has_eight_total_fields(self):
        """Schema has exactly 8 FieldGroup entries."""
        assert len(BLOCK_17400_SCHEMA.fields) == 8

    def test_config_grid_evidence_status_partial(self):
        groups = self._groups()
        assert groups["config_grid"].evidence_status == "partial"

    def test_config_sl1_evidence_status_partial(self):
        groups = self._groups()
        assert groups["config_sl1"].evidence_status == "partial"

    def test_simple_end_fields_evidence_status_smali_verified(self):
        """simple_end_fields group is smali_verified (all proven transforms)."""
        groups = self._groups()
        assert groups["simple_end_fields"].evidence_status == "smali_verified"

    def test_all_groups_not_required(self):
        """All groups are required=False (conditional on packet size)."""
        for group in BLOCK_17400_SCHEMA.fields:
            assert group.required is False, (
                f"Group '{group.name}' should have required=False"
            )


class TestBlock17400ConfigGrid:
    """Verify config_grid proven sub-fields."""

    def _config_grid(self):
        return next(
            f for f in BLOCK_17400_SCHEMA.fields
            if isinstance(f, FieldGroup) and f.name == "config_grid"
        )

    def test_config_grid_has_max_current(self):
        group = self._config_grid()
        names = {f.name for f in group.fields}
        assert "max_current" in names

    def test_config_grid_max_current_offset(self):
        """max_current at byte 84 (data[84-85], smali line 2578)."""
        group = self._config_grid()
        f = next(f for f in group.fields if f.name == "max_current")
        assert f.offset == 84

    def test_config_grid_max_current_not_required(self):
        group = self._config_grid()
        f = next(f for f in group.fields if f.name == "max_current")
        assert f.required is False

    def test_config_grid_max_current_type_uint16(self):
        from bluetti_sdk.protocol.v2.datatypes import UInt16
        group = self._config_grid()
        f = next(f for f in group.fields if f.name == "max_current")
        assert isinstance(f.type, UInt16)

    def test_config_grid_has_smali_reference_in_description(self):
        group = self._config_grid()
        f = next(f for f in group.fields if f.name == "max_current")
        assert "smali" in f.description.lower()


class TestBlock17400ConfigSL1:
    """Verify config_sl1 proven sub-fields."""

    def _config_sl1(self):
        return next(
            f for f in BLOCK_17400_SCHEMA.fields
            if isinstance(f, FieldGroup) and f.name == "config_sl1"
        )

    def test_config_sl1_has_max_current(self):
        group = self._config_sl1()
        names = {f.name for f in group.fields}
        assert "max_current" in names

    def test_config_sl1_max_current_offset(self):
        """max_current at byte 86 (data[86-87], smali lines 2744-2746)."""
        group = self._config_sl1()
        f = next(f for f in group.fields if f.name == "max_current")
        assert f.offset == 86

    def test_config_sl1_max_current_type_uint16(self):
        from bluetti_sdk.protocol.v2.datatypes import UInt16
        group = self._config_sl1()
        f = next(f for f in group.fields if f.name == "max_current")
        assert isinstance(f.type, UInt16)


class TestBlock17400DeferredGroups:
    """Verify deferred groups (no proven sub-fields yet)."""

    def _groups(self):
        return {
            f.name: f
            for f in BLOCK_17400_SCHEMA.fields
            if isinstance(f, FieldGroup)
        }

    def test_config_sl2_has_no_sub_fields(self):
        """SL2 max_current offset not proven - deferred."""
        groups = self._groups()
        assert len(groups["config_sl2"].fields) == 0

    def test_config_sl3_has_no_sub_fields(self):
        groups = self._groups()
        assert len(groups["config_sl3"].fields) == 0

    def test_config_sl4_has_no_sub_fields(self):
        groups = self._groups()
        assert len(groups["config_sl4"].fields) == 0

    def test_config_pcs1_has_no_sub_fields(self):
        groups = self._groups()
        assert len(groups["config_pcs1"].fields) == 0

    def test_config_pcs2_has_no_sub_fields(self):
        groups = self._groups()
        assert len(groups["config_pcs2"].fields) == 0


class TestBlock17400SimpleEndFields:
    """Verify simple_end_fields group (5 smali-proven fields)."""

    def _end_fields_group(self):
        return next(
            f for f in BLOCK_17400_SCHEMA.fields
            if isinstance(f, FieldGroup) and f.name == "simple_end_fields"
        )

    def test_five_sub_fields(self):
        group = self._end_fields_group()
        assert len(group.fields) == 5

    def test_volt_level_set_present(self):
        group = self._end_fields_group()
        names = {f.name for f in group.fields}
        assert "volt_level_set" in names

    def test_ac_supply_phase_num_present(self):
        group = self._end_fields_group()
        names = {f.name for f in group.fields}
        assert "ac_supply_phase_num" in names

    def test_soc_gen_auto_stop_present(self):
        group = self._end_fields_group()
        names = {f.name for f in group.fields}
        assert "soc_gen_auto_stop" in names

    def test_soc_gen_auto_start_present(self):
        group = self._end_fields_group()
        names = {f.name for f in group.fields}
        assert "soc_gen_auto_start" in names

    def test_soc_black_start_present(self):
        group = self._end_fields_group()
        names = {f.name for f in group.fields}
        assert "soc_black_start" in names

    def test_volt_level_set_offset(self):
        """volt_level_set at byte 176 (smali: lines 3525-3567)."""
        group = self._end_fields_group()
        f = next(f for f in group.fields if f.name == "volt_level_set")
        assert f.offset == 176

    def test_ac_supply_phase_num_offset(self):
        """ac_supply_phase_num at byte 176 (same word, different bits)."""
        group = self._end_fields_group()
        f = next(f for f in group.fields if f.name == "ac_supply_phase_num")
        assert f.offset == 176

    def test_soc_gen_auto_stop_offset(self):
        """soc_gen_auto_stop at byte 178 (smali: lines 3580-3605)."""
        group = self._end_fields_group()
        f = next(f for f in group.fields if f.name == "soc_gen_auto_stop")
        assert f.offset == 178

    def test_soc_gen_auto_start_offset(self):
        """soc_gen_auto_start at byte 179 (smali: lines 3607-3626)."""
        group = self._end_fields_group()
        f = next(f for f in group.fields if f.name == "soc_gen_auto_start")
        assert f.offset == 179

    def test_soc_black_start_offset(self):
        """soc_black_start at byte 181 (smali: lines 3628-3645)."""
        group = self._end_fields_group()
        f = next(f for f in group.fields if f.name == "soc_black_start")
        assert f.offset == 181

    def test_volt_level_set_has_bitmask_transform(self):
        """volt_level_set uses bitmask:0x7 (AND 0x7)."""
        group = self._end_fields_group()
        f = next(f for f in group.fields if f.name == "volt_level_set")
        assert f.transform is not None
        assert "bitmask:0x7" in f.transform

    def test_ac_supply_phase_num_has_shift_and_bitmask(self):
        """ac_supply_phase_num uses shift:3 + bitmask:0x7 (SHR 3, AND 0x7)."""
        group = self._end_fields_group()
        f = next(f for f in group.fields if f.name == "ac_supply_phase_num")
        assert f.transform is not None
        assert "shift:3" in f.transform
        assert "bitmask:0x7" in f.transform

    def test_soc_gen_auto_stop_has_clamp_transform(self):
        """soc_gen_auto_stop uses clamp:0:100 (min(100) equivalent)."""
        group = self._end_fields_group()
        f = next(f for f in group.fields if f.name == "soc_gen_auto_stop")
        assert f.transform is not None
        assert "clamp:0:100" in f.transform


class TestBlock17400ParserIntegration:
    """Test that V2Parser produces nested dicts for Block 17400 groups."""

    def _build_data(self, size=200):
        return bytearray(size)

    def _make_parser(self):
        from bluetti_sdk.protocol.v2.parser import V2Parser

        parser = V2Parser()
        parser.register_schema(BLOCK_17400_SCHEMA)
        return parser

    def test_parser_produces_nested_dicts(self):
        parser = self._make_parser()
        data = bytes(self._build_data(200))
        parsed = parser.parse_block(17400, data)

        # Each group should produce a sub-dict (possibly with None values)
        for group_name in [
            "config_grid",
            "config_sl1",
            "config_sl2",
            "simple_end_fields",
        ]:
            assert group_name in parsed.values, (
                f"Group '{group_name}' missing from parsed values"
            )
            got = type(parsed.values[group_name])
            assert isinstance(parsed.values[group_name], dict), (
                f"Expected dict for '{group_name}', got {got}"
            )

    def test_parser_config_grid_max_current_value(self):
        """config_grid.max_current reads from byte 84."""
        parser = self._make_parser()

        data = bytearray(200)
        data[84] = 0x00
        data[85] = 0x64  # 100 as big-endian UInt16

        parsed = parser.parse_block(17400, bytes(data))
        assert parsed.values["config_grid"]["max_current"] == 100

    def test_parser_simple_end_fields_null_when_short(self):
        """simple_end_fields return None when data too short (< 182 bytes)."""
        parser = self._make_parser()

        data = bytes(91)  # Exactly min_length, fields at 176+ are OOB
        parsed = parser.parse_block(17400, data)
        end = parsed.values["simple_end_fields"]
        assert isinstance(end, dict)
        # All fields at offsets 176+ should be None
        for fname in ["volt_level_set", "ac_supply_phase_num"]:
            assert end[fname] is None, (
                f"Expected None for {fname} with 91-byte data, got {end[fname]}"
            )
