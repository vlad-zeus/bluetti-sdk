# Block 15600 — Expanded Evidence Verdict
**Sprint**: 15600 Expanded Evidence Hunt (Strict Mode, Multi-Agent)
**Date**: 2026-02-17
**Adjudicator**: Agent R

---

## 1. Agent Reports Reviewed

| Agent | File | Approach | DC1 Verdict | DC2 Verdict |
|---|---|---|---|---|
| Agent A — Call-Graph Hunt | `docs/re/agents/15600-agent-a-callgraph.md` | Exhaustive corpus-wide grep for all occurrences of `outputCurrentDC1/2`; traced every caller from `getOutputCurrentDC1/2()` and `setOutputCurrentDC1/2()` | UNKNOWN — zero external callers | UNKNOWN — zero external callers |
| Agent B — UI/Resource Semantic Miner | `docs/re/agents/15600-agent-b-ui-semantic.md` | Searched string resources, all layout XML files, databinding generated classes, all DCDC UI activities and fragments for DC1/DC2 display or input elements | ABSENT from all UI layers | ABSENT from all UI layers |
| Agent C — Bytecode Arithmetic Hunter | `docs/re/agents/15600-agent-c-opcode-arith.md` | Global search for all `div-int/lit8`, `div-float`, `mul-float` opcodes in every DCDC-related smali file; traced operand register provenance | NO arithmetic found for DC1/DC2 anywhere | NO arithmetic found for DC1/DC2 anywhere |
| Agent D — Cross-Module Correlator | `docs/re/agents/15600-agent-d-crossmodule.md` | Investigated 15500 baseInfoParse vs 15600 settingsInfoParse linkage; searched write path (ProtocolParserV2, addSetTask); reconstructed block 15600 word layout | NO write path, NO display path, NO cross-module scale link found | NO write path, NO display path, NO cross-module scale link found |

All four agents converged on the same factual finding: `getOutputCurrentDC1()` and `getOutputCurrentDC2()` have zero external callers anywhere in the entire APK smali corpus. No scale arithmetic was found applied to either field outside the bean itself.

---

## 2. Cross-Agent Consistency Check

### Claim: "getOutputCurrentDC1/2() are never called outside DCDCSettings.smali"

| Agent | Finding | Consistent? |
|---|---|---|
| Agent A | "getOutputCurrentDC1 and getOutputCurrentDC2 are NEVER called outside DCDCSettings.smali" — confirmed by exhaustive corpus grep | YES |
| Agent B | "outputCurrentDC1 is never read by any UI component in the searched scope" | YES |
| Agent C | "getOutputCurrentDC1()I... never called from any UI activity in the corpus" | YES |
| Agent D | "getOutputCurrentDC1() and setOutputCurrentDC1() are only referenced in DCDCParser.smali and DCDCSettings.smali" | YES |

All four agents agree. No conflict.

### Claim: "setOutputCurrentDC1() is called only from DCDCParser.smali:2086 with no scale arithmetic"

| Agent | Finding | Consistent? |
|---|---|---|
| Agent A | `DCDCParser.smali:2086` calls `setOutputCurrentDC1(I)V`; no `div-int/lit8` before the call | YES |
| Agent B | "list.get(4) + list.get(5) → Integer.parseInt(hex, 16) → setOutputCurrentDC1()" (line 2086); no scaling | YES |
| Agent C | "setOutputCurrentDC1(I)V is called only from DCDCParser.smali line 2086... with no arithmetic scaling applied before or after" | YES |
| Agent D | "settingsInfoParse raw-int assignment at lines 2086, 2162" with no scaling | YES |

All four agents agree. No conflict.

### Claim: "outputCurrentDC3 has PROVEN scale = 0.1 A/LSB via direct arithmetic"

