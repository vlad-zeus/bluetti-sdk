"""Test declarative Block 1100 definition."""


def test_block_1100_declarative_schema_generation():
    """Test that InvBaseInfoBlock generates valid BlockSchema."""
    from power_sdk.schemas.block_1100_declarative import InvBaseInfoBlock

    schema = InvBaseInfoBlock.to_schema()

    # Check basic properties
    assert schema.block_id == 1100
    assert schema.name == "INV_BASE_INFO"
    assert schema.min_length == 62
    assert schema.protocol_version == 2000
    assert schema.strict is False

    # Check has fields
    assert len(schema.fields) > 0

    # Check specific critical fields exist
    field_names = {f.name for f in schema.fields}
    assert "inv_id" in field_names
    assert "inv_type" in field_names
    assert "inv_sn" in field_names
    assert "software_number" in field_names


def test_block_1100_declarative_contract():
    """Test canonical Block 1100 schema contract."""
    from power_sdk.schemas.block_1100_declarative import BLOCK_1100_DECLARATIVE_SCHEMA

    assert BLOCK_1100_DECLARATIVE_SCHEMA.block_id == 1100
    assert BLOCK_1100_DECLARATIVE_SCHEMA.name == "INV_BASE_INFO"
    assert BLOCK_1100_DECLARATIVE_SCHEMA.min_length == 62

    # Verify min_length is at least sufficient for basic fields + 6 software modules
    # Basic fields (1-25) + 6 software modules * 6 bytes = 62
    assert BLOCK_1100_DECLARATIVE_SCHEMA.min_length >= 62


def test_block_1100_declarative_field_structure():
    """Test specific field details in declarative Block 1100."""
    from power_sdk.protocol.v2.datatypes import String, UInt8, UInt16, UInt32
    from power_sdk.schemas.block_1100_declarative import InvBaseInfoBlock

    schema = InvBaseInfoBlock.to_schema()
    fields_by_name = {f.name: f for f in schema.fields}

    # Test basic fields
    inv_id = fields_by_name["inv_id"]
    assert inv_id.offset == 1
    assert isinstance(inv_id.type, UInt8)
    assert inv_id.required is True

    inv_type = fields_by_name["inv_type"]
    assert inv_type.offset == 2
    assert isinstance(inv_type.type, String)
    assert inv_type.type.length == 12
    assert inv_type.required is True

    inv_sn = fields_by_name["inv_sn"]
    assert inv_sn.offset == 14
    assert isinstance(inv_sn.type, String)
    assert inv_sn.type.length == 8
    assert inv_sn.required is True

    # Test software module 0 fields
    software_0_module_id = fields_by_name["software_0_module_id"]
    assert software_0_module_id.offset == 26
    assert isinstance(software_0_module_id.type, UInt16)

    software_0_version = fields_by_name["software_0_version"]
    assert software_0_version.offset == 28
    assert isinstance(software_0_version.type, UInt32)

    # Test protocol-dependent temperature fields
    ambient_temp = fields_by_name["ambient_temp"]
    assert ambient_temp.offset == 102
    assert ambient_temp.min_protocol_version == 2005
    assert len(ambient_temp.transform) == 1
    assert ambient_temp.transform[0].name == "minus"

