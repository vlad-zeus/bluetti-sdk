# Block 15600 (DC_DC_SETTINGS) — Device Validation Gate

**Added**: Sprint 2026-02-17
**Status**: PARTIAL GATE — Awaiting targeted device testing
**Evidence source**: `docs/re/15600-EVIDENCE.md`
**Schema**: `bluetti_sdk/schemas/block_15600_declarative.py`
**Verification status**: `partial` (must not be upgraded without completing this gate)

---

## Why This Gate Exists

Block 15600 controls DC-DC converter voltage and current output. The smali
analysis (15600-EVIDENCE.md) proved offsets and parser routes for 37 fields.

Scale evidence is now mixed:
- PROVEN from caller smali: `voltSetDC1/2/3` and `outputCurrentDC3` use x0.1
- STILL UNKNOWN: `outputCurrentDC1/2` scale (no direct caller evidence)

**Safety consequence**: Writing a raw integer that is 10× too large could
configure a dangerous output voltage or overcurrent limit. This block must
not be considered production-ready until the scale factors are confirmed.

---

## Critical Blockers (1)

### Closed Blocker: voltSetDC1/2/3 scale factor

| Property | Value |
|----------|-------|
| Offsets | bytes 2-3 (DC1), 6-7 (DC2), 10-11 (DC3) |
| Parser | `parseInt(16)` — no division |
| Smali refs | 2002-2036 (DC1), 2089-2123 (DC2), 2167-2201 (DC3) |
| Current schema | `UInt16` + `scale(0.1)` + unit `V` |
| Evidence | Caller-level read/write paths prove `/10` and `*10` behavior |
| Verdict | **PROVEN** |

### Open Blocker: outputCurrentDC1/2 scale factor

| Property | Value |
|----------|-------|
| Offsets | bytes 4-5 (DC1), 8-9 (DC2) |
| Parser | `parseInt(16)` — no division |
| Smali refs | 2052-2086 (DC1), 2128-2162 (DC2) |
| Current schema | `UInt16`, no transform, description says "UNKNOWN unit" |
| Evidence | `outputCurrentDC3` proven x0.1; direct evidence for DC1/DC2 still absent |
| Hypothesis | Scale = 0.1 A — **NOT PROVEN for DC1/DC2** |

**Test required**: Same approach as voltage: compare 15500 read with 15600
setpoint. If scale matches, document.

### Closed Blocker: outputCurrentDC3 scale factor

`outputCurrentDC3` is now proven x0.1 from caller smali evidence and reflected in
schema transform (`scale(0.1)`, unit `A`).

---

## Current Schema State (2026-02-17)

**9 fields implemented** in `block_15600_declarative.py`:

| Field | Offset | Transform | Status |
|-------|--------|-----------|--------|
| `dc_ctrl` | 0 | `hex_enable_list:0:0` | PROVEN (smali 1943-1958) |
| `silent_mode_ctrl` | 0 | `hex_enable_list:0:1` | PROVEN (smali 1943-1971) |
| `factory_set` | 0 | `hex_enable_list:0:2` | PROVEN (smali 1943-1984) |
| `self_adaption_enable` | 0 | `hex_enable_list:0:3` | PROVEN (smali 1943-1999) |
| `volt_set_dc1` | 2 | `scale(0.1)` | PROVEN |
| `output_current_dc1` | 4 | none | PARTIAL (offset proven, scale unknown) |
| `volt_set_dc2` | 6 | `scale(0.1)` | PROVEN |
| `volt_set_dc3` | 10 | `scale(0.1)` | PROVEN |
| `output_current_dc3` | 12 | `scale(0.1)` | PROVEN |

**23 TODO comments** for fields requiring extended packet (size > 4, > 26, > 54
words) or proven scale factors. These are documented in the schema file.

---

## Validation Protocol

### Prerequisites

1. DC-DC converter device connected and powered
2. Block 15500 (DC_DC_INFO) readable from device
3. Block 15600 readable from device
4. Safe operating environment — do **not** change setpoints on live loads
   without confirming scale factors first