| Agent | Key refs | Consistent? |
|---|---|---|
| Agent A | `DCDCSettingsAdvActivity.smali:794-802`; `DeviceSettingsSingleRangeActivity.smali:574` | YES |
| Agent B | `DCDCSettingsAdvActivity.smali:800-802` (`div-float/2addr` with `0x41200000 = 10.0f`); `DeviceSettingsSingleRangeActivity.smali:736` (factor=10.0f) | YES |
| Agent C | `DCDCSettingsAdvActivity.smali:794-802` confirmed; `DeviceSettingsSingleRangeActivity.smali:574` (`div-int/lit8 0xa`) confirmed | YES |
| Agent D | `DCDCSettingsAdvActivity.smali:794-822`; `DeviceSettingsSingleRangeActivity.smali:716-748` (factor=10.0f); write-back `×10` at lines 2224-2238 | YES |

All four agents agree. No conflict.

### Claim: "no DCDC_CURRENT_SET_DC1 or DCDC_CURRENT_SET_DC2 register exists"

| Agent | Finding | Consistent? |
|---|---|---|
| Agent B | "No DCDC_CURRENT_SET_DC1 or DCDC_CURRENT_SET_DC2 exists in ProtocolAddrV2" | YES |
| Agent D | "A search across all smali files for 0x3cf2, 0x3cf3, 0x3cf4, 0x3cf5 returned zero DCDC-related matches" for write commands | YES |

Two agents investigated, both agree. No conflict.

### Claim: "DC1/DC2 scale is 0.1 A/LSB by structural analogy with DC3" (classification as "strongly inferred" only)

| Agent | How they framed it | Consistent with strict-mode rules? |
|---|---|---|
| Agent A | "By analogy with DC3's confirmed scale=0.1, DC1/DC2 are likely scale=0.1 — but this cannot be proven" | YES — correctly marked as analogy |
| Agent B | "Scale 0.1 A/LSB should be applied to DC1/DC2 pending protocol-layer confirmation" | BORDERLINE — reads as a recommendation to apply, not a proof claim |
| Agent C | "Inferred scale: 10 (divide by 10 to get Amperes)" — marked as indirect | YES — explicitly marked indirect |
| Agent D | "strongly inferred... not proven" | YES — correctly distinguished |

No factual conflict. Agent B's recommendation language is softer than "proven" but does not claim proof status. The structural-analogy argument is internally consistent across all four agents. However, under the adjudication rules (Rule 4: structural analogy is NOT proof), this claim cannot be elevated to PROVEN.

### Conflicts Found

None. All four agents agree on every factual claim. The agents also agree on the status of the structural analogy: it is a strong inference, not proof.

---

## 3. Proven Claims (with proof chain)

### voltSetDC1/2/3 (confirmed from prior sprint)

**Status: PROVEN (prior sprint)**

All three voltage setpoint fields were proven in sprint `15600-SCALE-HUNT-A1-A2.md`:

- `voltSetDC1`: read path `ChargerSettingsVoltageActivityV2.smali:553-561` (`getVoltSetDC1()I` → `int-to-float` → `div-float/2addr` with `0x41200000` = 10.0f → display "V"); write path lines 712-720 (`valueSet_V * 10 → raw int`). Corroborated by `DCDCHomeActivity.smali:1130-1138`.
- `voltSetDC2`: read path `ChargerSettingsVoltageActivityV4.smali:1035-1043` (same arithmetic pattern); multiple corroborating files including `DeviceChargerSettingVoltageFragment.smali:404-412`, `ChargerSettingsPowerActivity.smali:828-836`, `DeviceConnSettingsProtocolV2ActivityUI2.smali:2457-2465`.
- `voltSetDC3`: read path `ChargerGenSettingsActivity.smali:1294-1302` (`getVoltSetDC3()I` → `int-to-float` → `div-float/2addr` with 10.0f → display "V").

Scale = 0.1 V/LSB for all three. Bean setters are pure `iput` (no arithmetic in bean). Scale applied only at caller sites.

### outputCurrentDC3 (confirmed from prior sprint)

**Status: PROVEN (prior sprint)**

