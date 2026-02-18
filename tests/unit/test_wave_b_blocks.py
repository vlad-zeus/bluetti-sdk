"""Tests for Wave B block schemas (2000, 2200, 2400, 7000, 11000, 12002, 19000).

These are control/settings blocks that configure device behavior.
"""


def test_block_2000_declarative_contract():
    """Test Block 2000 (INV_BASE_SETTINGS) canonical schema."""
    from power_sdk.schemas import BLOCK_2000_SCHEMA

    assert BLOCK_2000_SCHEMA.block_id == 2000
    assert BLOCK_2000_SCHEMA.name == "INV_BASE_SETTINGS"
    assert BLOCK_2000_SCHEMA.min_length == 35
    assert BLOCK_2000_SCHEMA.protocol_version == 2000
    assert BLOCK_2000_SCHEMA.strict is False

    # Verify key control fields exist
    field_names = {f.name for f in BLOCK_2000_SCHEMA.fields}
    assert "working_mode" in field_names
    assert "ctrl_grid_chg" in field_names
    assert "ctrl_pv" in field_names
    assert "ctrl_inverter" in field_names
    assert "dc_eco_ctrl" in field_names
    assert "ac_eco_ctrl" in field_names


def test_block_2000_field_structure():
    """Test Block 2000 specific field details."""
    from power_sdk.protocol.v2.datatypes import UInt8, UInt16
    from power_sdk.schemas import BLOCK_2000_SCHEMA

    fields = {f.name: f for f in BLOCK_2000_SCHEMA.fields}

    # Working mode at offset 1
    working_mode = fields["working_mode"]
    assert working_mode.offset == 1
    assert isinstance(working_mode.type, UInt8)
    assert working_mode.required is True

    # Control flags
    ctrl_grid_chg = fields["ctrl_grid_chg"]
    assert ctrl_grid_chg.offset == 7
    assert isinstance(ctrl_grid_chg.type, UInt8)

    # ECO mode parameters
    dc_eco_power = fields["dc_eco_power"]
    assert dc_eco_power.offset == 23
    assert isinstance(dc_eco_power.type, UInt16)
    assert dc_eco_power.unit == "W"


def test_block_2200_declarative_contract():
    """Test Block 2200 (INV_ADV_SETTINGS) canonical schema."""
    from power_sdk.schemas import BLOCK_2200_SCHEMA

    assert BLOCK_2200_SCHEMA.block_id == 2200
    assert BLOCK_2200_SCHEMA.name == "INV_ADV_SETTINGS"
    assert BLOCK_2200_SCHEMA.min_length == 27
    assert BLOCK_2200_SCHEMA.protocol_version == 2000

    # Verify key fields
    field_names = {f.name for f in BLOCK_2200_SCHEMA.fields}
    assert "adv_login_password" in field_names
    assert "inv_voltage" in field_names
    assert "inv_freq" in field_names
    assert "grid_max_power" in field_names


def test_block_2200_field_structure():
    """Test Block 2200 specific field details."""
    from power_sdk.protocol.v2.datatypes import String, UInt16
    from power_sdk.schemas import BLOCK_2200_SCHEMA

    fields = {f.name: f for f in BLOCK_2200_SCHEMA.fields}

    # Password field
    password = fields["adv_login_password"]
    assert password.offset == 0
    assert isinstance(password.type, String)
    assert password.type.length == 8

    # Voltage with scale transform
    inv_voltage = fields["inv_voltage"]
    assert inv_voltage.offset == 13
    assert isinstance(inv_voltage.type, UInt16)
    assert len(inv_voltage.transform) == 1
    assert inv_voltage.transform[0].name == "scale"
    assert inv_voltage.unit == "V"


def test_block_2400_declarative_contract():
    """Test Block 2400 (CERT_SETTINGS) canonical schema."""
    from power_sdk.schemas import BLOCK_2400_SCHEMA

    assert BLOCK_2400_SCHEMA.block_id == 2400
    assert BLOCK_2400_SCHEMA.name == "CERT_SETTINGS"
    assert BLOCK_2400_SCHEMA.min_length == 10

    field_names = {f.name for f in BLOCK_2400_SCHEMA.fields}
    assert "grid_uv2_value" in field_names
    assert "power_factor" in field_names
    assert "grid_cert_division" in field_names


def test_block_2400_field_structure():
    """Test Block 2400 specific field details."""
    from power_sdk.protocol.v2.datatypes import UInt8, UInt16
    from power_sdk.schemas import BLOCK_2400_SCHEMA

    fields = {f.name: f for f in BLOCK_2400_SCHEMA.fields}

    adv_enable = fields["adv_enable"]
    assert adv_enable.offset == 0
    assert isinstance(adv_enable.type, UInt8)

    grid_uv2_value = fields["grid_uv2_value"]
    assert grid_uv2_value.offset == 1
    assert isinstance(grid_uv2_value.type, UInt16)


def test_block_7000_declarative_contract():
    """Test Block 7000 (PACK_SETTINGS) canonical schema."""
    from power_sdk.schemas import BLOCK_7000_SCHEMA

    assert BLOCK_7000_SCHEMA.block_id == 7000
    assert BLOCK_7000_SCHEMA.name == "PACK_SETTINGS"
    assert BLOCK_7000_SCHEMA.min_length == 12

    field_names = {f.name for f in BLOCK_7000_SCHEMA.fields}
    assert "pack_id" in field_names
    assert "pack_parallel_number" in field_names
    assert "start_heating_enable" in field_names


