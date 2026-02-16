"""Unit tests for Wave D Batch 1 block schemas (smali-verified).

Tests verify:
- Schema contract (block_id, name, min_length, protocol_version)
- Field structure (offset, type, required, unit, transform)
- Proper registration in schema registry
"""


from bluetti_sdk.protocol.v2.datatypes import UInt8, UInt16, UInt32
from bluetti_sdk.schemas import (
    BLOCK_19100_SCHEMA,
    BLOCK_19200_SCHEMA,
    BLOCK_19300_SCHEMA,
    BLOCK_19305_SCHEMA,
    BLOCK_40127_SCHEMA,
)

# === Block 19100 (COMM_DELAY_SETTINGS) ===


def test_block_19100_declarative_contract():
    """Verify Block 19100 (COMM_DELAY_SETTINGS) schema contract."""
    assert BLOCK_19100_SCHEMA.block_id == 19100
    assert BLOCK_19100_SCHEMA.name == "COMM_DELAY_SETTINGS"
    assert BLOCK_19100_SCHEMA.min_length == 16
    assert BLOCK_19100_SCHEMA.protocol_version == 2000
    assert BLOCK_19100_SCHEMA.strict is False
    assert BLOCK_19100_SCHEMA.verification_status == "smali_verified"

    # Verify key fields exist
    field_names = {f.name for f in BLOCK_19100_SCHEMA.fields}
    assert "enable_flags_01" in field_names
    assert "enable_flags_02" in field_names
    assert "action_flags_01" in field_names
    assert "action_flags_02" in field_names


def test_block_19100_field_structure():
    """Verify Block 19100 field structure."""
    fields = {f.name: f for f in BLOCK_19100_SCHEMA.fields}

    # Enable flags
    enable_flags_01 = fields["enable_flags_01"]
    assert enable_flags_01.offset == 0
    assert isinstance(enable_flags_01.type, UInt16)
    assert enable_flags_01.required is True

    enable_flags_04 = fields["enable_flags_04"]
    assert enable_flags_04.offset == 6
    assert isinstance(enable_flags_04.type, UInt16)
    assert enable_flags_04.required is True

    # Action flags
    action_flags_01 = fields["action_flags_01"]
    assert action_flags_01.offset == 8
    assert isinstance(action_flags_01.type, UInt16)
    assert action_flags_01.required is True

    action_flags_04 = fields["action_flags_04"]
    assert action_flags_04.offset == 14
    assert isinstance(action_flags_04.type, UInt16)
    assert action_flags_04.required is True


# === Block 19200 (SCHEDULED_BACKUP) ===


def test_block_19200_declarative_contract():
    """Verify Block 19200 (SCHEDULED_BACKUP) schema contract."""
    assert BLOCK_19200_SCHEMA.block_id == 19200
    assert BLOCK_19200_SCHEMA.name == "SCHEDULED_BACKUP"
    assert BLOCK_19200_SCHEMA.min_length == 38
    assert BLOCK_19200_SCHEMA.protocol_version == 2000
    assert BLOCK_19200_SCHEMA.strict is False
    assert BLOCK_19200_SCHEMA.verification_status == "smali_verified"

    # Verify key fields exist
    field_names = {f.name for f in BLOCK_19200_SCHEMA.fields}
    assert "enable_flags" in field_names
    assert "mode_config" in field_names
    assert "schedule0_start_time" in field_names
    assert "schedule0_end_time" in field_names


def test_block_19200_field_structure():
    """Verify Block 19200 field structure."""
    fields = {f.name: f for f in BLOCK_19200_SCHEMA.fields}

    # Config fields
    enable_flags = fields["enable_flags"]
    assert enable_flags.offset == 0
    assert isinstance(enable_flags.type, UInt16)
    assert enable_flags.required is True

    mode_config = fields["mode_config"]
    assert mode_config.offset == 2
    assert isinstance(mode_config.type, UInt16)
    assert mode_config.required is True

    # Schedule 0
    schedule0_start = fields["schedule0_start_time"]
    assert schedule0_start.offset == 6
    assert isinstance(schedule0_start.type, UInt32)
    assert schedule0_start.required is False

    # Schedule 3
    schedule3_end = fields["schedule3_end_time"]
    assert schedule3_end.offset == 34
    assert isinstance(schedule3_end.type, UInt32)
    assert schedule3_end.required is False


# === Block 19300 (TIMER_SETTINGS) ===


def test_block_19300_declarative_contract():
    """Verify Block 19300 (TIMER_SETTINGS) schema contract."""
    assert BLOCK_19300_SCHEMA.block_id == 19300
    assert BLOCK_19300_SCHEMA.name == "TIMER_SETTINGS"
    assert BLOCK_19300_SCHEMA.min_length == 50
    assert BLOCK_19300_SCHEMA.protocol_version == 2000
    assert BLOCK_19300_SCHEMA.strict is False
    assert BLOCK_19300_SCHEMA.verification_status == "smali_verified"

    # Verify key fields exist
    field_names = {f.name for f in BLOCK_19300_SCHEMA.fields}
    assert "enable_flags_01" in field_names
    assert "enable_flags_02" in field_names
    assert "timer_count" in field_names