- Display read path: `DCDCSettingsAdvActivity.smali:794-802` — `getOutputCurrentDC3()I` → `int-to-float v4, v4` (line 798) → `const/high16 v6, 0x41200000` (10.0f, line 800) → `div-float/2addr v4, v6` (line 802) → appended with "A" unit string → `KeyValueVerticalView.setValue()`.
- Range-check read: `DeviceSettingsSingleRangeActivity.smali:570-574` — `getOutputCurrentDC3()I` → `div-int/lit8 v0, v0, 0xa` (÷10 integer, line 574) → compared against seekbar `maxValue`.
- Write path: `DeviceSettingsSingleRangeActivity$dcdcSettingsInfoHandle$1.smali:156-196` — `getMaxValue()I` → `int-to-float` → `mul-float/2addr` with `getFactor()F` (= 10.0f) → `addSetTask` to address `0x3CF6` (= 15606).

Scale = 0.1 A/LSB confirmed by both display (÷10) and write (×10) paths. Target register `0x3CF6` is confirmed word offset +6 of block `0x3CF0` (15600), placing `outputCurrentDC3` at byte offset 12 in the packet.

### outputCurrentDC1 — new findings

**NOT PROVEN — no direct evidence found.**

All four agents searched exhaustively. The finding is unanimous and consistent:

- `getOutputCurrentDC1()I` (defined at `DCDCSettings.smali:3404`) is called from ZERO locations outside `DCDCSettings.smali` itself.
- `setOutputCurrentDC1(I)V` (defined at `DCDCSettings.smali:4338`) is called from exactly one external location: `DCDCParser.smali:2086`, where it receives the output of `Integer.parseInt(hexStr, 16)` with no arithmetic applied before or after.
- No `div-int/lit8 0xa`, `div-float/2addr`, `mul-float`, or any other scale-related arithmetic opcode is applied to the value of `outputCurrentDC1` anywhere in the corpus.
- No string resource, layout view, databinding field, ViewModel, Fragment, Activity, or lambda file references `outputCurrentDC1` or `getOutputCurrentDC1` except within `DCDCSettings.smali`.
- No dedicated write register (`DCDC_CURRENT_SET_DC1`) exists in `ProtocolAddrV2.smali`. No `addSetTask` or `commonSetTask` targeting address `0x3CF2` (the expected word offset for DC1 current) was found in any file.

Per adjudication Rule 2, this is classified **UNKNOWN**: absence confirmed by exhaustive search.

### outputCurrentDC2 — new findings

**NOT PROVEN — no direct evidence found.**

Identical situation to DC1. Unanimous finding across all four agents:

- `getOutputCurrentDC2()I` (defined at `DCDCSettings.smali:3413`) is called from ZERO locations outside `DCDCSettings.smali`.
- `setOutputCurrentDC2(I)V` (defined at `DCDCSettings.smali:4347`) is called from exactly one external location: `DCDCParser.smali:2162`, with no arithmetic applied.
- No scale arithmetic found for `outputCurrentDC2` anywhere in the corpus.
- No dedicated UI view, write register, or display path found for DC2 current.
- No `addSetTask` targeting address `0x3CF4` (expected word offset for DC2 current) found in any file.

Per adjudication Rule 2, this is classified **UNKNOWN**: absence confirmed by exhaustive search.

---

## 4. Rejected Claims

### Claim: "Scale 0.1 A/LSB should be applied to DC1/DC2" (Agent B conclusion paragraph)

**Rejected as PROVEN.** Agent B's bottom-line statement "Scale 0.1 A/LSB should be applied to DC1/DC2 pending protocol-layer confirmation" was framed as a recommendation. However, the supporting argument is purely structural analogy: DC1/DC2 are parsed identically to DC3, they share the same bean, the hashCode/equals/toString treat them symmetrically. No file:line reference to arithmetic applied to `outputCurrentDC1` or `outputCurrentDC2` was provided by Agent B — because none exists. Per Rule 4 (structural analogy is NOT proof) and Rule 5 (claims without file:line references are rejected as evidence), this cannot be elevated above "strongly inferred."

### Claim: "Firmware treats all three DC output current fields symmetrically" (Agents B and C)

**Accepted as description, rejected as proof.** The structural symmetry observation is accurate: all three fields are `I` type, parsed by identical `Integer.parseInt(hex, 16)` calls in `DCDCParser.settingsInfoParse`, stored by identical pure-`iput` setters, and appear in parallel positions in the bean constructor. This accurately describes the code structure. However, it does not constitute proof of scale for DC1/DC2 because scale is applied only at caller sites, and there are no caller sites for DC1/DC2. The claim stands as accurate description but is rejected as evidence of scale.

