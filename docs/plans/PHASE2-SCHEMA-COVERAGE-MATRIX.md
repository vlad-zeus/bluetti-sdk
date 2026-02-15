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

### Wave B (P1): Core control/settings blocks from APK docs

| Block | Doc Status | SDK Schema | Priority | Notes |
|---|---|---|---|---|
| 2000 | Full | Missing | P1 | Inverter base settings |
| 2200 | Full | Missing | P1 | Inverter advanced settings |
| 2400 | Full | Missing | P1 | Certification settings |
| 7000 | Full | Missing | P1 | Pack settings |
| 11000 | Full | Missing | P1 | IoT info |
| 12002 | Full | Missing | P1 | IoT WiFi settings |
| 19000 | Full | Missing | P1 | SOC threshold settings |

### Wave C (P2): Monitoring expansion

| Block | Doc Status | SDK Schema | Priority | Notes |
|---|---|---|---|---|
| 1700 | Partial | Missing | P2 | Meter info |
| 3500 | Partial | Missing | P2 | Energy statistics |
| 3600 | Partial | Missing | P2 | Year energy |
| 12161 | Partial | Missing | P2 | IoT enable status |
| 720 | Partial | Missing | P2 | OTA status |
| 6300 | Partial | Missing | P2 | Pack BMU read |

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
