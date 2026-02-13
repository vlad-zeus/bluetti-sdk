# V2 Protocol Timer Blocks - Detailed Analysis

## Overview

Timer functionality in V2 protocol uses multiple related blocks to manage scheduled charge/discharge operations. This is critical for time-of-use (TOU) optimization.

---

## Timer Block Structure

### Main Timer Block: 0x4B64 (19300)

**Method:** `commTimerSettingsParse`
**Bean:** `DeviceCommTimerSettings`

**Contains:**
1. Enable list (offsets 0-7, 8 bytes)
2. Timer count (offset 9, 1 byte)
3. Timer task list (offsets 10+, variable length)

### Related Blocks

| Block | Dec | Purpose |
|-------|-----|---------|
| 0x4B64 | 19300 | Main timer settings |
| 0x4B69 | 19305 | Timer task list (full) |
| 0x4BA5 | 19365 | AT1 timer slots 1-2 |
| 0x4BE1 | 19425 | AT1 timer slots 3-4 |
| 0x4C1D | 19485 | AT1 additional timer slots |

---

## Timer Data Format

### Enable Bits (Offsets 0-7)

**Format:** 8 bytes, each containing 4 timer enable flags (2 bits per timer)

```
Byte layout (each byte = 4 timers):
Byte 0: Timers 1-4   enable flags
Byte 1: Timers 5-8   enable flags
Byte 2: Timers 9-12  enable flags
Byte 3: Timers 13-16 enable flags
Byte 4: Timers 17-20 enable flags
Byte 5: Timers 21-24 enable flags
Byte 6: Timers 25-28 enable flags
Byte 7: Timers 29-32 enable flags
```

**Extraction:**
```python
# Parse 2-byte hex string into 4 enable flags
hex_str = "A5"  # Example: 0xA5 = 10100101
value = int(hex_str, 16)

# Extract 4 flags (2 bits each gives 0-3 value)
# Typically 0=disabled, 1=enabled
flags = []
for i in range(4):
    flag = (value >> (i * 2)) & 0x03
    flags.append(flag > 0)
```

### Timer Count (Offset 9)

**Format:** 1 byte hex string
**Value:** Number of active timers (typically 0-32)

```python
timer_count = int(data_bytes[9], 16)
```

### Timer Task List (Offsets 10+)

**Method:** `commTimerTaskListParse`
**Format:** Each timer occupies **40 bytes (20 registers)**

**Size calculation:**
```
If total_size >= 90 bytes: use offsets 10-89 (80 bytes = 2 timers)
If total_size < 90 bytes:  use offsets 10-49 (40 bytes = 1 timer)
```

**Each timer structure (40 bytes):**

| Byte Offset | Registers | Field | Format | Description |
|-------------|-----------|-------|--------|-------------|
| 0-1 | 0 | EnableFlag | uint16 | Timer enable (parsed separately) |
| 2-3 | 1 | StartHour | uint8 | Start hour (0-23) |
| 4-5 | 1 | StartMinute | uint8 | Start minute (0-59) |
| 6-7 | 2 | EndHour | uint8 | End hour (0-23) |
| 8-9 | 2 | EndMinute | uint8 | End minute (0-59) |
| 10-11 | 3 | DaysOfWeek | bits | 7 bits for days (Sun-Sat) |
| 12-13 | 4 | TimerMode | uint8 | Mode (charge/discharge/etc.) |
| 14-15 | 5 | PowerLevel | uint16 | Power setting (W) |
| 16-17 | 6 | Priority | uint8 | Priority level |
| 18-39 | 7-11 | Reserved | - | Additional settings |

**Note:** Exact field layout needs further reverse engineering from `parseTimerItem` method at line 31973 of ProtocolParserV2.smali.

---

## Timer Block Reading Strategy

### Option 1: Read Main Block Only (19300)

**Pros:**
- Single read operation
- Gets all essential data
- Sufficient for most use cases

**Cons:**
- May have size limitations
- Only gets first few timers if many are configured

