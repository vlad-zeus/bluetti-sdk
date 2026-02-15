# Phase 2 Schema Coverage Matrix

Status: Draft (post `platform-stable`)  
Updated: 2026-02-15

## Goal

Turn APK-recovered block documentation into implemented, tested declarative schemas and aligned device profiles.

## Ground Truth Sources

1. `docs/blocks/V2_BLOCKS_INDEX.md` (78 discovered V2 blocks)
2. `docs/blocks/*.md` detailed reverse-engineering notes
3. Active SDK profiles in `bluetti_sdk/devices/profiles/*.py`

## Current Implementation Snapshot

Implemented declarative schemas in SDK:

1. Block `100` (`APP_HOME_DATA`)
2. Block `1100` (`INV_BASE_INFO`) ✅ Wave A
3. Block `1300` (`INV_GRID_INFO`)
4. Block `1400` (`INV_LOAD_INFO`) ✅ Wave A
5. Block `1500` (`INV_INV_INFO`) ✅ Wave A
6. Block `6000` (`PACK_MAIN_INFO`)
7. Block `6100` (`PACK_ITEM_INFO`) ✅ Wave A

Profile-required blocks today:

1. `EL30V2`: `100`, `1300`, `6000` (✅ fully covered)
2. `Elite 200 V2`: `100`, `1300`, `6000` (✅ fully covered)
3. `EL100V2`: `100`, `1100`, `1300`, `1400`, `1500`, `6000`, `6100` (✅ fully covered)

## Priority Matrix (Phase 2)

### Wave A (P0): Close active profile gaps ✅ COMPLETED

| Block | Doc Status | SDK Schema | In Active Profile | Priority | Status |
|---|---|---|---|---|---|
| 1100 | Full | ✅ Implemented | EL100V2 | P0 | ✅ Done |
| 1400 | Full | ✅ Implemented | EL100V2 | P0 | ✅ Done |
| 1500 | Full | ✅ Implemented | EL100V2 | P0 | ✅ Done |
| 6100 | Full | ✅ Implemented | EL100V2 | P0 | ✅ Done |

Definition of done for Wave A: ✅ ALL COMPLETE

1. ✅ Add `block_1100_declarative.py`, `block_1400_declarative.py`, `block_1500_declarative.py`, `block_6100_declarative.py`
2. ✅ Register schemas via `schemas/__init__.py` auto-registration
3. ✅ Add unit tests (structure validation) and smoke tests (client integration)
4. ✅ Validate EL100V2 group reads for `inverter` and `cells`
5. ✅ Quality gates: ruff ✓, mypy ✓, pytest (270 passed, 89% coverage ✓)

### Wave B (P1): Core control/settings blocks from APK docs ✅ COMPLETED

| Block | Doc Status | SDK Schema | Priority | Status | Field Coverage |
|---|---|---|---|---|---|
| 2000 | Full | ✅ Implemented | P1 | ✅ Done | 23 fields (partial: gaps at offsets 1-5, 5-7, 7-9, 9-11, 11-13, 13-15, 15-19, 19-21, 25-27, 31-33) |
| 2200 | Full | ✅ Implemented | P1 | ✅ Done | 11 fields (partial: gaps at 9-11, 11-13; includes password field) |
| 2400 | Full | ✅ Implemented | P1 | ✅ Done | 6 fields (full coverage for documented offsets) |
| 7000 | Full | ✅ Implemented | P1 | ✅ Done | 4 fields (partial: gap at offset 3-11) |
| 11000 | Full | ✅ Implemented | P1 | ✅ Done | 6 fields (full coverage for IOT identification) |
| 12002 | Full | ✅ Implemented | P1 | ✅ Done | 4 fields (partial: variable offset due to H32BEnable; SECURITY: WiFi credentials) |
| 19000 | Full | ✅ Implemented | P1 | ✅ Done | 6 threshold pairs (bit-packed format, requires application unpacking) |

Definition of done for Wave B: ✅ ALL COMPLETE

