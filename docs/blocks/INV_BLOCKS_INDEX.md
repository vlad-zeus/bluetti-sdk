# Bluetti V2 Protocol - INV Blocks Index

This directory contains reverse-engineered documentation for Bluetti inverter-related V2 protocol blocks (1100-1500 series).

## Block Overview

| Block ID | Hex | Name | Priority | Description | File |
|----------|-----|------|----------|-------------|------|
| 1100 | 0x44C | INV_BASE_INFO | Medium | Inverter identification, software versions, temperatures | [BLOCK_1100_INV_BASE_INFO.md](BLOCK_1100_INV_BASE_INFO.md) |
| 1300 | 0x514 | INV_GRID_INFO | **HIGHEST** | **Grid voltage, frequency, power, energy** | [BLOCK_1300_INV_GRID_INFO.md](BLOCK_1300_INV_GRID_INFO.md) |
| 1400 | 0x578 | INV_LOAD_INFO | High | Load output (DC 5V/12V/24V, AC phases) | [BLOCK_1400_INV_LOAD_INFO.md](BLOCK_1400_INV_LOAD_INFO.md) |
| 1500 | 0x5DC | INV_INV_INFO | High | Inverter output voltage, current, power | [BLOCK_1500_INV_INV_INFO.md](BLOCK_1500_INV_INV_INFO.md) |

## Quick Reference

### Block 1100 - INV_BASE_INFO
**Essential device identification and status**

Key fields:
- Inverter ID, Type, Serial Number
- 6 software module versions
- Ambient, inverter, and PV DC-DC temperatures
- Fault codes

Use cases:
- Device discovery and identification
- Temperature monitoring and alerts
- Firmware version tracking

---

### Block 1300 - INV_GRID_INFO ⭐ PRIORITY
**Critical grid connection monitoring**

Key fields:
- **Grid frequency** (Hz) - Shared across phases
- **Grid voltage** per phase (V)
- **Grid current** per phase (A)
- **Grid power** per phase (W)
- Total charge power and energy
- Total feedback (export) energy

Use cases:
- Monitor grid voltage for over/under voltage conditions
- Track grid frequency for stability
- Measure grid import/export power
- Calculate energy costs

**This is the most important block for grid-tied systems!**

---

### Block 1400 - INV_LOAD_INFO
**Comprehensive load monitoring**

Key fields:
- DC outputs: 5V, 12V, 24V (power, current)
- AC outputs: Per-phase power, voltage, current
- Total DC and AC energy consumption

Use cases:
- Monitor USB port usage (5V)
- Track car port loads (12V)
- Measure household appliance consumption (AC)
- Load balancing across phases

---

### Block 1500 - INV_INV_INFO
**Inverter performance monitoring**

Key fields:
- Inverter output frequency (Hz)
- Per-phase work status
- Per-phase output: voltage, current, power
- Total energy produced

Use cases:
- Verify inverter output quality
- Detect phase-specific faults
- Track inverter efficiency
- Monitor operational status

---

## Data Flow Architecture

```
Grid Input → [1300] → System → [1500] → AC Output → [1400] → Loads
                                ↓
                        [1100] Base Info
                     (ID, temps, status)
```

### Typical Polling Strategy

1. **High frequency (1-5 seconds)**:
   - Block 1300: Grid voltage/frequency (safety critical)
   - Block 1400: Load power (real-time monitoring)
   - Block 1500: Inverter output (performance)

2. **Medium frequency (10-30 seconds)**:
   - Block 1100: Temperatures

3. **Low frequency (1-5 minutes)**:
   - Block 1100: Software versions, device info (changes rarely)

---

## Common Field Patterns

### Multi-Phase Support
All INV blocks support both single-phase and three-phase configurations:
- Field `sysPhaseNumber` indicates phase count (1 or 3)
- Phase data stored sequentially in 12-byte chunks
- Phase indexing: 0, 1, 2 (for 3-phase)

### Scaling Factors
- **Voltage**: Divide by 10.0 (e.g., 2300 → 230.0V)
- **Current**: Divide by 10.0 (e.g., 52 → 5.2A)
- **Frequency**: Divide by 10.0 (e.g., 600 → 60.0Hz)
- **Energy**: Divide by 10.0 for kWh
- **Power**: No scaling (direct W value)
- **Temperature**: Subtract 40 from raw value

### Signed vs Unsigned
- Most values are unsigned (uint8, uint16, uint32)
- Some fields use signed integers with absolute value:
  - Grid power (block 1300)
  - Grid current (block 1300)
  - Apparent power may be signed

---

## Integration Example

### Python Helper Class

