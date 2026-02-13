# V2 Protocol Blocks - Documentation

This directory contains comprehensive documentation of all V2 protocol blocks reverse-engineered from the Bluetti APK.

## Files

- **README.md** (this file) - Overview and quick start
- **V2_BLOCKS_INDEX.md** - Complete index of all 78 V2 blocks
- **ADDITIONAL_BLOCKS.md** - Detailed documentation of 70 additional blocks
- **TIMER_BLOCKS.md** - In-depth analysis of timer/schedule blocks

## Quick Reference

### What are V2 Blocks?

V2 protocol blocks are Modbus register addresses used by newer Bluetti devices (2nd gen IOT modules) to read and write device data. Each block represents a specific function:

- **Info blocks**: Read-only data (battery %, power, voltages, etc.)
- **Settings blocks**: Read/write configuration (charging mode, limits, schedules, etc.)
- **Event blocks**: Specific data packets for accessories

### Block Address Format

Blocks are referenced by their **hexadecimal address**:
- `0x0064` (decimal 100) - Home data (main dashboard)
- `0x07D0` (decimal 2000) - Inverter base settings
- `0x4B64` (decimal 19300) - Timer settings

## Documentation Status

| Category | Total | Fully Documented | Partial | Unknown |
|----------|-------|------------------|---------|---------|
| **All Blocks** | 78 | 15 | 55 | 8 |
| **High Priority** | 28 | 12 | 14 | 2 |
| **Settings Blocks** | 18 | 8 | 8 | 2 |

### Fully Documented Blocks (Complete Field Mappings)

1. **0x0064 (100)** - Home data *(by other agent)*
2. **0x044C (1100)** - Inverter base info *(by other agent)*
3. **0x04B0 (1200)** - PV info *(by other agent)*
4. **0x0514 (1300)** - Grid info *(by other agent)*
5. **0x0578 (1400)** - Load info *(by other agent)*
6. **0x05DC (1500)** - Inverter info *(by other agent)*
7. **0x1770 (6000)** - Pack main info *(by other agent)*
8. **0x17D4 (6100)** - Pack item info *(by other agent)*
9. **0x07D0 (2000)** - Inverter base settings
10. **0x0898 (2200)** - Inverter advanced settings
11. **0x0960 (2400)** - Certification settings
12. **0x1B58 (7000)** - Pack settings
13. **0x2AF8 (11000)** - IOT base info
14. **0x2EE2 (12002)** - IOT WiFi settings
15. **0x4A38 (19000)** - SOC threshold settings

## Most Important Blocks

### For Home Assistant Integration

**Top 5 Read-Only (Info) Blocks:**
1. `0x0064` (100) - Home data - Battery %, power, status
2. `0x044C` (1100) - Inverter base info - Detailed power metrics
3. `0x1770` (6000) - Pack main info - Battery details
4. `0x2AF8` (11000) - IOT info - Device identification
5. `0x0DAC` (3500) - Energy statistics - Historical data

**Top 5 Settings Blocks:**
1. `0x07D0` (2000) - Inverter base settings - Charging, outputs, ECO mode
2. `0x4A38` (19000) - SOC thresholds - Battery protection limits
3. `0x4B64` (19300) - Timers - Scheduled charging/discharging
4. `0x2EE2` (12002) - IOT WiFi - Network configuration
5. `0x0960` (2400) - Certification - Grid compliance

### For Power Users

**Advanced Control:**
- `0x0898` (2200) - Advanced inverter settings (password protected)
- `0x9CBF` (40127) - Home storage mode
- `0x4A9C` (19100) - Delay settings
- `0x1B58` (7000) - Pack configuration

**Monitoring:**
- `0x06A4` (1700) - Meter info (CT clamps)
- `0x0E10` (3600) - Year energy stats
- `0x02D0` (720) - OTA/firmware status

## Block Categories

### Inverter Blocks (1100-2600)
Control and monitor AC/DC inverter operations.

**Key blocks:**
- 1100-1500: Real-time info (PV, grid, load, inverter)
- 2000: Base settings (mode, charging, outputs)
- 2200: Advanced settings (voltage, frequency, limits)
- 2400: Grid certification (compliance standards)

### Battery Pack Blocks (6000-7200)
Battery management and monitoring.

**Key blocks:**
- 6000: Pack main info (voltage, current, SOC, temps)
- 6100: Pack item info (cell voltages, detailed stats)
- 7000: Pack settings (heating, parallel config)

### IOT Module Blocks (11000-13800)
IOT module configuration and status.

**Key blocks:**
- 11000: IOT identification (model, SN, version)
- 12002: WiFi settings (SSID, password)
- 12161: IOT enable status
- 13500: WiFi mesh info
- 13088: Matter protocol info

### Timer/Schedule Blocks (19000-19500)
Time-based automation and charging schedules.

**Key blocks:**
- 19000: SOC thresholds (battery limits)
- 19100: Delay settings (grid charge delays)
- 19200: Scheduled backup
- 19300: Timer settings (complex, multi-block)

### Accessory Blocks (14000-18600)
Connected accessories and expansion devices.

**Categories:**
- 14500, 14700: Smart plugs
- 15000: EV charger
- 15500-15750: DC-DC converter & hub
- 16000-16400: Solar panels
- 17000-17400: Transfer switches (ATS/AT1)
- 18000-18300: EPAD expansion