1. ✅ Add block_2000/2200/2400/7000/11000/12002/19000_declarative.py
2. ✅ Register schemas via `schemas/__init__.py` auto-registration (14 total built-in blocks)
3. ✅ Add unit tests (test_wave_b_blocks.py: 14 tests, test_wave_b_blocks_smoke.py: 4 tests)
4. ✅ Quality gates: ruff ✓, mypy ✓, pytest (304 passed, 89% coverage ✓)
5. ✅ Documentation: TODO(smali-verify) markers for ambiguous offsets

Key Findings:
- Block 2200, 12002: Contain sensitive data (password, WiFi credentials)
- Block 19000: Bit-packed format (2 SOC thresholds per UInt16 register)
- All blocks marked required=False for ambiguous fields pending smali verification

### Wave C (P2): Monitoring expansion ✅ COMPLETED

| Block | Doc Status | SDK Schema | Priority | Status | Field Coverage |
|---|---|---|---|---|---|
| 720 | Partial | ✅ Implemented | P2 | ✅ Done | 2 fields (minimal: ota_status, ota_progress) |
| 1700 | Partial | ✅ Implemented | P2 | ✅ Done | 2 fields (minimal: meter_power, meter_current) |
| 3500 | Partial | ✅ Implemented | P2 | ✅ Done | 4 fields (estimated: total_pv/charge/discharge/grid energy) |
| 3600 | Partial | ✅ Implemented | P2 | ✅ Done | 4 fields (estimated: year_pv/charge/discharge/grid energy) |
| 6300 | Partial | ✅ Implemented | P2 | ✅ Done | 8 fields (partial: BMU0 structure, multi-BMU requires dynamic parsing) |
| 12161 | Partial | ✅ Implemented | P2 | ✅ Done | 3 fields (minimal: iot_enable, iot_mode, iot_ctrl_status) |

Definition of done for Wave C: ✅ ALL COMPLETE

1. ✅ Add block_720/1700/3500/3600/6300/12161_declarative.py
2. ✅ Register schemas via `schemas/__init__.py` auto-registration (20 total built-in blocks)
3. ✅ Add unit tests (test_wave_c_blocks.py: 12 tests, test_wave_c_blocks_smoke.py: 4 tests)
4. ✅ Quality gates: ruff ✓, mypy ✓, pytest (321 passed, 90% coverage ✓)
5. ✅ Documentation: TODO(smali-verify) markers for all partial blocks

Key Findings:
- Blocks 720, 1700, 12161: Minimal schemas (no detailed field mappings in APK docs)
- Blocks 3500, 3600: Estimated energy fields based on Block 100 patterns
- Block 6300: Detailed schema for single BMU; multi-BMU requires dynamic parsing
- All blocks marked required=False for estimated/minimal fields pending smali verification

### Wave D (P3): Long tail / accessory / event blocks

All remaining documented blocks from `V2_BLOCKS_INDEX.md` not included above.

## Execution Rules (strict)

1. Platform first rule is closed; now only schema/profile expansion in this phase.
2. No deprecated shim code for new schemas.
3. New block implementation must include:
   - Declarative schema
   - Unit tests (schema + parser integration)
   - Documentation link back to source block doc
4. No profile references to blocks without schema unless explicitly marked experimental.
5. Keep quality gates green on every wave: `ruff`, `mypy`, `pytest`, coverage floor.

## Claude Task Pack (copy/paste)

1. Implement Wave A blocks (`1100`, `1400`, `1500`, `6100`) as declarative schemas.
2. Add/adjust registry loading so new schemas auto-register.
3. Add tests:
   - one equivalence/structure test per block
   - one EL100V2 group-read smoke test using mocks
4. Update support matrix docs with actual implemented status.
5. Run `ruff`, `mypy`, `pytest` and report final numbers.

## Exit Criteria for Phase 2

1. All blocks referenced by shipped profiles are implemented.
2. Support matrix published and accurate.
3. No undocumented gaps between profile block lists and schema registry.
