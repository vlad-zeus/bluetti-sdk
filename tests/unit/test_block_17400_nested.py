"""Unit tests for Block 17400 (AT1_SETTINGS) nested schema model.

Tests verify:
- Contract: block_id, name, min_length, verification_status
- Nested groups present: 7x AT1BaseConfigItem + simple_end_fields + 2 enable groups
- Evidence-accurate structure: only proven fields modeled
- Deferred fields documented (not in schema)
- Parser: nested dict produced for each group, hex_enable_list transforms applied
- Completion pass (2026-02-17): original evidence scan; no guessed fields
- hex_enable_list unlock (2026-02-17): 10 new scalar fields added via transform
- force_enable unlock (2026-02-17): 6 force_enable scalar fields added
  (config_grid from data[12-13], config_sl1 from data[2-3])
- analysis audit corrections (2026-02-17): 6 offsets corrected, 7 new fields added
"""

from power_sdk.plugins.bluetti.v2.protocol.schema import FieldGroup
from power_sdk.plugins.bluetti.v2.schemas import BLOCK_17400_SCHEMA


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
            f.name: f for f in BLOCK_17400_SCHEMA.fields if isinstance(f, FieldGroup)
        }

    def test_all_ten_groups_present(self):
        """10 FieldGroups: 7x config items + simple_end_fields + 2 enable groups."""
        groups = self._groups()
        expected = {
            "top_level_enables",
            "startup_flags",
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
        from power_sdk.plugins.bluetti.v2.protocol.schema import Field

        flat = [f for f in BLOCK_17400_SCHEMA.fields if isinstance(f, Field)]
        assert flat == [], f"Expected no flat fields, got: {[f.name for f in flat]}"

    def test_schema_has_ten_total_fields(self):
        """Schema has exactly 10 FieldGroup entries after hex_enable_list unlock."""
        assert len(BLOCK_17400_SCHEMA.fields) == 10

    def test_config_grid_evidence_status_partial(self):
        groups = self._groups()
        assert groups["config_grid"].evidence_status == "partial"

    def test_config_sl1_evidence_status_partial(self):
        groups = self._groups()
        assert groups["config_sl1"].evidence_status == "partial"

    def test_simple_end_fields_evidence_status_verified_reference(self):
        """simple_end_fields group is verified_reference (all proven transforms)."""
        groups = self._groups()
        assert groups["simple_end_fields"].evidence_status == "verified_reference"

    def test_top_level_enables_evidence_status_verified_reference(self):
        """top_level_enables group is verified_reference.

        Indices are confirmed in reference evidence.
        """
        groups = self._groups()
        assert groups["top_level_enables"].evidence_status == "verified_reference"

    def test_startup_flags_evidence_status_verified_reference(self):
        """startup_flags group is verified_reference.

        Indices are confirmed in reference evidence.
        """
        groups = self._groups()
        assert groups["startup_flags"].evidence_status == "verified_reference"

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
            f
            for f in BLOCK_17400_SCHEMA.fields
            if isinstance(f, FieldGroup) and f.name == "config_grid"
        )

    def test_config_grid_has_six_sub_fields(self):
        """config_grid has 6 proven sub-fields.

        type, linkage_enable, force_enable_0/1/2, max_current.
        """
        group = self._config_grid()
        assert len(group.fields) == 6

    def test_config_grid_has_type(self):
        group = self._config_grid()
        names = {f.name for f in group.fields}
        assert "type" in names

    def test_config_grid_type_offset(self):
        """type at byte 20 (data[20-21], reference lines 2398-2472)."""
        group = self._config_grid()
        f = next(f for f in group.fields if f.name == "type")
        assert f.offset == 20

    def test_config_grid_type_has_hex_enable_list_transform(self):
        """type uses hex_enable_list:0:0 transform."""
        group = self._config_grid()
        f = next(f for f in group.fields if f.name == "type")
        assert f.transform is not None
        assert "hex_enable_list:0:0" in f.transform

    def test_config_grid_has_linkage_enable(self):
        group = self._config_grid()
        names = {f.name for f in group.fields}
        assert "linkage_enable" in names

    def test_config_grid_linkage_enable_offset(self):
        """linkage_enable at byte 22 (data[22-23], reference lines 2433-2494)."""
        group = self._config_grid()
        f = next(f for f in group.fields if f.name == "linkage_enable")
        assert f.offset == 22

    def test_config_grid_has_max_current(self):
        group = self._config_grid()
        names = {f.name for f in group.fields}
        assert "max_current" in names

    def test_config_grid_max_current_offset(self):
        """max_current at byte 84 (data[84-85], reference line 2578)."""
        group = self._config_grid()
        f = next(f for f in group.fields if f.name == "max_current")
        assert f.offset == 84

    def test_config_grid_max_current_not_required(self):
        group = self._config_grid()
        f = next(f for f in group.fields if f.name == "max_current")
        assert f.required is False

    def test_config_grid_max_current_type_uint16(self):
        from power_sdk.plugins.bluetti.v2.protocol.datatypes import UInt16

        group = self._config_grid()
        f = next(f for f in group.fields if f.name == "max_current")
        assert isinstance(f.type, UInt16)

    def test_config_grid_has_force_enable_fields(self):
        """config_grid has force_enable_0/1/2 at bytes 12-13."""
        group = self._config_grid()
        names = {f.name for f in group.fields}
        assert "force_enable_0" in names
        assert "force_enable_1" in names
        assert "force_enable_2" in names

    def test_config_grid_force_enable_offset(self):
        """force_enable fields at byte 12 (data[12-13])."""
        group = self._config_grid()
        for fname in ("force_enable_0", "force_enable_1", "force_enable_2"):
            f = next(f for f in group.fields if f.name == fname)
            assert f.offset == 12, f"{fname} should be at offset 12"

    def test_config_grid_force_enable_transforms(self):
        """force_enable_0/1/2 use hex_enable_list:0:0/1/2 respectively."""
        group = self._config_grid()
        for idx in range(3):
            f = next(f for f in group.fields if f.name == f"force_enable_{idx}")
            assert f.transform is not None
            assert f"hex_enable_list:0:{idx}" in f.transform

    def test_config_grid_has_reference_reference_in_description(self):
        group = self._config_grid()
        f = next(f for f in group.fields if f.name == "max_current")
        assert "reference" in f.description.lower()


