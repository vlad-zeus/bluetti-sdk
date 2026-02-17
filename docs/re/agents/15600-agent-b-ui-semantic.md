# Agent B — UI/Resource Semantic Miner: outputCurrentDC1/2
**Date**: 2026-02-17

---

## String Resources Analysis

**File searched**: `d:\HomeAssistant\_research\reverse_engineering\bluetti_smali\res\values\strings.xml` (368 KB, too large to read whole, searched via Grep)

**Searches performed**:
- Regex `(current.*dc[12]|dc[12].*current|output.?current)` — no DC1/DC2 specific hits
- `%.1f` format strings — **no matches**
- `(dcdc|dc_dc|dcdcsetting)` — many DCDC error/protect strings, none current-specific for DC1/DC2
- `(current.*limit|limit.*current|max.*current|current.*max)` — AC/Grid current strings only
- `ampere|amps?` — no ampere unit labels for DCDC channels

**Relevant hits found**:

| string key | value | relevance |
|---|---|---|
| `max_chg_current` | 最大充电电流 | title of the DC3 max current KVV view (layout line 10) |
| `max_output_current` | 最大输出电流 | generic max output current |
| `output_current` | Current | generic; no channel qualifier |
| `max_chg_current_msg1` | "The current exceeds the limit for Normal Mode. Please configure it in the Advanced Mode." | shown with `%dA` argument = **55** (0x37) — this is the DC3 normal-mode max |
| `max_chg_current_desc1` | "Set the maximum charging current according to the safe range of the target device and cable." | description for DC3 max current slider |

**Finding**: No DC1-specific or DC2-specific current string keys exist. All DCDC current string resources reference DC3's `kvv_max_output_current` view exclusively.

---

## Layout Analysis

### `device_dcdc_settings_adv_activity.xml`
**File**: `d:\HomeAssistant\_research\reverse_engineering\bluetti_smali\res\layout\device_dcdc_settings_adv_activity.xml`

Views present:

| id | type | title string | default value | DC channel |
|---|---|---|---|---|
| `item_pv_enable` | SettingItemView | `@string/device_photovoltaic_enable` | — | DC ctrl enable |
| `kvv_self_adaption_mode` | KeyValueVerticalView | `@string/device_self_adaption_mode` | `@string/device_turn_off` | — |
| `kvv_max_output_current` | KeyValueVerticalView | `@string/max_chg_current` | `0A` | **DC3 only** |
| `kvv_chg_mode` | KeyValueVerticalView | `@string/device_charging_mode` | `--` | DC3 chg mode |
| `kvv_cable_settings` | KeyValueVerticalView | `@string/device_cable_settings` | `--` | — |
| `item_parallel_communication` | SettingItemView | `@string/device_parallel_communication_mode` | — | — |
| `btn_factory_reset` | CustomButton | `@string/device_factory_reset` | — | — |

**Finding**: There is ONE max-output-current view (`kvv_max_output_current`) and it is exclusively for DC3 (confirmed by smali code). No `kvv_max_output_current_dc1`, no `kvv_max_output_current_dc2`, no seekbar/slider for DC1 or DC2 current.

### `device_dcdc_home_activity.xml`
**File**: `d:\HomeAssistant\_research\reverse_engineering\bluetti_smali\res\layout\device_dcdc_home_activity.xml`

Contains: energy view (charger), SN view, DC ctrl switch, silent mode, `kvv_chg_volt` (charging voltage). No DC current input views.

### `device_dcdc_cable_settings_activity.xml`
Not separately analyzed (not opened); cable settings are not current-related.

---

## DCDCSettingsAdvActivity Analysis (DC3 pattern + DC1/DC2 search)

**File**: `d:\HomeAssistant\_research\reverse_engineering\bluetti_smali\smali_classes5\net\poweroak\bluetticloud\ui\connectv2\activity\DCDCSettingsAdvActivity.smali`

### DC3 confirmed pattern (lines 780–822)

```smali
.line 165
iget-object v0, v0, ...->kvvMaxOutputCurrent:...KeyValueVerticalView;

iget-object v4, p0, ...->dcdcSettings:...DCDCSettings;
invoke-virtual {v4}, ...DCDCSettings;->getOutputCurrentDC3()I  ; line 794
move-result v4
int-to-float v4, v4
const/high16 v6, 0x41200000    # 10.0f                       ; line 800
div-float/2addr v4, v6                                         ; line 802  ← divide by 10
...
const-string v6, "A"                                           ; line 812  ← unit = Amperes
...append(F)...append("A")...
invoke-virtual {v0, v4}, ...KeyValueVerticalView;->setValue(...)V ; line 822
```