def test_block_7000_field_structure():
    """Test Block 7000 specific field details."""
    from power_sdk.protocol.v2.datatypes import UInt8, UInt16
    from power_sdk.schemas import BLOCK_7000_SCHEMA

    fields = {f.name: f for f in BLOCK_7000_SCHEMA.fields}

    pack_id = fields["pack_id"]
    assert pack_id.offset == 0
    assert isinstance(pack_id.type, UInt8)
    assert pack_id.required is True

    pack_parallel_number = fields["pack_parallel_number"]
    assert pack_parallel_number.offset == 1
    assert isinstance(pack_parallel_number.type, UInt16)


def test_block_11000_declarative_contract():
    """Test Block 11000 (IOT_INFO) canonical schema."""
    from power_sdk.schemas import BLOCK_11000_SCHEMA

    assert BLOCK_11000_SCHEMA.block_id == 11000
    assert BLOCK_11000_SCHEMA.name == "IOT_INFO"
    assert BLOCK_11000_SCHEMA.min_length == 38

    field_names = {f.name for f in BLOCK_11000_SCHEMA.fields}
    assert "iot_model" in field_names
    assert "iot_sn" in field_names
    assert "safety_code" in field_names
    assert "iot_software_ver" in field_names


def test_block_11000_field_structure():
    """Test Block 11000 specific field details."""
    from power_sdk.protocol.v2.datatypes import String, UInt32
    from power_sdk.schemas import BLOCK_11000_SCHEMA

    fields = {f.name: f for f in BLOCK_11000_SCHEMA.fields}

    # Model string (12 bytes)
    iot_model = fields["iot_model"]
    assert iot_model.offset == 0
    assert isinstance(iot_model.type, String)
    assert iot_model.type.length == 12
    assert iot_model.required is True

    # Serial number (8 bytes)
    iot_sn = fields["iot_sn"]
    assert iot_sn.offset == 12
    assert isinstance(iot_sn.type, String)
    assert iot_sn.type.length == 8

    # Safety code (8-byte string)
    safety_code = fields["safety_code"]
    assert safety_code.offset == 20
    assert isinstance(safety_code.type, String)
    assert safety_code.type.length == 8

    # Software version (32-bit)
    iot_software_ver = fields["iot_software_ver"]
    assert iot_software_ver.offset == 28
    assert isinstance(iot_software_ver.type, UInt32)


def test_block_12002_declarative_contract():
    """Test Block 12002 (IOT_WIFI_SETTINGS) canonical schema."""
    from power_sdk.schemas import BLOCK_12002_SCHEMA

    assert BLOCK_12002_SCHEMA.block_id == 12002
    assert BLOCK_12002_SCHEMA.name == "IOT_WIFI_SETTINGS"
    assert BLOCK_12002_SCHEMA.min_length == 98

    field_names = {f.name for f in BLOCK_12002_SCHEMA.fields}
    assert "wifi_ssid" in field_names
    assert "wifi_password" in field_names
    assert "wifi_no_password_enable" in field_names


def test_block_12002_field_structure():
    """Test Block 12002 specific field details."""
    from power_sdk.protocol.v2.datatypes import String, UInt8
    from power_sdk.schemas import BLOCK_12002_SCHEMA

    fields = {f.name: f for f in BLOCK_12002_SCHEMA.fields}

    # SSID (variable length)
    wifi_ssid = fields["wifi_ssid"]
    assert wifi_ssid.offset == 0
    assert isinstance(wifi_ssid.type, String)
    assert wifi_ssid.type.length == 64  # Conservative allocation

    # Flags at fixed offsets
    wifi_no_password_enable = fields["wifi_no_password_enable"]
    assert wifi_no_password_enable.offset == 96
    assert isinstance(wifi_no_password_enable.type, UInt8)


def test_block_19000_declarative_contract():
    """Test Block 19000 (SOC_SETTINGS) canonical schema."""
    from power_sdk.schemas import BLOCK_19000_SCHEMA

    assert BLOCK_19000_SCHEMA.block_id == 19000
    assert BLOCK_19000_SCHEMA.name == "SOC_SETTINGS"
    assert BLOCK_19000_SCHEMA.min_length == 6
    assert BLOCK_19000_SCHEMA.verification_status == "smali_verified"

    field_names = {f.name for f in BLOCK_19000_SCHEMA.fields}
    assert "grid_charge_threshold" in field_names
    assert "ups_mode_threshold" in field_names
    assert "battery_protect_threshold" in field_names


def test_block_19000_field_structure():
    """Test Block 19000 specific field details (bit-packed)."""
    from power_sdk.protocol.v2.datatypes import UInt16
    from power_sdk.schemas import BLOCK_19000_SCHEMA

    fields = {f.name: f for f in BLOCK_19000_SCHEMA.fields}

    # Threshold pairs are UInt16 bit-packed
    grid_charge = fields["grid_charge_threshold"]
    assert grid_charge.offset == 0
    assert isinstance(grid_charge.type, UInt16)
    assert grid_charge.required is True

    ups_mode = fields["ups_mode_threshold"]
    assert ups_mode.offset == 2
    assert isinstance(ups_mode.type, UInt16)