### Special Blocks (20000+)
Certification, diagnostics, and advanced features.

**Key blocks:**
- 26001: Time-of-use tariffs
- 40127: Home storage mode
- 40044, 40187, 40181: Advanced certifications

## Using This Documentation

### Reading Data

1. Find your desired block in `V2_BLOCKS_INDEX.md`
2. Check documentation status (Full/Partial)
3. For fully documented blocks, see `ADDITIONAL_BLOCKS.md` for field mappings
4. Use the offset table to parse response bytes

**Example - Reading SOC Thresholds (0x4A38):**

```python
# Read 10 bytes from block 0x4A38
response = modbus_read(0x4A38, length=10)

# Parse register 0 (bytes 0-1)
word = (response[0] << 8) | response[1]
off_soc = word & 0x7F           # bits 0-6
off_enable = (word >> 7) & 0x01 # bit 7
on_soc = (word >> 8) & 0x7F     # bits 8-14
on_enable = (word >> 15) & 0x01 # bit 15
```

### Writing Settings

1. Verify block supports writing (Settings blocks only)
2. Review security notes in documentation
3. Build data according to field mappings
4. Write to device and verify

**Example - Writing Inverter Settings (0x07D0):**

```python
# Enable grid charging (offset 7)
data = modbus_read(0x07D0, length=50)  # Read current
data[7] = 0x01  # Set CtrlGridChg = enabled
modbus_write(0x07D0, data)  # Write back
```

### Advanced Features

**Timers** - See `TIMER_BLOCKS.md` for complete guide
- Multi-block structure
- Complex parsing logic
- Enable flags + task list

**Multi-WiFi** - Blocks 13611, 13624
- Support for multiple WiFi networks
- Automatic failover

**Certification** - Blocks 2400, 40044, 40181, 40187
- Grid compliance by region
- Anti-backflow settings
- Power factor control

## Implementation Roadmap

### Phase 1: Essential (For basic Home Assistant integration)
- [x] Home data (100) - *by other agent*
- [x] Inverter info (1100-1500) - *by other agent*
- [x] Pack info (6000-6100) - *by other agent*
- [x] IOT info (11000)
- [x] Inverter base settings (2000)
- [x] SOC thresholds (19000)

### Phase 2: Control (For power users)
- [x] Advanced settings (2200)
- [x] WiFi settings (12002)
- [ ] Timer settings (19300) - Documented, needs implementation
- [ ] Home storage mode (40127) - Needs analysis
- [ ] Pack settings (7000)

### Phase 3: Monitoring (For detailed tracking)
- [ ] Meter info/settings (1700, 1900)
- [ ] Energy statistics (3500, 3600)
- [ ] IOT status (12161)
- [ ] OTA status (720)

### Phase 4: Accessories (Device dependent)
- [ ] Smart plug blocks
- [ ] Panel blocks
- [ ] DC hub blocks
- [ ] Transfer switch blocks

## Testing Notes

### What's Been Tested
- Block address enumeration (from APK)
- Parse method identification (from APK)
- Field offset extraction (from APK code)

### What Needs Testing
- Actual device responses (register values)
- Write operations (all settings blocks)
- Timer functionality (complex structure)
- Device-specific variations (different models)

### Testing Strategy
1. **Read-only first**: Verify info blocks work correctly
2. **Safe writes**: Test non-critical settings (LED, display)
3. **Critical writes**: Test with supervision (charging, limits)
4. **Model variation**: Test on multiple device types

## Security Warnings

### High-Risk Blocks
- `0x0898` (2200) - Advanced settings, can modify voltage/frequency
- `0x4A38` (19000) - SOC limits, battery protection
- `0x2EE2` (12002) - WiFi credentials, handle securely
- `0x4B64` (19300) - Timers, could cause unexpected behavior

### Best Practices
1. Always read before writing (verify current state)
2. Validate all values before writing
3. Test on non-production systems first
4. Keep backups of working configurations
5. Never disable safety features unless you understand implications

## Contributing

To add documentation for undocumented blocks:

1. Find the parse method in `ProtocolParserV2.smali`
2. Extract field offsets using pattern:
   - `invoke-interface {v0, vX}, List;->get(I)` = offset in vX
   - `invoke-virtual {vY, vZ}, Bean;->setFieldName(X)` = field name
3. Document in `ADDITIONAL_BLOCKS.md`
4. Update `V2_BLOCKS_INDEX.md` status

## References

### Source Files
- **Block enumeration**: `ConnectManager.smali` lines 8168-8249
- **Block handlers**: `ConnectManager.smali` lines 5916-8100
- **Parse methods**: `ProtocolParserV2.smali`
- **Bean classes**: `smali_classes5/.../connectv2/bean/`

### Related Documentation
- V1 Protocol: (if exists)
- Modbus Implementation: (bluetti_mqtt core)
- Home Assistant Integration: (entity mappings)

## Version History

- **2025-02-13**: Initial comprehensive documentation
  - Mapped all 78 V2 blocks
  - Fully documented 15 high-priority blocks
  - Detailed timer block analysis
  - Created index and quick reference

## Contact

For questions or contributions, see main repository documentation.

---

**Note**: This documentation is reverse-engineered from the Bluetti Android APK and may not be 100% accurate. Always test carefully and report any discrepancies.
