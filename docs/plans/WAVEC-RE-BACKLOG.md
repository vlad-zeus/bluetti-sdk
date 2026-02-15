# Wave C Reverse-Engineering Backlog

Status: Open  
Scope: finalize Wave C provisional schemas with smali-verified field maps.

## Why this exists

Wave C blocks are currently implemented as minimal/estimated schemas to keep
coverage moving, but they are not fully reverse-engineered. This backlog is the
"do not forget" checklist before marking Wave C truly complete.

## Priority Order

1. Block `6300` (PACK_BMU_READ) - high complexity, dynamic structure
2. Block `12161` (IOT_ENABLE_INFO) - control/status semantics
3. Block `1700` (METER_INFO) - monitoring correctness
4. Block `3500` (TOTAL_ENERGY_INFO) - long-term energy data correctness
5. Block `3600` (CURR_YEAR_ENERGY) - annual energy data correctness
6. Block `720` (OTA_STATUS) - firmware flow visibility

## Per-block Tasks

### Block 6300 - `parsePackBMUInfo` / `parsePackSubPackInfo`

1. Extract full offset formulas for `bmu_cnt > 1`.
2. Verify software version gate by protocol version.
3. Define strategy:
   - either dynamic parser extension for BMU arrays, or
   - explicit packed/array field model in schema layer.
4. Add golden payload tests for single-BMU and multi-BMU samples.

### Block 12161 - `parseIOTEnableInfo`

1. Recover full `IoTCtrlStatus` field map and enum semantics.
2. Replace minimal placeholders with verified names/types.
3. Add tests with known payload → expected parsed values.

### Block 1700 - `parseInvMeterInfo`

1. Recover full CT meter field list (power/current/voltage and signs/scales).
2. Verify signed vs unsigned handling and scale factors.
3. Add parser tests with non-zero and negative-value payloads.

### Block 3500 - `parseTotalEnergyInfo`

1. Recover exact field set (not Block 100 assumptions).
2. Confirm units/scales (kWh vs other, decimal scale).
3. Add tests with fixed vectors and expected values.

### Block 3600 - `parseCurrYearEnergy`

1. Recover exact yearly metrics and ordering.
2. Confirm scale/units and reset behavior semantics.
3. Add tests with fixed vectors and expected values.

### Block 720 - `parseOTAStatus`

1. Recover status code map and progress semantics.
2. Add optional enum mapping where appropriate.
3. Add tests for representative OTA states.

## Exit Criteria (Wave C Re-closure)

1. All six blocks have smali-verified field maps.
2. No "estimated" fields remain in Wave C schemas.
3. TODO(smali-verify) markers removed from Wave C files.
4. Golden-vector tests added for each block.
5. `PHASE2-SCHEMA-COVERAGE-MATRIX.md` updated from `Provisional` to `Done`.