### Claim: "VoltSetDC1 ÷10 convention confirms the firmware uses scale=10 for all DCDCSettings electrical fields" (Agent C)

**Rejected as proof.** Agent C correctly identifies that `voltSetDC1` uses ÷10 at `DCDCHomeActivity.smali:1130-1138` and infers this corroborates a scale convention. This is an accurate generalization across the proven fields (voltSetDC1/2/3, outputCurrentDC3 all use scale=0.1) but does not constitute direct arithmetic evidence for `outputCurrentDC1/2`. Rejected per Rule 4.

### Claim: "15500 dcOutputCurrent uses ÷10 → implies 15600 DC1/DC2 current scale is consistent" (Agent D)

**Rejected as proof.** Agent D correctly identifies that `DCDCParser.baseInfoParse:351` applies `div-float/2addr` with `0x41200000` (÷10) to set `DCDCInfo.setDcOutputCurrent(F)`. However, `DCDCInfo.dcOutputCurrent` is the total live-measured DC output current (a separate bean, separate data path, separate protocol block 15500). There is no code that compares or co-processes this value against `DCDCSettings.outputCurrentDC1/2`. Agent D itself notes: "getOutputCurrentDC1() never called in DCDCHomeActivity — NO LINKAGE." Rejected per Rule 4.

---

## 5. Final Status Table

| Field | Status | Scale | Evidence quality | Proof refs |
|---|---|---|---|---|
| voltSetDC1 | PROVEN | 0.1 V/LSB | Direct smali (read + write) | `ChargerSettingsVoltageActivityV2.smali:553-561, 712-720`; `DCDCHomeActivity.smali:1130-1138` |
| voltSetDC2 | PROVEN | 0.1 V/LSB | Direct smali (multiple callers) | `ChargerSettingsVoltageActivityV4.smali:1035-1043`; `DeviceChargerSettingVoltageFragment.smali:404-412`; `ChargerSettingsPowerActivity.smali:828-836` |
| voltSetDC3 | PROVEN | 0.1 V/LSB | Direct smali | `ChargerGenSettingsActivity.smali:1294-1302` |
| outputCurrentDC3 | PROVEN | 0.1 A/LSB | Direct smali (display + write) | `DCDCSettingsAdvActivity.smali:794-802`; `DeviceSettingsSingleRangeActivity.smali:574`; `dcdcSettingsInfoHandle$1.smali:156-196` |
| outputCurrentDC1 | UNKNOWN | 0.1 A/LSB (strongly inferred only) | Structural analogy; no direct arithmetic evidence | None — field has zero external callers in corpus |
| outputCurrentDC2 | UNKNOWN | 0.1 A/LSB (strongly inferred only) | Structural analogy; no direct arithmetic evidence | None — field has zero external callers in corpus |

---

## 6. What Was Searched (Exhaustiveness Assessment)

The combined search scope across all four agents was comprehensive. The conclusion that no direct evidence exists is supported by multiple independent search strategies all returning negative results for DC1/DC2.