Pattern: `raw_int → float → ÷ 10.0f → append "A"` → display string. Scale confirmed = 0.1 A/LSB.

### DC1/DC2 search results

Searches in DCDCSettingsAdvActivity.smali:
- `outputCurrentDC[12]` — **NO MATCHES**
- `getOutputCurrentDC[12]` — **NO MATCHES**
- `div-float` — only **one** instance: line 802 (DC3)
- `0x41200000` — only **one** instance: line 800 (DC3)
- `kvvMaxOutputCurrent` — lines 790, 1207, 1209, 1683, 1963, 2013 — all are DC3

**Finding**: `outputCurrentDC1` and `outputCurrentDC2` are **NEVER READ** in `DCDCSettingsAdvActivity`. The activity only displays DC3's current via the single `kvvMaxOutputCurrent` view. DC1 and DC2 current values are stored in `DCDCSettings` but have no dedicated display in this activity.

---

## DCDCSettingsVoltageActivity Analysis

**File**: `d:\HomeAssistant\_research\reverse_engineering\bluetti_smali\smali_classes5\net\poweroak\bluetticloud\ui\connectv2\activity\DCDCSettingsVoltageActivity.smali`

Binding used: `DeviceChargerSettingVoltActivityBinding`

- `outputCurrentDC1/DC2` — **NO MATCHES**
- One `0x41200000` (= 10.0f) found at line 1125; used with **unit "V"** (voltage, not current):

```smali
.line 63
iget-object v0, v1, ...->viewRangeSetting:...DeviceSettingRangeValueLayout;
const/high16 v1, 0x41200000    # 10.0f          ; line 1125
invoke-virtual {v0, v1}, ...->setFactor(F)V      ; line 1128
const-string v1, "V"                              ; line 1131
invoke-virtual {v0, v1}, ...->setUnit(Ljava/lang/String;)V
```

**Finding**: `DCDCSettingsVoltageActivity` handles only **voltage** settings (unit = "V", factor = 10.0f → 0.1 V/LSB). No current DC1/DC2 handling whatsoever.

---

## Fragment Analysis

**File**: `d:\HomeAssistant\_research\reverse_engineering\bluetti_smali\smali_classes5\net\poweroak\bluetticloud\ui\connectv2\fragment\DeviceChargerSettingVoltageFragment.smali`

Searched for `outputCurrentDC[12]` — **NO MATCHES**.

Found `0x41200000` at lines 410, 1328, 1554, 2108:

| line | method context | field accessed | purpose |
|---|---|---|---|
| 410 | `update()` lambda | `getVoltSetDC2()` | VoltSetDC2 ÷ 10 → `setValueSet(F)` for voltage display |
| 1328 | `initView$1$5$1` | parameter to `showSetupValueDialog` | voltage dialog factor = 10.0f |
| 1554 | `update()` | `getVoltSetDC2()` | VoltSetDC2 ÷ 10 → `setValueSet(F)` |
| 2108 | `update()` (another branch) | `getVoltSetDC2()` | same: VoltSetDC2 ÷ 10 → `setValueSet(F)` |

All `div-float/2addr` ÷ 10.0f in this fragment operate on `VoltSetDC2`, not on `outputCurrentDC1/DC2`. The fragment is voltage-only.

**Finding**: `DeviceChargerSettingVoltageFragment` does **not** display or handle `outputCurrentDC1` or `outputCurrentDC2` at all.

---

## DataBinding Analysis

**File**: `d:\HomeAssistant\_research\reverse_engineering\bluetti_smali\smali_classes4\net\poweroak\bluetticloud\databinding\DeviceDcdcSettingsAdvActivityBinding.smali`

View fields:
```
kvvCableSettings    — cable settings
kvvChgMode          — charging mode (DC3)
kvvMaxOutputCurrent — max output current (DC3 ONLY, confirmed by smali)
kvvSelfAdaptionMode — self-adaption mode
itemPvEnable        — PV enable (DC ctrl)
itemParallelCommunication
itemUpgrade
btnFactoryReset
```

No `kvvMaxOutputCurrentDC1`, no `kvvMaxOutputCurrentDC2`, no current-input views for DC1/DC2.

**Finding**: The databinding generated file for the DCDC Advanced Settings activity confirms there are **no view-to-field mappings** for DC1 or DC2 current in this UI layer.

---

## Key Indirect Evidence: DeviceSettingsSingleRangeActivity + ProtocolAddrV2