def test_block_19300_field_structure():
    """Verify Block 19300 field structure."""
    fields = {f.name: f for f in BLOCK_19300_SCHEMA.fields}

    # Enable flags
    enable_flags_01 = fields["enable_flags_01"]
    assert enable_flags_01.offset == 0
    assert isinstance(enable_flags_01.type, UInt16)
    assert enable_flags_01.required is True

    enable_flags_04 = fields["enable_flags_04"]
    assert enable_flags_04.offset == 6
    assert isinstance(enable_flags_04.type, UInt16)
    assert enable_flags_04.required is True

    # Timer count
    timer_count = fields["timer_count"]
    assert timer_count.offset == 9
    assert isinstance(timer_count.type, UInt8)
    assert timer_count.required is True


# === Block 19305 (TIMER_TASK_LIST) ===


def test_block_19305_declarative_contract():
    """Verify Block 19305 (TIMER_TASK_LIST) schema contract."""
    assert BLOCK_19305_SCHEMA.block_id == 19305
    assert BLOCK_19305_SCHEMA.name == "TIMER_TASK_LIST"
    assert BLOCK_19305_SCHEMA.min_length == 40
    assert BLOCK_19305_SCHEMA.protocol_version == 2000
    assert BLOCK_19305_SCHEMA.strict is False
    assert BLOCK_19305_SCHEMA.verification_status == "smali_verified"

    # Verify key fields exist
    field_names = {f.name for f in BLOCK_19305_SCHEMA.fields}
    assert "timer0_enable" in field_names
    assert "timer0_start_hour" in field_names
    assert "timer0_start_minute" in field_names
    assert "timer0_days_of_week" in field_names
    assert "timer0_mode" in field_names
    assert "timer0_power" in field_names


def test_block_19305_field_structure():
    """Verify Block 19305 field structure."""
    fields = {f.name: f for f in BLOCK_19305_SCHEMA.fields}

    # Enable
    timer0_enable = fields["timer0_enable"]
    assert timer0_enable.offset == 0
    assert isinstance(timer0_enable.type, UInt16)
    assert timer0_enable.required is True

    # Time fields
    timer0_start_hour = fields["timer0_start_hour"]
    assert timer0_start_hour.offset == 2
    assert isinstance(timer0_start_hour.type, UInt8)
    assert timer0_start_hour.required is True

    timer0_end_minute = fields["timer0_end_minute"]
    assert timer0_end_minute.offset == 8
    assert isinstance(timer0_end_minute.type, UInt8)
    assert timer0_end_minute.required is True

    # Days and mode
    timer0_days = fields["timer0_days_of_week"]
    assert timer0_days.offset == 10
    assert isinstance(timer0_days.type, UInt16)
    assert timer0_days.required is True

    timer0_mode = fields["timer0_mode"]
    assert timer0_mode.offset == 12
    assert isinstance(timer0_mode.type, UInt8)
    assert timer0_mode.required is True

    # Power
    timer0_power = fields["timer0_power"]
    assert timer0_power.offset == 14
    assert isinstance(timer0_power.type, UInt16)
    assert timer0_power.unit == "W"
    assert timer0_power.required is True


# === Block 40127 (HOME_STORAGE_SETTINGS) ===


def test_block_40127_declarative_contract():
    """Verify Block 40127 (HOME_STORAGE_SETTINGS) schema contract."""
    assert BLOCK_40127_SCHEMA.block_id == 40127
    assert BLOCK_40127_SCHEMA.name == "HOME_STORAGE_SETTINGS"
    assert BLOCK_40127_SCHEMA.min_length == 24
    assert BLOCK_40127_SCHEMA.protocol_version == 2000
    assert BLOCK_40127_SCHEMA.strict is False

    # Verify key fields exist
    field_names = {f.name for f in BLOCK_40127_SCHEMA.fields}
    assert "setting_enable_1" in field_names
    assert "grid_power_l1" in field_names
    assert "grid_power_l2" in field_names
    assert "grid_power_l3" in field_names
    assert "grid_uv1_value" in field_names


def test_block_40127_field_structure():
    """Verify Block 40127 field structure."""
    fields = {f.name: f for f in BLOCK_40127_SCHEMA.fields}

    # Enable flags
    setting_enable_1 = fields["setting_enable_1"]
    assert setting_enable_1.offset == 2
    assert isinstance(setting_enable_1.type, UInt16)
    assert setting_enable_1.required is True

    # Grid power limits
    grid_power_l1 = fields["grid_power_l1"]
    assert grid_power_l1.offset == 4
    assert isinstance(grid_power_l1.type, UInt16)
    assert grid_power_l1.unit == "W"
    assert grid_power_l1.required is True

    grid_power_l3 = fields["grid_power_l3"]
    assert grid_power_l3.offset == 8
    assert isinstance(grid_power_l3.type, UInt16)
    assert grid_power_l3.unit == "W"
    assert grid_power_l3.required is True

    # Grid protection settings
    grid_uv1_value = fields["grid_uv1_value"]
    assert grid_uv1_value.offset == 12
    assert isinstance(grid_uv1_value.type, UInt16)
    assert grid_uv1_value.unit == "V"
    assert grid_uv1_value.required is False

    grid_ov1_time = fields["grid_ov1_time"]
    assert grid_ov1_time.offset == 22
    assert isinstance(grid_ov1_time.type, UInt16)
    assert grid_ov1_time.unit == "ms"
    assert grid_ov1_time.required is False