| Search scope | Searched by | Result |
|---|---|---|
| All DCDC UI activities (8 files): `DCDCSettingsAdvActivity`, `DCDCHomeActivity`, `DCDCSettingsVoltageActivity`, `DCDCCableSettingsActivity`, `DCDCInputDetailsActivity`, `DCDCParallelCommunicationActivity`, `DCDCChgModeActivity`, `DCDCChgModeSelectActivity` | Agent A + C | NEGATIVE for DC1/DC2 |
| `DeviceSettingsSingleRangeActivity.smali` (classes4, 1801 lines) | Agent A + C | NEGATIVE for DC1/DC2; DC3 confirmed |
| All DCDC lambda/inner-class synthetic files | Agent A | NEGATIVE (exhaustive glob + grep) |
| `DeviceEnergyViewDCDC.smali` | Agent A + C | NEGATIVE |
| `DeviceChargerSettingVoltageFragment.smali` | Agent A + B | NEGATIVE |
| String resources (`strings.xml`) | Agent B | NEGATIVE — no DC1/DC2 current string keys |
| Layout XML files (`device_dcdc_settings_adv_activity.xml`, `device_dcdc_home_activity.xml`) | Agent B | NEGATIVE — no DC1/DC2 current views |
| `DeviceDcdcSettingsAdvActivityBinding.smali` (databinding) | Agent B | NEGATIVE — no `kvvMaxOutputCurrentDC1/DC2` |
| `ProtocolAddrV2.smali` (register map) | Agent B + D | NEGATIVE — no `DCDC_CURRENT_SET_DC1/DC2` constant |
| `DCDCParser.smali` settingsInfoParse write path | Agent A + B + C + D | NEGATIVE — raw `parseInt` only, no scaling for DC1/DC2 |
| `ProtocolParserV2.smali` write path (all block 0x3CF0 handling) | Agent D | NEGATIVE — only returns data-length for read task |
| Corpus-wide grep for `outputCurrentDC1` (all smali_classes* dirs) | Agent A | NEGATIVE outside DCDCSettings.smali + DCDCParser.smali |
| Corpus-wide grep for `outputCurrentDC2` (all smali_classes* dirs) | Agent A | NEGATIVE outside DCDCSettings.smali + DCDCParser.smali |
| Corpus-wide search for `getOutputCurrentDC` variants | Agent A + C | DC1/DC2 getters defined but never invoked externally |
| Corpus-wide search for `setOutputCurrentDC1/DC2` | Agent A + C | Called only from `DCDCParser.smali:2086, 2162` |
| Corpus-wide `div-int/lit8` opcode search (all DCDC files) | Agent C | No `0xa` division on DC1/DC2 found anywhere |
| Corpus-wide `div-float/mul-float` opcode search | Agent C | No float arithmetic on DC1/DC2 found anywhere |
| `addSetTask` / `commonSetTask` targeting address `0x3CF2` or `0x3CF4` | Agent D | NEGATIVE — no write path to DC1/DC2 current addresses |
| 15500 baseInfoParse vs 15600 settingsInfoParse linkage | Agent D | NO LINKAGE — fields are separate beans, no co-display logic |
| ViewModel files (all `*DCDC*ViewModel*`) | Agent A | NO VIEWMODEL FILES FOUND in corpus |
| Charger voltage activities (`ChargerSettingsVoltageActivityV2/V4`, `ChargerGenSettingsActivity`, `ChargerSettingsPowerActivity`) | Prior sprint (A1-A2) | NEGATIVE for DC1/DC2 current; voltage fields confirmed |

**Exhaustiveness Assessment**: The search is genuinely exhaustive by all practical measures. The corpus-wide grep approach used by Agent A (searching every smali file in all `smali_classes*` directories by field name string) is definitive: if any file in the APK contained the string `outputCurrentDC1` or `getOutputCurrentDC1`, it would have been found. The result — hits only in `DCDCSettings.smali` (the bean) and `DCDCParser.smali` (the parser) — confirms these fields are present but unused in the UI layer.

**What could still be checked** (remaining theoretical gaps):

1. **Obfuscated/reflected call sites**: If the APK uses runtime reflection to call `getOutputCurrentDC1()` by name, a string search would miss it. This is unlikely given the Kotlin data class structure but cannot be ruled out from static analysis alone.
2. **Native code layer**: If there is a native `.so` library that reads the `DCDCSettings` Parcelable (Agent A confirmed `writeToParcel()` includes DC1/DC2 at lines 4646 and 4650), scale conversion could occur in native code. Agent D confirmed the `writeToParcel()` paths exist but no analysis of native libraries was performed.
3. **Firmware/BLE protocol documentation**: The device firmware itself may apply a different scale when interpreting these fields. The APK evidence tells us only what the Android UI layer does, not what the DCDC module firmware does with the raw values.
4. **Physical device test**: Reading a live device to compare raw 15600 values against known settings (the Step 1 protocol in `15600-DEVICE-VALIDATION.md`) remains the most direct resolution path.

---

## 7. Final Decision

**outputCurrentDC1 scale**: UNKNOWN

