"""Unit tests for Block 17400 (AT1_SETTINGS) nested schema model.

Tests verify:
- Contract: block_id, name, min_length, verification_status
- Nested groups present: 7x AT1BaseConfigItem + simple_end_fields
- Evidence-accurate structure: only proven fields modeled
- Deferred fields documented (not in schema)
- Parser: nested dict produced for each group
- Completion pass (2026-02-17): no guessed fields added
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


class TestBlock17400CompletionPassEvidence:
    """Completion pass (2026-02-17): no-guessing constraint verification.

    Evidence re-scan found 0 new proven fields to add.
    All un-modeled PROVEN fields require either hexStrToEnableList transform
    (not in framework), complex list/sub-parser logic, or have only
    pattern-inferred (not directly smali-proven) byte offsets.
    """

    def _all_sub_field_names(self):
        names = set()
        for group in BLOCK_17400_SCHEMA.fields:
            if isinstance(group, FieldGroup):
                for f in group.fields:
                    names.add(f.name)
        return names

    def test_total_proven_scalar_fields_is_seven(self):
        """Schema contains exactly 7 proven scalar sub-fields after completion pass.

        Evidence re-scan found no additional proven fields to add.
        """
        total = sum(
            len(g.fields)
            for g in BLOCK_17400_SCHEMA.fields
            if isinstance(g, FieldGroup)
        )
        assert total == 7, (
            f"Expected 7 proven scalar sub-fields, got {total}. "
            "Completion pass found no additional proven fields to add."
        )

    def test_hex_str_to_enable_list_fields_absent(self):
        """Fields requiring hexStrToEnableList transform are not in schema.

        These fields ARE proven in smali (docs/re/17400-EVIDENCE.md) but
        require a hexStrToEnableList() transform that is not yet part of
        the transform framework. Adding them without the correct transform
        would produce wrong values.
        """
        present = self._all_sub_field_names()
        # Top-level deferred (bytes 0-11, smali lines 2012-2253)
        top_level_deferred = {
            "chg_from_grid_enable",
            "feed_to_grid_enable",
            "delay_enable_1",
            "delay_enable_2",
            "delay_enable_3",
        }
        # bytes 174-175 fields (smali lines 3426-3523)
        byte_174_deferred = {
            "black_start_enable",
            "black_start_mode",
            "generator_auto_start_enable",
            "off_grid_power_priority",
        }
        # Per-config-item sub-fields (smali lines 2472-2663)
        per_item_deferred = {"linkage_enable", "type"}
        all_deferred = top_level_deferred | byte_174_deferred | per_item_deferred
        present_deferred = present & all_deferred
        assert not present_deferred, (
            f"Deferred hexStrToEnableList fields must not be in schema: "
            f"{present_deferred}"
        )

    def test_complex_list_fields_absent(self):
        """Fields requiring complex list/sub-parser logic are not in schema.

        forceEnable/timerEnable require List<Integer> parsing.
        protectList requires protectEnableParse() sub-parser.
        socSetList requires socThresholdParse() sub-parser.
        All are beyond the current FieldGroup flat-scalar model.
        """
        present = self._all_sub_field_names()
        complex_list_fields = {
            "force_enable",
            "timer_enable",
            "protect_list",
            "soc_set_list",
        }
        present_complex = present & complex_list_fields
        assert not present_complex, (
            f"Complex-list fields must not be in schema: {present_complex}"
        )

    def test_sl2_sl3_sl4_max_current_absent(self):
        """configSL2/SL3/SL4 max_current offsets are pattern-inferred only.

        Evidence says 'pattern continues for configSL2, SL3, SL4' but gives
        no explicit smali line for their max_current byte offsets. Under the
        no-guessing constraint these remain empty (sub_fields=[]).
        """
        groups = {
            g.name: g
            for g in BLOCK_17400_SCHEMA.fields
            if isinstance(g, FieldGroup)
        }
        for name in ("config_sl2", "config_sl3", "config_sl4"):
            assert len(groups[name].fields) == 0, (
                f"{name} max_current is pattern-inferred (no direct smali ref); "
                "must remain empty until proven."
            )

    def test_pcs1_pcs2_remain_empty(self):
        """configPCS1/PCS2 have no proven sub-field offsets in evidence.

        Evidence gives only byte range (data indices 94-159 / 95-159) with no
        specific absolute offset for any sub-field. Remains deferred.
        """
        groups = {
            g.name: g
            for g in BLOCK_17400_SCHEMA.fields
            if isinstance(g, FieldGroup)
        }
        for name in ("config_pcs1", "config_pcs2"):
            assert len(groups[name].fields) == 0, (
                f"{name} has no proven sub-field offsets in evidence; "
                "must remain empty."
            )

    def test_all_modeled_fields_are_smali_proven(self):
        """Every sub-field currently in the schema has a smali line reference.

        This test guards against future regressions where unproven fields are
        accidentally added. All descriptions must contain 'smali'.
        """
        for group in BLOCK_17400_SCHEMA.fields:
            if not isinstance(group, FieldGroup):
                continue
            for f in group.fields:
                assert f.description and "smali" in f.description.lower(), (
                    f"Field '{group.name}.{f.name}' lacks smali line reference "
                    "in description. Only smali-proven fields may be modeled."
                )

    def test_verification_status_stays_partial(self):
        """Block 17400 must remain partial until device validation is done.

        Even though all currently modeled sub-fields are smali-proven,
        the overall schema is structurally incomplete (many deferred fields)
        and device testing has not been completed. smali_verified upgrade
        requires both hexStrToEnableList transform + device validation gate.
        """
        assert BLOCK_17400_SCHEMA.verification_status == "partial"