**Example:**
```python
# Read block 0x4B64, length varies:
# - Minimum: 50 bytes (10 + 40 bytes for 1 timer)
# - Recommended: 90 bytes (10 + 80 bytes for 2 timers)
# - Maximum: 650+ bytes (10 + 40*16 bytes for all timers)

result = read_modbus_block(0x4B64, length=90)
```

### Option 2: Read Task List Block (19305)

**Pros:**
- Dedicated timer data block
- May support more timers

**Cons:**
- Needs separate read
- Block structure unclear without testing

### Option 3: Read AT1 Timer Blocks

**For AT1 devices only:**
- 0x4BA5: Timer slots 1-2
- 0x4BE1: Timer slots 3-4

These may be AT1-specific timer extensions.

---

## Parsing Implementation

### Step 1: Parse Enable Flags

```python
def parse_timer_enables(data_bytes: List[str]) -> List[bool]:
    """
    Parse timer enable flags from first 8 bytes
    Returns list of up to 32 boolean enable flags
    """
    enable_list = []

    # Process 8 bytes (offsets 0-7)
    for i in range(8):
        if i*2 + 1 >= len(data_bytes):
            break

        # Combine 2 hex bytes into 1 value
        hex_str = data_bytes[i*2] + data_bytes[i*2 + 1]
        value = int(hex_str, 16)

        # Extract 4 enable flags (2 bits each)
        for bit_pos in range(4):
            flag = (value >> (bit_pos * 2)) & 0x03
            enable_list.append(flag > 0)

    return enable_list
```

### Step 2: Get Timer Count

```python
def parse_timer_count(data_bytes: List[str]) -> int:
    """Get number of active timers from offset 9"""
    if len(data_bytes) < 10:
        return 0
    return int(data_bytes[9], 16)
```

### Step 3: Parse Timer Tasks

```python
def parse_timer_tasks(data_bytes: List[str], start_num: int = 1) -> List[TimerTask]:
    """
    Parse timer task list starting from offset 10
    start_num: Timer index offset (usually 1)
    """
    tasks = []

    # Determine how many bytes we have for timers
    if len(data_bytes) >= 90:
        timer_data = data_bytes[10:90]  # 80 bytes = 2 timers
    else:
        timer_data = data_bytes[10:50]  # 40 bytes = 1 timer

    # Each timer is 40 bytes
    num_timers = len(timer_data) // 40

    for i in range(num_timers):
        offset = i * 40
        timer_bytes = timer_data[offset:offset+40]

        # Parse timer structure (needs more detail)
        task = parse_single_timer(timer_bytes, start_num + i)
        tasks.append(task)

    return tasks
```

### Step 4: Parse Single Timer (Simplified)

```python
def parse_single_timer(timer_bytes: List[str], index: int) -> TimerTask:
    """
    Parse a single 40-byte timer structure
    This is a simplified version - actual format needs verification
    """
    # Start time (offsets 2-5)
    start_hour = int(timer_bytes[2], 16)
    start_minute = int(timer_bytes[4], 16)

    # End time (offsets 6-9)
    end_hour = int(timer_bytes[6], 16)
    end_minute = int(timer_bytes[8], 16)

    # Days of week (offset 10-11, bit field)
    days_word = int(timer_bytes[10] + timer_bytes[11], 16)
    days = []
    for day in range(7):
        if (days_word >> day) & 0x01:
            days.append(['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][day])

    # Mode and power (offsets 12-15)
    mode = int(timer_bytes[12], 16)
    power = int(timer_bytes[14] + timer_bytes[15], 16)

    return TimerTask(
        index=index,
        start_hour=start_hour,
        start_minute=start_minute,
        end_hour=end_hour,
        end_minute=end_minute,
        days=days,
        mode=mode,
        power=power
    )
```

---

## Timer Modes

Based on similar Bluetti devices, typical timer modes include:

| Mode Value | Description |
|------------|-------------|
| 0 | Disabled |
| 1 | Charge from grid |
| 2 | Charge from PV |
| 3 | Discharge (grid sell) |
| 4 | Load priority |
| 5 | Battery priority |
| 6 | Custom |

**Note:** Exact mode values need verification from actual devices.

---

## Writing Timer Settings

### Write Enable Flags