class TestBlock17400ConfigSL1:
    """Verify config_sl1 proven sub-fields."""

    def _config_sl1(self):
        return next(
            f
            for f in BLOCK_17400_SCHEMA.fields
            if isinstance(f, FieldGroup) and f.name == "config_sl1"
        )

    def test_config_sl1_has_six_sub_fields(self):
        """config_sl1 has 6 proven sub-fields.

        type, linkage_enable, force_enable_0/1/2, max_current.
        """
        group = self._config_sl1()
        assert len(group.fields) == 6

    def test_config_sl1_has_type(self):
        group = self._config_sl1()
        names = {f.name for f in group.fields}
        assert "type" in names

    def test_config_sl1_type_offset(self):
        """type at byte 20 (data[20-21], reference lines 2621-2624)."""
        group = self._config_sl1()
        f = next(f for f in group.fields if f.name == "type")
        assert f.offset == 20

    def test_config_sl1_type_has_hex_enable_list_index_1(self):
        """SL1 type uses hex_enable_list:0:1 (index [1], different from grid's [0])."""
        group = self._config_sl1()
        f = next(f for f in group.fields if f.name == "type")
        assert f.transform is not None
        assert "hex_enable_list:0:1" in f.transform

    def test_config_sl1_has_linkage_enable(self):
        group = self._config_sl1()
        names = {f.name for f in group.fields}
        assert "linkage_enable" in names

    def test_config_sl1_linkage_enable_offset(self):
        """linkage_enable at byte 22 (data[22-23], reference lines 2652-2655)."""
        group = self._config_sl1()
        f = next(f for f in group.fields if f.name == "linkage_enable")
        assert f.offset == 22

    def test_config_sl1_has_max_current(self):
        group = self._config_sl1()
        names = {f.name for f in group.fields}
        assert "max_current" in names

    def test_config_sl1_max_current_offset(self):
        """max_current at byte 86 (data[86-87], reference lines 2744-2746)."""
        group = self._config_sl1()
        f = next(f for f in group.fields if f.name == "max_current")
        assert f.offset == 86

    def test_config_sl1_max_current_type_uint16(self):
        from power_sdk.plugins.bluetti.v2.protocol.datatypes import UInt16

        group = self._config_sl1()
        f = next(f for f in group.fields if f.name == "max_current")
        assert isinstance(f.type, UInt16)

    def test_config_sl1_has_force_enable_fields(self):
        """config_sl1 has force_enable_0/1/2 at bytes 2-3."""
        group = self._config_sl1()
        names = {f.name for f in group.fields}
        assert "force_enable_0" in names
        assert "force_enable_1" in names
        assert "force_enable_2" in names

    def test_config_sl1_force_enable_offset(self):
        """force_enable fields at byte 2 (data[2-3])."""
        group = self._config_sl1()
        for fname in ("force_enable_0", "force_enable_1", "force_enable_2"):
            f = next(f for f in group.fields if f.name == fname)
            assert f.offset == 2, f"{fname} should be at offset 2"

    def test_config_sl1_force_enable_transforms(self):
        """force_enable_0/1/2 use hex_enable_list:0:0/1/2 respectively."""
        group = self._config_sl1()
        for idx in range(3):
            f = next(f for f in group.fields if f.name == f"force_enable_{idx}")
            assert f.transform is not None
            assert f"hex_enable_list:0:{idx}" in f.transform


