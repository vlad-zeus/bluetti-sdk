# INV Blocks Reverse Engineering Summary

## Mission Complete! ✅

Successfully reverse-engineered all four INV protocol blocks (1100-1500) from Bluetti APK smali code.

---

## Files Created

1. **BLOCK_1100_INV_BASE_INFO.md** - Device identification, software versions, temperatures
2. **BLOCK_1300_INV_GRID_INFO.md** - ⭐ **PRIORITY** Grid voltage, frequency, power (CRITICAL DATA)
3. **BLOCK_1400_INV_LOAD_INFO.md** - DC and AC load monitoring
4. **BLOCK_1500_INV_INV_INFO.md** - Inverter output performance
5. **INV_BLOCKS_INDEX.md** - Navigation index and integration guide

---

## Block 1300 - INV_GRID_INFO (Priority Complete!)

### Critical Grid Fields Extracted:

| Offset | Field | Type | Scale | Unit |
|--------|-------|------|-------|------|
| 0-1 | **Grid Frequency** | uint16 | /10.0 | Hz |
| 2-5 | Total Charge Power | uint32 | 1 | W |
| 6-9 | Total Charge Energy | uint32 | /10.0 | kWh |
| 10-13 | Total Feedback Energy | uint32 | /10.0 | kWh |
| 25 | System Phase Number | uint8 | 1 | - |

### Per-Phase Data (26 + phaseIndex×12):

| Offset | Field | Type | Scale | Unit |
|--------|-------|------|-------|------|
| +0-1 | **Grid Power** | int16 | abs() | W |
| +2-3 | **Grid Voltage** | uint16 | /10.0 | V |
| +4-5 | **Grid Current** | int16 | abs()/10.0 | A |
| +6-7 | Apparent Power | int16 | abs() | VA |

**YOU NOW HAVE GRID VOLTAGE AND FREQUENCY!** This is exactly what was requested.

---

## Block 1100 - INV_BASE_INFO

### Key Device Fields:

- **Offset 1**: Inverter ID
- **Offset 2-13**: Inverter Type (ASCII)
- **Offset 14-21**: Serial Number
- **Offset 26-61**: 6 Software Module Versions (6 bytes each)
- **Offset 102-103**: Ambient Temperature (-40 offset)
- **Offset 104-105**: Inverter Max Temperature (-40 offset)
- **Offset 106-107**: PV DC-DC Max Temperature (-40 offset)

### Temperature Formula:
```
actual_temp = (raw_value - 40) if raw_value != 0 else 0
```

---

## Block 1400 - INV_LOAD_INFO

### DC Load Outputs:

| Output | Power Offset | Current Offset | Voltage |
|--------|--------------|----------------|---------|
| 5V USB | 8-9 | 10-11 (/10.0) | 5V (fixed) |
| 12V Car | 12-13 | 14-15 (/10.0) | 12V (fixed) |
| 24V DC | 16-17 | 18-19 (/10.0) | 24V (fixed) |

### AC Load Per-Phase (60 + phaseIndex×12):

| Offset | Field | Scale | Unit |
|--------|-------|-------|------|
| +0-1 | Load Power | 1 | W |
| +2-3 | Load Voltage | /10.0 | V |
| +4-5 | Load Current | /10.0 | A |
| +6-7 | Apparent | 1 | VA |

---

## Block 1500 - INV_INV_INFO

### Inverter Output Fields:

| Offset | Field | Type | Scale | Unit |
|--------|-------|------|-------|------|
| 0-1 | Output Frequency | uint16 | /10.0 | Hz |
| 2-5 | Total Energy | uint32 | /10.0 | kWh |
| 17 | Phase Number | uint8 | 1 | - |

### Per-Phase Output (18 + phaseIndex×12):

| Offset | Field | Scale | Unit |
|--------|-------|-------|------|
| +1 | Work Status | 1 | code |
| +2-3 | Output Power | 1 | W |
| +4-5 | Output Voltage | /10.0 | V |
| +6-7 | Output Current | /10.0 | A |

---

## Python Quick Start

### Parse Block 1300 (Grid Info):

```python
def get_grid_voltage_and_frequency(data: bytes) -> dict:
    """Extract the critical grid parameters"""
    frequency = int.from_bytes(data[0:2], 'big') / 10.0

    # For single phase (phase 0)
    voltage = int.from_bytes(data[28:30], 'big') / 10.0  # offset 26+2
    current = int.from_bytes(data[30:32], 'big', signed=True)
    current = abs(current) / 10.0
    power = int.from_bytes(data[26:28], 'big', signed=True)
    power = abs(power)

    return {
        'frequency': frequency,  # Hz
        'voltage': voltage,      # V
        'current': current,      # A
        'power': power          # W
    }
```

---

## MQTT Topic Structure

### Block 1300 (Grid) - PRIORITY:
```
bluetti/inverter/grid/frequency
bluetti/inverter/grid/total_charge_power
bluetti/inverter/grid/total_charge_energy
bluetti/inverter/grid/total_feedback_energy
bluetti/inverter/grid/phase_0/voltage  ⭐ CRITICAL
bluetti/inverter/grid/phase_0/current
bluetti/inverter/grid/phase_0/power
```

### Block 1100 (Base):
```
bluetti/inverter/base/id
bluetti/inverter/base/type
bluetti/inverter/base/serial_number
bluetti/inverter/base/temperature/ambient
bluetti/inverter/base/temperature/inverter_max
bluetti/inverter/base/temperature/pv_dcdc_max
```