```python
def build_enable_bytes(enable_list: List[bool]) -> List[str]:
    """
    Build 8 bytes of enable flags from list of booleans
    Pads to 32 timers if needed
    """
    # Pad to 32 timers
    while len(enable_list) < 32:
        enable_list.append(False)

    bytes_out = []

    # Process 4 timers at a time (2 bits each = 1 byte)
    for i in range(0, 32, 4):
        value = 0
        for j in range(4):
            if enable_list[i + j]:
                value |= (0x01 << (j * 2))

        # Convert to 2 hex chars
        hex_str = f"{value:02X}"
        bytes_out.extend([hex_str[0:1], hex_str[1:2]])

    return bytes_out
```

### Write Timer Task

```python
def build_timer_bytes(timer: TimerTask) -> List[str]:
    """
    Build 40-byte timer structure
    Returns list of hex strings
    """
    timer_bytes = ['00'] * 40

    # Start time
    timer_bytes[2] = f"{timer.start_hour:02X}"
    timer_bytes[4] = f"{timer.start_minute:02X}"

    # End time
    timer_bytes[6] = f"{timer.end_hour:02X}"
    timer_bytes[8] = f"{timer.end_minute:02X}"

    # Days of week
    days_value = 0
    for day_name in timer.days:
        day_index = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].index(day_name)
        days_value |= (1 << day_index)
    timer_bytes[10:12] = [f"{days_value >> 8:02X}", f"{days_value & 0xFF:02X}"]

    # Mode
    timer_bytes[12] = f"{timer.mode:02X}"

    # Power
    timer_bytes[14:16] = [f"{timer.power >> 8:02X}", f"{timer.power & 0xFF:02X}"]

    return timer_bytes
```

### Full Timer Write

```python
def write_timer_settings(enables: List[bool], timers: List[TimerTask], timer_count: int):
    """
    Write complete timer configuration to device
    """
    # Build data packet
    data = []

    # Enable flags (8 bytes = 16 hex chars)
    data.extend(build_enable_bytes(enables))

    # Offset 8 reserved
    data.append('00')

    # Timer count (offset 9)
    data.append(f"{timer_count:02X}")

    # Timer tasks (40 bytes each)
    for timer in timers:
        data.extend(build_timer_bytes(timer))

    # Write to block 0x4B64
    write_modbus_block(0x4B64, data)
```

---

## Testing Strategy

### Phase 1: Read Only
1. Read block 0x4B64 with various lengths (50, 90, 200 bytes)
2. Parse enable flags and timer count
3. Attempt to parse timer structures
4. Verify against app display

### Phase 2: Write Enable Only
1. Toggle single timer enable
2. Verify change persists
3. Check device behavior

### Phase 3: Write Full Timer
1. Create simple timer (daily, 1-hour window)
2. Write to empty slot
3. Verify device executes timer
4. Test modification and deletion

### Phase 4: Advanced Features
1. Multiple timers
2. Different modes (charge/discharge)
3. Power levels
4. Days of week combinations

---

## Known Limitations

1. **Timer Slot Limit**: Unknown maximum (likely 16-32 timers)
2. **Exact Field Layout**: Needs verification from `parseTimerItem` decompilation
3. **Mode Values**: Need device testing to confirm
4. **Priority/Advanced Fields**: Bytes 18-39 purpose unknown
5. **Device Compatibility**: May vary by model (AC500, EP500, etc.)

---

## Related Code Locations

- **Timer Settings Parse**: ProtocolParserV2.smali line 3249
- **Timer Task Parse**: ProtocolParserV2.smali line 3397
- **Single Timer Parse**: ProtocolParserV2.smali line 31973
- **Timer Build Task**: ProtocolParserV2.smali line 1999 (`buildTimerSetTask`)

---

## Next Steps

1. Decompile `parseTimerItem` method to get exact field layout
2. Test timer reading on actual device
3. Verify field interpretations
4. Implement write functionality
5. Add Home Assistant timer entity support

---

## Security Notes

- Writing incorrect timer data could cause device malfunction
- Always validate time ranges (0-23 hours, 0-59 minutes)
- Verify power settings are within device limits
- Test on non-critical systems first
- Consider adding "dry run" mode for validation