**outputCurrentDC2 scale**: UNKNOWN

**Rationale**: All four independent agents searched the entire APK smali corpus exhaustively using complementary methods (call-graph tracing, UI/resource mining, opcode arithmetic hunting, cross-module correlation) and found zero direct evidence — no arithmetic operation, no display site, no write path — applied to `outputCurrentDC1` or `outputCurrentDC2` outside the bean itself. The structural analogy with `outputCurrentDC3` (proven scale = 0.1 A/LSB) is a strong inference but does not meet the PROVEN threshold under strict-mode adjudication rules. The fields exist in the bean and are populated by the parser but appear to have no dedicated UI in the current firmware version.

**Remaining minimal device tests**:

Since the status is UNKNOWN, device testing is required to resolve. The following tests are sufficient and are already specified in `15600-DEVICE-VALIDATION.md` (Step 1):

1. **Read-back test for outputCurrentDC1** (READ-ONLY, safe):
   - Read Block 15600 (`DC_DC_SETTINGS`) raw bytes; extract bytes 4-5 (word offset 2 from base `0x3CF0`); parse as big-endian uint16 → this is the raw `outputCurrentDC1` value.
   - Read Block 15500 (`DC_DC_INFO`) and extract `dc1Current` (per-port DC1 current, type J/long per `DCDCInfo.smali`).
   - If `15600_raw_dc1_current × 0.1 ≈ dc1_current_reading_in_amps` → scale = 0.1 A/LSB confirmed.
   - Also check whether `15600_raw_dc1_current` equals the displayed/configured max current for DC1 on the device front panel (if the device has such a display).

2. **Read-back test for outputCurrentDC2** (READ-ONLY, safe):
   - Same approach: bytes 8-9 of the 15600 packet → raw `outputCurrentDC2`.
   - Compare against Block 15500 `dc2Current`.

3. **Plausibility check**: If the raw value for `outputCurrentDC1` at rest is in the range 0–80, and the device is set to limit DC1 current to approximately (raw × 0.1) amperes, scale = 0.1 A/LSB is confirmed. Raw values in range 0–800 would suggest scale = 1 A/LSB instead.

---

## 8. Recommendation

**B) Schema must remain partial — device test required (UNKNOWN status)**

`outputCurrentDC1` and `outputCurrentDC2` have no direct arithmetic evidence in the smali corpus. Four independent exhaustive searches confirm the absence. The scale cannot be determined from static APK analysis alone.

- The schema field `output_current_dc1` (byte offset 4) and the currently unimplemented `output_current_dc2` (byte offset 8) **must not** receive a `scale(0.1)` transform until device validation is complete.
- Option C (accept structural inference with "inferred" label) is explicitly not recommended per sprint rules and is rejected by this adjudicator.
- The device test protocol in `15600-DEVICE-VALIDATION.md` Step 1 (read-back comparison against Block 15500) is the minimal safe path to resolution. It requires no writes and no changes to device configuration.

---

## Appendix: Note on 15600-DEVICE-VALIDATION.md Blocker Status

The current `15600-DEVICE-VALIDATION.md` (as read 2026-02-17) already reflects the correct state:

- **Closed Blocker (voltSetDC1/2/3)**: The document correctly marks this as "Closed Blocker" with PROVEN status. The prior sprint (A1-A2) findings are sufficient. No update needed for this section.
- **Closed Blocker (outputCurrentDC3)**: Also correctly marked as proven/closed.
- **Open Blocker (outputCurrentDC1/2)**: Correctly marked as open, with hypothesis "Scale = 0.1 A — NOT PROVEN for DC1/DC2." This verdict confirms the open blocker remains open and that the device test specified in Step 1 of the validation protocol is the correct resolution path.

The document does NOT need updating based on the expanded evidence hunt findings — all four agents confirmed what the validation document already states. The "Closed Blocker" sections for voltSetDC and outputCurrentDC3 are accurately marked; the "Open Blocker" for outputCurrentDC1/2 correctly identifies the gap. The schema upgrade criteria in that document (item "outputCurrentDC1/2 scale factors confirmed") remains unmet.