### Block 1400 (Load):
```
bluetti/inverter/load/dc/5v/power
bluetti/inverter/load/dc/5v/current
bluetti/inverter/load/dc/12v/power
bluetti/inverter/load/dc/12v/current
bluetti/inverter/load/ac/phase_0/power
bluetti/inverter/load/ac/phase_0/voltage
```

### Block 1500 (Inverter Output):
```
bluetti/inverter/output/frequency
bluetti/inverter/output/total_energy
bluetti/inverter/output/phase_0/status
bluetti/inverter/output/phase_0/power
bluetti/inverter/output/phase_0/voltage
bluetti/inverter/output/phase_0/current
```

---

## Verification Details

### Source Code Analysis:
- **File**: `ProtocolParserV2.smali`
- **Path**: `bluetti_smali/smali_classes5/net/poweroak/bluetticloud/ui/connectv2/tools/`
- **Methods Analyzed**:
  - Line 19578: `parseInvBaseInfo(Ljava/util/List;I)`
  - Line 23034: `parseInvGridInfo(Ljava/util/List;I)` ⭐
  - Line 23916: `parseInvLoadInfo(Ljava/util/List;I)`
  - Line 23537: `parseInvInvInfo(Ljava/util/List;)`

### Key Smali Patterns Found:

1. **Phase loop structure**:
   ```smali
   mul-int/lit8 v6, v5, 0xc    # phaseIndex * 12
   add-int/lit8 v10, v6, 0x1a  # + base_offset
   ```

2. **16-bit value parsing**:
   ```smali
   invoke-interface {v0, v5}, Ljava/util/List;->get(I)Ljava/lang/Object;
   invoke-interface {v0, v7}, Ljava/util/List;->get(I)Ljava/lang/Object;
   new-instance v9, Ljava/lang/StringBuilder;
   # Concatenate two hex bytes, parse as integer
   ```

3. **32-bit value parsing**:
   ```smali
   invoke-interface {v0, v7, v6}, Ljava/util/List;->subList(II)Ljava/util/List;
   invoke-static/range {v10 .. v15}, .../bit32RegByteToNumber$default(...)J
   ```

4. **Scale division**:
   ```smali
   const/high16 v9, 0x41200000    # 10.0f
   div-float/2addr v6, v9
   ```

---

## Multi-Phase Support

All blocks support 1-phase and 3-phase configurations:

### Single Phase (sysPhaseNumber = 1):
- Phase 0 only
- Simpler parsing
- Common in residential systems

### Three Phase (sysPhaseNumber = 3):
- Phase 0, 1, 2
- 12 bytes per phase
- Sequential layout
- Common in commercial/industrial

---

## Next Steps for Implementation

1. **Implement Block 1300 parser first** (grid voltage/frequency - highest priority)
2. **Test with real device** to verify byte order and offsets
3. **Add error handling** for partial/corrupted data
4. **Implement remaining blocks** (1100, 1400, 1500)
5. **Create MQTT publishers** for Home Assistant integration
6. **Add monitoring dashboards** with critical alerts

---

## Safety Monitoring Thresholds

### Grid Voltage (Block 1300):
- **Normal**: 210-250V (for 230V systems)
- **Warning**: 200-210V or 250-260V
- **Critical**: <200V or >260V

### Grid Frequency (Block 1300):
- **Normal**: 59.5-60.5 Hz (60Hz) or 49.5-50.5 Hz (50Hz)
- **Warning**: ±0.5 Hz from nominal
- **Critical**: ±1.0 Hz from nominal

### Temperature (Block 1100):
- **Normal**: 0-50°C
- **Warning**: 50-65°C
- **Critical**: >65°C

---

## Code Quality Notes

### Data Validation Required:

1. **Check buffer length** before parsing
2. **Validate phase number** (1 or 3 expected)
3. **Handle zero values** (may indicate sensor fault)
4. **Check for overflow** (unlikely but possible)
5. **Verify checksums** (if protocol includes them)

### Example Validation:

```python
def validate_grid_data(data: bytes) -> bool:
    """Validate grid data before parsing"""
    if len(data) < 38:  # Minimum for single phase
        return False

    phase_num = data[25]
    if phase_num not in [1, 3]:
        return False

    required_len = 26 + (phase_num * 12)
    return len(data) >= required_len
```

---

## Success Metrics

✅ **Block 1100** - Fully documented (8.6 KB)
✅ **Block 1300** - Fully documented (5.8 KB) - **PRIORITY ACHIEVED**
✅ **Block 1400** - Fully documented (8.5 KB)
✅ **Block 1500** - Fully documented (7.7 KB)
✅ **Index created** (8.4 KB)
✅ **Summary created** (this file)

**Total documentation**: 47+ KB of detailed protocol information
**Lines of smali analyzed**: ~6000+ lines
**Methods reverse-engineered**: 4 major parsing methods
**Fields documented**: 50+ unique fields across all blocks

---

## Owner's Request Status: ✅ COMPLETE

**Original request**: "Extract grid voltage and frequency from Block 1300"

**Delivered**:
- ✅ Grid voltage (offset 28-29, per phase, /10.0 scale)
- ✅ Grid frequency (offset 0-1, global, /10.0 scale)
- ✅ Bonus: Grid power, current, energy tracking
- ✅ Bonus: All three additional INV blocks (1100, 1400, 1500)
- ✅ Python parsing examples
- ✅ MQTT integration guide
- ✅ Home Assistant sensor configurations

**Grid voltage and frequency are now fully accessible!** 🎉

---

**Generated**: 2026-02-13
**Status**: Complete
**Priority**: Block 1300 (INV_GRID_INFO) - ✅ DELIVERED