### Step 1: Read-Back Scale Factor Test (READ-ONLY)

Objective: Confirm volt/current scale without writing.

```
1. Read Block 15500 (DC_DC_INFO) — parse volt_dc1 using existing scale (0.1)
2. Read Block 15600 (DC_DC_SETTINGS) — record raw voltSetDC1 value
3. Compare: if 15600_raw × 0.1 ≈ 15500_volt_dc1 → scale confirmed
4. Repeat for outputCurrentDC1 vs. 15500 current read
5. Document raw values and computed results
```

**Expected result if hypothesis correct**: 15600 raw value = 10 × (15500 read value).

### Step 2: Known-Setting Verification (OPTIONAL, low-risk)

Only if read-back test is inconclusive and the device is in a safe test state:

```
1. Note current voltSetDC1 setting (from Step 1)
2. Write a small adjustment (±1 raw unit) and re-read Block 15500
3. Measure actual output voltage if multimeter available
4. Record: raw_write → measured_voltage
5. Restore original value immediately
```

### Step 3: Extended Packet Verification

Objective: Confirm protocol version gates (list.size() conditions).

```
1. Capture raw Block 15600 packet bytes
2. Count 16-bit words (bytes / 2)
3. Record which condition gates apply:
   - ≤ 4 words: baseline only (dc_ctrl + voltSetDC1)
   - > 4 words: + outputCurrentDC1/2/3, voltSetDC2/3
   - > 26 words: + chgModeDC1-4, batteryCapacity, etc.
   - > 54 words: + sysPowerCtrl, remoteStartupSoc, etc.
4. Update schema min_length if current value (36) is wrong for device
```

---

## Upgrade Criteria

### To `partial` → `smali_verified`

All of the following must be satisfied:

- [x] voltSetDC1/2/3 scale factors confirmed (0.1 V)
- [x] outputCurrentDC3 scale factor confirmed (0.1 A)
- [ ] outputCurrentDC1/2 scale factors confirmed (0.1 A or other)
- [ ] voltSet2DC3 semantics confirmed
- [ ] Schema transforms updated with confirmed scale values
- [ ] At least 1 extended-packet field confirmed (chgModeDC1 or batteryCapacity)
- [ ] `verification_status` and descriptions updated in schema
- [ ] Tests updated (new field counts, scale factor assertions)

### Intermediate `partial` upgrade (safe to do now)

The old field count in PHASE2 matrix was stale. Schema now has **9 fields**
(4 enable bits + 5 voltage/current fields with mixed verification status).

---

## Files to Update After Validation

1. `bluetti_sdk/schemas/block_15600_declarative.py`
   - Add `transform=("scale:0.1",)` (or confirmed factor) to volt/current fields
   - Add 23+ deferred fields from the evidence table
   - Change `verification_status` from `"partial"` to `"smali_verified"`

2. `docs/plans/PHASE2-SCHEMA-COVERAGE-MATRIX.md`
   - Update "4 fields" → "7 fields" (fix stale count)
   - Remove "3 CRITICAL blockers" note once resolved
   - Change status from `⚠️ Partial` to `✅ Verified`

3. `tests/unit/test_wave_d_batch3_blocks.py`
   - Update field count assertions to match new schema

4. This file: update status from BLOCKED → COMPLETE

---

## Evidence References

| Artifact | Location | Notes |
|----------|----------|-------|
| Complete field table (46 fields) | `docs/re/15600-EVIDENCE.md` | All offsets/transforms |
| Smali parser source | `DCDCParser.settingsInfoParse` lines 1780-3195 | Block 15500 for comparison |
| Scale comparison target | `DCDCParser.baseInfoParse` lines ~100-800 | Uses `/ 10.0f` |
| Current schema | `bluetti_sdk/schemas/block_15600_declarative.py` | 7 fields, partial |
| PHASE2 matrix entry | `docs/plans/PHASE2-SCHEMA-COVERAGE-MATRIX.md` line 195 | Needs "4→7" fix |