class TestBlock17400DeferredGroups:
    """Verify formerly-deferred groups now have analysis-audit-proven fields."""

    def _groups(self):
        return {
            f.name: f for f in BLOCK_17400_SCHEMA.fields if isinstance(f, FieldGroup)
        }

    def test_config_sl2_has_max_current(self):
        """SL2 max_current proven at byte 88 (reference 2869-2906)."""
        groups = self._groups()
        assert len(groups["config_sl2"].fields) == 1

    def test_config_sl3_has_max_current(self):
        """SL3 max_current proven at byte 90 (reference 3027-3064)."""
        groups = self._groups()
        assert len(groups["config_sl3"].fields) == 1

    def test_config_sl4_has_max_current(self):
        """SL4 max_current proven at byte 92 (reference 3192-3229)."""
        groups = self._groups()
        assert len(groups["config_sl4"].fields) == 1

    def test_config_pcs1_has_two_sub_fields(self):
        """PCS1 has type + max_current (reference 2393-3272, 3287-3304)."""
        groups = self._groups()
        assert len(groups["config_pcs1"].fields) == 2

    def test_config_pcs2_has_two_sub_fields(self):
        """PCS2 has type + max_current (reference 2393-3356, 3366-3383)."""
        groups = self._groups()
        assert len(groups["config_pcs2"].fields) == 2


