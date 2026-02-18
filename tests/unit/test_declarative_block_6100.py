"""Test declarative Block 6100 definition."""


def test_block_6100_declarative_schema_generation():
    """Test that PackItemInfoBlock generates valid BlockSchema."""
    from power_sdk.schemas.block_6100_declarative import PackItemInfoBlock

    schema = PackItemInfoBlock.to_schema()

    # Check basic properties
    assert schema.block_id == 6100
    assert schema.name == "PACK_ITEM_INFO"
    assert schema.min_length == 160
    assert schema.protocol_version == 2000
    assert schema.strict is False

    # Check has fields
    assert len(schema.fields) > 0

    # Check specific critical fields exist
    field_names = {f.name for f in schema.fields}
    assert "pack_id" in field_names
    assert "pack_type" in field_names
    assert "voltage" in field_names
    assert "pack_soc" in field_names
    assert "total_cell_cnt" in field_names


def test_block_6100_declarative_contract():
    """Test canonical Block 6100 schema contract."""
    from power_sdk.schemas.block_6100_declarative import BLOCK_6100_DECLARATIVE_SCHEMA

    assert BLOCK_6100_DECLARATIVE_SCHEMA.block_id == 6100
    assert BLOCK_6100_DECLARATIVE_SCHEMA.name == "PACK_ITEM_INFO"
    assert BLOCK_6100_DECLARATIVE_SCHEMA.min_length == 160

    # Verify min_length includes fixed fields up to software_number
    assert BLOCK_6100_DECLARATIVE_SCHEMA.min_length >= 160


def test_block_6100_declarative_field_structure():
    """Test specific field details in declarative Block 6100."""
    from power_sdk.protocol.v2.datatypes import String, UInt8, UInt16
    from power_sdk.schemas.block_6100_declarative import PackItemInfoBlock

    schema = PackItemInfoBlock.to_schema()
    fields_by_name = {f.name: f for f in schema.fields}

    # Test pack identification fields
    pack_id = fields_by_name["pack_id"]
    assert pack_id.offset == 1
    assert isinstance(pack_id.type, UInt8)
    assert pack_id.required is True

    pack_type = fields_by_name["pack_type"]
    assert pack_type.offset == 2
    assert isinstance(pack_type.type, String)
    assert pack_type.type.length == 12
    assert pack_type.required is True

    pack_sn = fields_by_name["pack_sn"]
    assert pack_sn.offset == 14
    assert isinstance(pack_sn.type, String)
    assert pack_sn.type.length == 8
    assert pack_sn.required is True

    # Test electrical parameters
    voltage = fields_by_name["voltage"]
    assert voltage.offset == 22
    assert isinstance(voltage.type, UInt16)
    assert len(voltage.transform) == 1
    assert voltage.transform[0].name == "scale"
    assert voltage.unit == "V"
    assert voltage.required is True

    current = fields_by_name["current"]
    assert current.offset == 24
    assert isinstance(current.type, UInt16)
    assert len(current.transform) == 1
    assert current.transform[0].name == "scale"
    assert current.unit == "A"

    # Test state fields
    pack_soc = fields_by_name["pack_soc"]
    assert pack_soc.offset == 27
    assert isinstance(pack_soc.type, UInt8)
    assert pack_soc.unit == "%"
    assert pack_soc.required is True

    pack_soh = fields_by_name["pack_soh"]
    assert pack_soh.offset == 29
    assert isinstance(pack_soh.type, UInt8)
    assert pack_soh.unit == "%"

    average_temp = fields_by_name["average_temp"]
    assert average_temp.offset == 30
    assert isinstance(average_temp.type, UInt16)
    assert len(average_temp.transform) == 1
    assert average_temp.transform[0].name == "minus"
    assert average_temp.unit == "°C"

    # Test count fields
    total_cell_cnt = fields_by_name["total_cell_cnt"]
    assert total_cell_cnt.offset == 105
    assert isinstance(total_cell_cnt.type, UInt8)
    assert total_cell_cnt.required is True

    ntc_cell_cnt = fields_by_name["ntc_cell_cnt"]
    assert ntc_cell_cnt.offset == 107
    assert isinstance(ntc_cell_cnt.type, UInt8)

    bmu_cnt = fields_by_name["bmu_cnt"]
    assert bmu_cnt.offset == 109
    assert isinstance(bmu_cnt.type, UInt8)

