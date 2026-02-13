# Block 1100 (0x44C) - INV_BASE_INFO

## Block Information
- **Block ID**: 1100 (0x44C)
- **Name**: INV_BASE_INFO
- **Description**: Inverter base information - ID, type, serial number, software versions, temperatures
- **Source**: `parseInvBaseInfo()` method in ProtocolParserV2.smali

## Field Mappings

### Basic Device Information

| Offset | Size | Field Name | Data Type | Scale | Unit | Description |
|--------|------|------------|-----------|-------|------|-------------|
| 1 | 1 | invId | uint8 | 1 | - | Inverter ID number |
| 2 | 12 | invType | ASCII | - | - | Inverter type string (12 bytes, parsed as ASCII) |
| 14 | 8 | invSN | bytes | - | - | Inverter serial number (parsed via getDeviceSN) |
| 23 | 1 | invPowerType | uint8 | 1 | - | Inverter power type identifier |
| 25 | 1 | softwareNumber | uint8 | 1 | - | Number of software version entries (usually 6) |

### Software Version Information

**Per software module** (6 bytes per entry, 6 entries total):

Starting offset: 26 + (moduleIndex × 6)

| Module Index | Offset Range | Description |
|--------------|--------------|-------------|
| 0 | 26-31 | Software module 1 version info |
| 1 | 32-37 | Software module 2 version info |
| 2 | 38-43 | Software module 3 version info |
| 3 | 44-49 | Software module 4 version info |
| 4 | 50-55 | Software module 5 version info |
| 5 | 56-61 | Software module 6 version info |

**Each software version entry** (6 bytes):

| Relative Offset | Size | Field Name | Data Type | Description |
|-----------------|------|------------|-----------|-------------|
| +0 | 2 | moduleId | uint16 | Software module identifier |
| +2 | 4 | version | uint32 | Software version number |

### Temperature Sensors

**Note**: Temperature offsets vary by protocol version:

#### Protocol Version >= 2005 (VER_2005):

| Offset | Size | Field Name | Data Type | Scale | Unit | Description |
|--------|------|------------|-----------|-------|------|-------------|
| 102 | 2 | ambientTemp | uint16 | -40 | °C | Ambient temperature (subtract 40 from raw value, 0 = invalid) |
| 104 | 2 | invMaxTemp | uint16 | -40 | °C | Inverter maximum temperature (subtract 40, 0 = invalid) |
| 106 | 2 | pvDcdcMaxTemp | uint16 | -40 | °C | PV DC-DC converter max temperature (subtract 40, 0 = invalid) |

#### Protocol Version >= 2001 (VER_2001) but < 2005:

| Offset | Size | Field Name | Data Type | Scale | Unit | Description |
|--------|------|------------|-----------|-------|------|-------------|
| 97 | 1 | workingTimeNumber | uint8 | 1 | - | Working time number |
| 99 | 1 | devVoltageType | uint8 | 1 | - | Device voltage type |

#### Protocol Version < 2001:

| Offset | Size | Field Name | Data Type | Scale | Unit | Description |
|--------|------|------------|-----------|-------|------|-------------|
| 85 | 1 | workingTimeNumber | uint8 | 1 | - | Working time number |
| 87 | 1 | devVoltageType | uint8 | 1 | - | Device voltage type |

### Additional Fields (Protocol >= 2005)

| Offset | Size | Field Name | Data Type | Scale | Unit | Description |
|--------|------|------------|-----------|-------|------|-------------|
| 108 | 2 | faultCode | uint16 | 1 | - | Fault/error code (if protocol ver >= 0x7D7/2007) |

## Code Analysis Notes

From line 19578-20178 of ProtocolParserV2.smali:

1. **Inverter ID** (offset 1):
   ```smali
   invoke-interface {v0, v3}, Ljava/util/List;->get(I)Ljava/lang/Object;  # v3 = 1
   invoke-static {v4, v6}, Ljava/lang/Integer;->parseInt(Ljava/lang/String;I)I
   ```

2. **Inverter Type** (offset 2-13):
   Uses `getASCIIStr()` helper to parse 12-byte ASCII string

3. **Inverter SN** (offset 14-21):
   Uses `getDeviceSN()` helper to parse 8-byte serial number