```python
class BluettiInverter:
    """Helper class for parsing all INV blocks"""

    def __init__(self):
        self.base_info = None
        self.grid_info = None
        self.load_info = None
        self.inv_info = None

    def update_base_info(self, data: bytes):
        """Parse block 1100"""
        self.base_info = parse_inv_base_info(data)

    def update_grid_info(self, data: bytes):
        """Parse block 1300"""
        self.grid_info = parse_inv_grid_info(data)

    def update_load_info(self, data: bytes):
        """Parse block 1400"""
        self.load_info = parse_inv_load_info(data)

    def update_inv_info(self, data: bytes):
        """Parse block 1500"""
        self.inv_info = parse_inv_inv_info(data)

    def get_grid_status(self) -> dict:
        """Get critical grid parameters"""
        if not self.grid_info:
            return None

        phase_0 = self.grid_info['phases'][0] if self.grid_info['phases'] else {}

        return {
            'frequency': self.grid_info['frequency'],
            'voltage': phase_0.get('gridVoltage'),
            'current': phase_0.get('gridCurrent'),
            'power': phase_0.get('gridPower'),
            'is_stable': self._check_grid_stability()
        }

    def _check_grid_stability(self) -> bool:
        """Check if grid parameters are within safe limits"""
        if not self.grid_info or not self.grid_info['phases']:
            return False

        freq = self.grid_info['frequency']
        voltage = self.grid_info['phases'][0].get('gridVoltage', 0)

        # Example thresholds (adjust for your region)
        freq_ok = 59.5 <= freq <= 60.5  # 60Hz regions
        # freq_ok = 49.5 <= freq <= 50.5  # 50Hz regions
        voltage_ok = 210 <= voltage <= 250  # 230V nominal

        return freq_ok and voltage_ok
```

---

## Home Assistant Sensors

### Essential Sensors to Create

```yaml
# Block 1300 - Grid Info (Priority)
sensor:
  - platform: mqtt
    name: "Grid Frequency"
    state_topic: "bluetti/inverter/grid/frequency"
    unit_of_measurement: "Hz"
    device_class: frequency

  - platform: mqtt
    name: "Grid Voltage Phase 0"
    state_topic: "bluetti/inverter/grid/phase_0/voltage"
    unit_of_measurement: "V"
    device_class: voltage

  - platform: mqtt
    name: "Grid Power"
    state_topic: "bluetti/inverter/grid/phase_0/power"
    unit_of_measurement: "W"
    device_class: power

# Block 1100 - Base Info
  - platform: mqtt
    name: "Inverter Temperature"
    state_topic: "bluetti/inverter/base/temperature/inverter_max"
    unit_of_measurement: "°C"
    device_class: temperature

# Block 1400 - Load Info
  - platform: mqtt
    name: "AC Load Power"
    state_topic: "bluetti/inverter/load/ac/total_power"
    unit_of_measurement: "W"
    device_class: power

  - platform: mqtt
    name: "DC 12V Current"
    state_topic: "bluetti/inverter/load/dc/12v/current"
    unit_of_measurement: "A"
    device_class: current

# Block 1500 - Inverter Info
  - platform: mqtt
    name: "Inverter Output Power"
    state_topic: "bluetti/inverter/output/phase_0/power"
    unit_of_measurement: "W"
    device_class: power
```

---

## Reverse Engineering Source

All blocks were reverse-engineered from:
- **Source file**: `bluetti_smali/smali_classes5/net/poweroak/bluetticloud/ui/connectv2/tools/ProtocolParserV2.smali`
- **APK**: Bluetti Android application (decompiled)
- **Methods**: `parseInvBaseInfo()`, `parseInvGridInfo()`, `parseInvLoadInfo()`, `parseInvInvInfo()`

### Verification Status
- ✅ Block 1100: Fully documented
- ✅ Block 1300: Fully documented (PRIORITY COMPLETE)
- ✅ Block 1400: Fully documented
- ✅ Block 1500: Fully documented

---

## Next Steps

1. **Implement parsers** for each block in your application
2. **Test with real device** to verify offsets and scaling
3. **Add error handling** for incomplete/corrupted data
4. **Create Home Assistant integration** using MQTT discovery
5. **Add alerts** for critical conditions (voltage, temperature, faults)

---

## Related Documentation

- [Block 100 - Device Core Info](../BLOCK_100_CORE_INFO.md) (if available)
- [V2 Protocol Overview](../V2_PROTOCOL.md) (if available)
- [Bluetti MQTT Integration Guide](../MQTT_INTEGRATION.md) (if available)

---

## Contributing

If you find errors or have additional insights:
1. Verify against the original smali code
2. Test with physical hardware
3. Document your findings with line number references
4. Submit corrections with evidence

---

**Last Updated**: 2026-02-13
**Protocol Version**: V2 (2001-2007+)
**Status**: Complete