While no DC1/DC2 current display was found in any UI component, the following evidence from the range settings subsystem is highly relevant as a structural analog.

### ProtocolAddrV2 register map
**File**: `d:\HomeAssistant\_research\reverse_engineering\bluetti_smali\smali_classes5\net\poweroak\bluetticloud\ui\connectv2\tools\ProtocolAddrV2.smali`

```smali
.field public static final DCDC_SETTINGS:I = 0x3cf0          ; = 15600 — the bulk settings packet
.field public static final DCDC_CURRENT_SET_DC3:I = 0x3cf6   ; = 15606 — DC3 individual write register
.field public static final DCDC_VOLT_SET_DC2:I = 0x3cf3      ; = 15603
.field public static final DCDC_CHG_MODE_1:I = 0x3cfe        ; = 15614
```

**No `DCDC_CURRENT_SET_DC1` or `DCDC_CURRENT_SET_DC2` exists** in ProtocolAddrV2. DC1 and DC2 current can only be written via the bulk `DCDC_SETTINGS = 0x3cf0` packet.

### DeviceRangeSettingBean for `dcdc_max_chg_current` (DC3)
**File**: `d:\HomeAssistant\_research\reverse_engineering\bluetti_smali\smali_classes4\net\poweroak\bluetticloud\ui\connect\activity\DeviceSettingsSingleRangeActivity.smali`, lines 714–748

Constructor call:
```smali
const/4  v3,  0x0        # notes = null
const/4  v4,  0x0        # funcDesc = null
const/4  v5,  0x1        # isSupportInput = true
const/4  v6,  0x1        # seekBarVisible = true
const/4  v7,  0x1        # (unused default param)
const/16 v8,  0x37       # minValue = 0x37 = 55  (UI slider max in normal mode, in A)
const-string v9, "A"     # unit = "A"
const/high16 v10, 0x41200000  # factor = 10.0f
const/4  v11, 0x1        # numOfDecimals = 1
const/16 v12, 0x3cf6     # regAddr = 0x3CF6 = 15606 (= DCDC_CURRENT_SET_DC3)
const/16 v15, 0xc03      # bitLen = 0xC03 = 3075
```

The `DeviceRangeSettingBean` constructor signature (from d2 metadata):
`(notes, funcDesc, isSupportInput, seekBarVisible, minValue, maxValue, unit, factor, numOfDecimals, regAddr, bitLen, bitShift)`

So `factor = 10.0f` is the UI-to-register multiplier. Raw register value = UI_value_in_A × 10.

**Write-back confirmation** (`dcdcSettingsInfoHandle$1.smali`, lines 156–196):
```smali
invoke-virtual {p1}, ...->getMaxValue()I     ; get slider value in "tenths of amps"
int-to-float p1, p1
invoke-virtual {p0}, ...->getFactor()F       ; = 10.0f
mul-float/2addr p1, p0                       ; UI_value × 10.0 = raw register value
float-to-int v2, p1
const/16 v1, 0x3cf6                          ; regAddr = DCDC_CURRENT_SET_DC3
invoke-static ...addSetTask...               ; write to register
```

This confirms: **raw register value = displayed_A × 10**, i.e., **scale = 0.1 A/LSB** for the DC3 current register.

### Normal vs Advanced mode max values (lines 2129–2138)
```smali
if advMode:
    const/16 v3, 0x50    # 80 (max in adv mode = 80 raw = 8.0 A displayed)
else:
    const/16 v3, 0x37    # 55 (max in normal mode = 55 raw = 5.5 A displayed)
invoke-virtual {v0, v3}, ...setMaxValue(I)V
```

With `factor = 10.0f`: 55 raw = 5.5 A, 80 raw = 8.0 A. Both physically plausible DC charging current limits.

### DCDCParser byte-index mapping
**File**: `d:\HomeAssistant\_research\reverse_engineering\bluetti_smali\smali_classes5\net\poweroak\bluetticloud\ui\connectv2\tools\DCDCParser.smali`, lines 2045–2086, 2125–2162

- `list.get(4)` + `list.get(5)` → `Integer.parseInt(hex, 16)` → `setOutputCurrentDC1()` (line 2086)
- `list.get(8)` + `list.get(9)` → `Integer.parseInt(hex, 16)` → `setOutputCurrentDC2()` (line 2162)
- `list.get(12)` + `list.get(13)` → `Integer.parseInt(hex, 16)` → `setOutputCurrentDC3()` (line 2238)