4. **Software versions** (offset 26-61):
   Loop parsing 6 software modules:
   ```smali
   :goto_0
   if-ge v6, v8, :cond_0    # v8 = 6 (number of modules)
   mul-int/lit8 v9, v6, 0x6  # moduleIndex * 6
   add-int/lit8 v10, v9, 0x1a  # + 26 = start offset
   add-int/lit8 v9, v9, 0x20   # + 32 = end offset
   ```

5. **Temperature parsing** (protocol version dependent):
   - Raw value 0 means invalid/not present
   - Subtract 40 from non-zero values to get actual temperature
   - Example: raw value 0x3C (60) = 60 - 40 = 20°C

## Python Decoding Example

```python
def parse_inv_base_info(data: bytes, protocol_ver: int = 2005) -> dict:
    """
    Parse INV_BASE_INFO block (1100 / 0x44C)

    Args:
        data: Raw byte data from device
        protocol_ver: Protocol version number

    Returns:
        Dictionary with inverter base information
    """
    result = {
        'invId': data[1],
        'invType': data[2:14].decode('ascii', errors='ignore').strip('\x00'),
        'invSN': data[14:22].hex().upper(),  # Serial number as hex string
        'invPowerType': data[23],
        'softwareNumber': data[25],
        'softwareList': []
    }

    # Parse software version info (6 modules)
    for i in range(6):
        base_offset = 26 + (i * 6)
        module_id = int.from_bytes(data[base_offset:base_offset+2], 'big')
        version = int.from_bytes(data[base_offset+2:base_offset+6], 'big')
        result['softwareList'].append({
            'moduleId': module_id,
            'version': version
        })

    # Parse temperatures based on protocol version
    if protocol_ver >= 2005 and len(data) >= 108:
        # Temperatures with -40 offset
        ambient_raw = int.from_bytes(data[102:104], 'big')
        result['ambientTemp'] = (ambient_raw - 40) if ambient_raw != 0 else 0

        inv_max_raw = int.from_bytes(data[104:106], 'big')
        result['invMaxTemp'] = (inv_max_raw - 40) if inv_max_raw != 0 else 0

        pv_dcdc_raw = int.from_bytes(data[106:108], 'big')
        result['pvDcdcMaxTemp'] = (pv_dcdc_raw - 40) if pv_dcdc_raw != 0 else 0

        # Fault code if protocol >= 2007
        if protocol_ver >= 2007 and len(data) >= 110:
            result['faultCode'] = int.from_bytes(data[108:110], 'big')

    elif protocol_ver >= 2001:
        result['workingTimeNumber'] = data[97] if len(data) > 97 else 0
        result['devVoltageType'] = data[99] if len(data) > 99 else 0
    else:
        result['workingTimeNumber'] = data[85] if len(data) > 85 else 0
        result['devVoltageType'] = data[87] if len(data) > 87 else 0

    return result
```

## Usage in Home Assistant

This block provides essential device identification and status:

- **Device identification**: Serial number, type, model
- **Software versions**: Track firmware updates
- **Temperature monitoring**: Detect overheating conditions
- **Fault codes**: Alert on device errors

### Example MQTT Topics
```
bluetti/inverter/base/id
bluetti/inverter/base/type
bluetti/inverter/base/serial_number
bluetti/inverter/base/power_type
bluetti/inverter/base/software/module_0/version
bluetti/inverter/base/temperature/ambient
bluetti/inverter/base/temperature/inverter_max
bluetti/inverter/base/temperature/pv_dcdc_max
bluetti/inverter/base/fault_code
```

## Temperature Monitoring

Temperature thresholds (typical):
- **Normal**: 0-50°C
- **Warning**: 50-65°C
- **Critical**: >65°C

The inverter monitors:
1. **Ambient temperature**: Environment around the unit
2. **Inverter max temp**: Hottest component in inverter section
3. **PV DC-DC max temp**: Hottest component in solar input converter

## Verification Notes

- Tested against: ProtocolParserV2.smali lines 19578-20178
- Method: `parseInvBaseInfo(Ljava/util/List;I)Lnet/poweroak/bluetticloud/ui/connectv2/bean/InvBaseInfo;`
- Bean class: `InvBaseInfo` with nested `DeviceSoftwareVerInfo` objects
- Protocol version checks: VER_2001 (0x7D1), VER_2005 (0x7D5), 2007 (0x7D7)
- All offsets are byte indices (each list element = 1 byte as hex string)