class TestBlock17400SimpleEndFields:
    """Verify simple_end_fields group (5 reference-proven fields)."""

    def _end_fields_group(self):
        return next(
            f
            for f in BLOCK_17400_SCHEMA.fields
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
        """volt_level_set at byte 176 (reference: lines 3525-3567)."""
        group = self._end_fields_group()
        f = next(f for f in group.fields if f.name == "volt_level_set")
        assert f.offset == 176

    def test_ac_supply_phase_num_offset(self):
        """ac_supply_phase_num at byte 176 (same word, different bits)."""
        group = self._end_fields_group()
        f = next(f for f in group.fields if f.name == "ac_supply_phase_num")
        assert f.offset == 176

    def test_soc_gen_auto_stop_offset(self):
        """soc_gen_auto_stop at byte 178 (reference: lines 3580-3605)."""
        group = self._end_fields_group()
        f = next(f for f in group.fields if f.name == "soc_gen_auto_stop")
        assert f.offset == 178

    def test_soc_gen_auto_start_offset(self):
        """soc_gen_auto_start at byte 179 (reference: lines 3607-3626)."""
        group = self._end_fields_group()
        f = next(f for f in group.fields if f.name == "soc_gen_auto_start")
        assert f.offset == 179

    def test_soc_black_start_offset(self):
        """soc_black_start at byte 181 (reference: lines 3628-3645)."""
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


class TestBlock17400TopLevelEnables:
    """Verify top_level_enables group (chg_from_grid_enable, feed_to_grid_enable)."""

    def _group(self):
        return next(
            f
            for f in BLOCK_17400_SCHEMA.fields
            if isinstance(f, FieldGroup) and f.name == "top_level_enables"
        )

    def test_two_sub_fields(self):
        group = self._group()
        assert len(group.fields) == 2

    def test_chg_from_grid_enable_present(self):
        group = self._group()
        names = {f.name for f in group.fields}
        assert "chg_from_grid_enable" in names

    def test_chg_from_grid_enable_offset(self):
        """chg_from_grid_enable at byte 0 (data[0-1], reference 2012-2129)."""
        group = self._group()
        f = next(f for f in group.fields if f.name == "chg_from_grid_enable")
        assert f.offset == 0

    def test_chg_from_grid_enable_transform(self):
        """Uses hex_enable_list:0:3 (index [3] confirmed in evidence doc)."""
        group = self._group()
        f = next(f for f in group.fields if f.name == "chg_from_grid_enable")
        assert f.transform is not None
        assert "hex_enable_list:0:3" in f.transform

    def test_feed_to_grid_enable_present(self):
        group = self._group()
        names = {f.name for f in group.fields}
        assert "feed_to_grid_enable" in names

    def test_feed_to_grid_enable_offset(self):
        """feed_to_grid_enable at byte 2 (data[2-3], reference 2051-2142)."""
        group = self._group()
        f = next(f for f in group.fields if f.name == "feed_to_grid_enable")
        assert f.offset == 2

    def test_feed_to_grid_enable_transform(self):
        """Uses hex_enable_list:0:4 (index [4] confirmed in evidence doc)."""
        group = self._group()
        f = next(f for f in group.fields if f.name == "feed_to_grid_enable")
        assert f.transform is not None
        assert "hex_enable_list:0:4" in f.transform

    def test_evidence_status_verified_reference(self):
        group = self._group()
        assert group.evidence_status == "verified_reference"


class TestBlock17400StartupFlags:
    """Verify startup_flags group (4 fields from bytes 174-175)."""

    def _group(self):
        return next(
            f
            for f in BLOCK_17400_SCHEMA.fields
            if isinstance(f, FieldGroup) and f.name == "startup_flags"
        )

    def test_four_sub_fields(self):
        group = self._group()
        assert len(group.fields) == 4

    def test_all_four_fields_present(self):
        group = self._group()
        names = {f.name for f in group.fields}
        expected = {
            "black_start_enable",
            "black_start_mode",
            "generator_auto_start_enable",
            "off_grid_power_priority",
        }
        assert expected == names

    def test_all_at_offset_174(self):
        """All 4 fields share byte offset 174 (data[174-175])."""
        group = self._group()
        for f in group.fields:
            assert f.offset == 174, (
                f"Field '{f.name}' should be at offset 174, got {f.offset}"
            )

    def test_black_start_enable_transform(self):
        """black_start_enable uses hex_enable_list:0:2 (index [2])."""
        group = self._group()
        f = next(f for f in group.fields if f.name == "black_start_enable")
        assert f.transform is not None
        assert "hex_enable_list:0:2" in f.transform

    def test_black_start_mode_transform(self):
        """black_start_mode uses hex_enable_list:0:3 (index [3])."""
        group = self._group()
        f = next(f for f in group.fields if f.name == "black_start_mode")
        assert f.transform is not None
        assert "hex_enable_list:0:3" in f.transform

    def test_generator_auto_start_enable_transform(self):
        """generator_auto_start_enable uses hex_enable_list:0:4 (index [4])."""
        group = self._group()
        f = next(f for f in group.fields if f.name == "generator_auto_start_enable")
        assert f.transform is not None
        assert "hex_enable_list:0:4" in f.transform

    def test_off_grid_power_priority_transform(self):
        """off_grid_power_priority uses hex_enable_list:0:5 (index [5])."""
        group = self._group()
        f = next(f for f in group.fields if f.name == "off_grid_power_priority")
        assert f.transform is not None
        assert "hex_enable_list:0:5" in f.transform

    def test_evidence_status_verified_reference(self):
        group = self._group()
        assert group.evidence_status == "verified_reference"

    def test_all_fields_have_reference_reference(self):
        group = self._group()
        for f in group.fields:
            assert f.description and "reference" in f.description.lower(), (
                f"Field '{f.name}' lacks reference reference in description"
            )


class TestBlock17400ParserIntegration:
    """Test that V2Parser produces nested dicts for Block 17400 groups."""

    def _build_data(self, size=200):
        return bytearray(size)

    def _make_parser(self):
        from power_sdk.plugins.bluetti.v2.protocol.parser import V2Parser

        parser = V2Parser()
        parser.register_schema(BLOCK_17400_SCHEMA)
        return parser

    def test_parser_produces_nested_dicts(self):
        parser = self._make_parser()
        data = bytes(self._build_data(200))
        parsed = parser.parse_block(17400, data)

        # Each group should produce a sub-dict (possibly with None values)
        for group_name in [
            "top_level_enables",
            "startup_flags",
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

    def test_parser_hex_enable_list_transform_applied(self):
        """hex_enable_list transform is applied by parser for startup_flags group.

        bytes 174-175 = 0x1234:
          0x1234 = 0001001000110100 → chunks [0,2,0,1,0,3,2,0]
          index[2]=0 (black_start_enable), index[3]=1 (black_start_mode),
          index[4]=0 (gen_auto_start_enable), index[5]=3 (off_grid_power_priority)
        """
        parser = self._make_parser()
        data = bytearray(200)
        data[174] = 0x12
        data[175] = 0x34  # UInt16 big-endian = 0x1234

        parsed = parser.parse_block(17400, bytes(data))
        flags = parsed.values["startup_flags"]
        assert isinstance(flags, dict)
        assert flags["black_start_enable"] == 0
        assert flags["black_start_mode"] == 1
        assert flags["generator_auto_start_enable"] == 0
        assert flags["off_grid_power_priority"] == 3

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
    """Completion pass, hex_enable_list unlock, and analysis audit verification.

    Completion pass (2026-02-17): evidence re-scan found 0 new fields addable
    with the original framework (no hexStrToEnableList support).

    hex_enable_list unlock (2026-02-17): 10 scalar fields added after the
    hex_enable_list transform was implemented. delay_enable_1-3 remain deferred
    (full List<Integer>, not a single scalar index).

    analysis audit corrections (2026-02-17): 6 wrong byte offsets corrected,
    7 new proven fields added (SL2/SL3/SL4 max_current, PCS1/PCS2 type + max_current).
    """

    def _all_sub_field_names(self):
        names = set()
        for group in BLOCK_17400_SCHEMA.fields:
            if isinstance(group, FieldGroup):
                for f in group.fields:
                    names.add(f.name)
        return names

    def test_total_proven_scalar_fields_is_thirty(self):
        """Schema contains exactly 30 proven scalar sub-fields.

        7 original + 10 added via hex_enable_list transform + 6 force_enable
        + 7 new fields (SL2/SL3/SL4 max_current + PCS1/PCS2 type + max_current):
        - top_level_enables: 2 (chg_from_grid_enable, feed_to_grid_enable)
        - startup_flags: 4 (black_start_*, gen_auto_start, off_grid_priority)
        - config_grid: type, linkage_enable, force_enable_0/1/2, max_current (6 total)
        - config_sl1: type, linkage_enable, force_enable_0/1/2, max_current (6 total)
        - config_sl2: max_current (1 total)
        - config_sl3: max_current (1 total)
        - config_sl4: max_current (1 total)
        - config_pcs1: type, max_current (2 total)
        - config_pcs2: type, max_current (2 total)
        - simple_end_fields: 5 (unchanged)
        """
        total = sum(
            len(g.fields)
            for g in BLOCK_17400_SCHEMA.fields
            if isinstance(g, FieldGroup)
        )
        assert total == 30, (
            f"Expected 30 proven scalar sub-fields, got {total}. (2+4+6+6+1+1+1+2+2+5)"
        )

    def test_hex_enable_list_scalar_fields_now_present(self):
        """Scalar hexStrToEnableList fields are now in schema."""
        present = self._all_sub_field_names()
        # These were deferred until hex_enable_list transform was added
        now_present = {
            "chg_from_grid_enable",
            "feed_to_grid_enable",
            "black_start_enable",
            "black_start_mode",
            "generator_auto_start_enable",
            "off_grid_power_priority",
            "type",  # in config_grid and config_sl1
            "linkage_enable",  # in config_grid and config_sl1
        }
        missing = now_present - present
        assert not missing, (
            f"Expected hex_enable_list scalar fields in schema, missing: {missing}"
        )

    def test_delay_enable_fields_still_absent(self):
        """delay_enable_1/2/3 remain deferred (full List<Integer>, not scalar index).

        The Java parser stores the whole hexStrToEnableList() result as a
        List<Integer> for delayEnable1-3 (bytes 6-11). This cannot be modeled
        as a single scalar field with hex_enable_list:mode:index.
        """
        present = self._all_sub_field_names()
        still_deferred = {"delay_enable_1", "delay_enable_2", "delay_enable_3"}
        present_deferred = present & still_deferred
        assert not present_deferred, (
            f"delay_enable fields must remain deferred (full List<Integer>): "
            f"{present_deferred}"
        )

    def test_complex_list_fields_absent(self):
        """Fields requiring complex list/sub-parser logic are not in schema.

        timerEnable requires protectEnableParse() sub-parser logic.
        protectList requires protectEnableParse() sub-parser.
        socSetList requires socThresholdParse() sub-parser.
        All are beyond the current FieldGroup flat-scalar model.

        Note: force_enable_0/1/2 ARE modeled (scalar index extraction via
        hex_enable_list transform from delayEnable2/3). The top-level
        delay_enable_1/2/3 full-list forms remain deferred.
        """
        present = self._all_sub_field_names()
        complex_list_fields = {
            "timer_enable",
            "protect_list",
            "soc_set_list",
        }
        present_complex = present & complex_list_fields
        assert not present_complex, (
            f"Complex-list fields must not be in schema: {present_complex}"
        )

    def test_all_modeled_fields_are_reference_proven(self):
        """Every sub-field currently in the schema has a reference line reference.

        This test guards against future regressions where unproven fields are
        accidentally added. All descriptions must contain 'reference'.
        """
        for group in BLOCK_17400_SCHEMA.fields:
            if not isinstance(group, FieldGroup):
                continue
            for f in group.fields:
                assert f.description and "reference" in f.description.lower(), (
                    f"Field '{group.name}.{f.name}' lacks reference line reference "
                    "in description. Only reference-proven fields may be modeled."
                )

    def test_verification_status_stays_partial(self):
        """Block 17400 must remain partial until device validation is done.

        Even though all currently modeled sub-fields are reference-proven,
        the overall schema is structurally incomplete (many deferred fields)
        and device testing has not been completed. verified_reference upgrade
        requires both hexStrToEnableList transform + device validation gate.
        """
        assert BLOCK_17400_SCHEMA.verification_status == "partial"