The outer list is the raw hex byte stream of packet 0x3CF0 (= 15600), each list element = one byte as a 2-char hex string. This exactly matches the known byte positions: DC1 at bytes 4–5, DC2 at bytes 8–9, DC3 at bytes 12–13.

All three fields (`outputCurrentDC1`, `outputCurrentDC2`, `outputCurrentDC3`) are parsed with **identical code patterns** — same `Integer.parseInt(concat, 16)` method, no scaling applied during parsing. The raw integer value is stored directly.

---

## UI Evidence Table

| ui_field_label | linked_to | conversion_found | refs | confidence |
|---|---|---|---|---|
| `kvv_max_output_current` / "Max Charging Current" | `DCDCSettings.getOutputCurrentDC3()` | `int_to_float` → `÷ 10.0f` → append "A" | `DCDCSettingsAdvActivity.smali:790-822` | PROVEN (DC3) |
| Range slider `dcdc_max_chg_current` | register `0x3CF6` = DCDC_CURRENT_SET_DC3 | `DeviceRangeSettingBean.factor = 10.0f`, unit = "A" | `DeviceSettingsSingleRangeActivity.smali:714-748`, `dcdcSettingsInfoHandle$1.smali:190` | PROVEN (DC3) |
| (no view exists) | `DCDCSettings.outputCurrentDC1` | no UI display found | Searched: DCDCSettingsAdvActivity, DCDCSettingsVoltageActivity, DeviceChargerSettingVoltageFragment, DeviceDcdcSettingsAdvActivityBinding | ABSENT |
| (no view exists) | `DCDCSettings.outputCurrentDC2` | no UI display found | Same search scope as DC1 | ABSENT |
| "A" unit label | All DCDC current displays | Unit = "A" (Amperes) | `DCDCSettingsAdvActivity.smali:812`, `DeviceSettingsSingleRangeActivity.smali:734` | CONFIRMED |

---

## Structural Symmetry Argument

All three DC channels (DC1, DC2, DC3) are parsed by `DCDCParser.smali` using **identical code patterns**:
1. Concatenate byte[n] + byte[n+1] as hex string
2. `Integer.parseInt(hex, 16)` to get raw int
3. `setOutputCurrentDC{1,2,3}(raw_int)` — stored as-is, **no scaling in parser**

The only scaling occurs at the display/write layer. For DC3:
- Display: `raw_int / 10.0f` → shown as float Amps
- Write: `slider_value_A × 10.0f` → raw register value

DC1 and DC2 have **no dedicated UI display** found in the searched codebase. They are part of the bulk `DCDC_SETTINGS` write only. The firmware treats all three DC output current fields symmetrically in the data model (`DCDCSettings.smali` hash/equals/toString treat them equivalently at lines 3740–3800).

---

## Verdict

- **DC1 current UI evidence**: ABSENT — `outputCurrentDC1` is never read by any UI component in the searched scope. No dedicated display view, no separate write register (no `DCDC_CURRENT_SET_DC1` in ProtocolAddrV2).

- **DC2 current UI evidence**: ABSENT — same as DC1. `outputCurrentDC2` has no UI display and no dedicated write register.

- **Scale implied by UI (for DC3, used as structural analog)**: **0.1 A/LSB** — proven by:
  1. `DCDCSettingsAdvActivity.smali:800-802`: `div-float/2addr v4, v6` where `v6 = 0x41200000 = 10.0f`
  2. `DeviceSettingsSingleRangeActivity.smali:736`: `DeviceRangeSettingBean.factor = 10.0f`, `unit = "A"`
  3. `dcdcSettingsInfoHandle$1.smali:178-184`: write-back uses `getMaxValue() * getFactor()` where factor = 10.0f, writing to register `0x3CF6`

- **Scale for DC1/DC2 (inferred, NOT directly proven via UI)**: **0.1 A/LSB** — strongly implied by:
  1. Symmetric parsing pattern with DC3 in DCDCParser (identical code structure for all three channels)
  2. Symmetric data model treatment in DCDCSettings bean
  3. No counter-evidence (no different scale factor found anywhere for DC1/DC2)
  4. Physical plausibility: DC charging current limits in the range of 0–55 raw (= 0–5.5 A) or 0–80 raw (= 0–8.0 A) are consistent with the device hardware specs

**Bottom line**: UI evidence directly proves 0.1 A/LSB for DC3 current. DC1/DC2 are absent from UI but structurally identical to DC3 in every measurable dimension. Scale 0.1 A/LSB should be applied to DC1/DC2 pending protocol-layer confirmation.
