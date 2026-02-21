"""Unit tests for V2 datatypes."""

import pytest
from power_sdk.plugins.bluetti.v2.protocol.datatypes import (
    Bitmap,
    Enum,
    Int8,
    Int16,
    Int32,
    String,
    UInt8,
    UInt16,
    UInt32,
)


def test_uint8():
    """Test UInt8 parsing and encoding."""
    dtype = UInt8()

    # Parse
    data = bytes([0, 42, 255])
    assert dtype.parse(data, 0) == 0
    assert dtype.parse(data, 1) == 42
    assert dtype.parse(data, 2) == 255

    # Encode
    assert dtype.encode(0) == b"\x00"
    assert dtype.encode(42) == b"\x2a"
    assert dtype.encode(255) == b"\xff"

    # Out of range
    with pytest.raises(ValueError):
        dtype.encode(256)
    with pytest.raises(ValueError):
        dtype.encode(-1)


def test_int8():
    """Test Int8 parsing and encoding."""
    dtype = Int8()

    # Parse
    data = bytes([0, 127, 128, 255])
    assert dtype.parse(data, 0) == 0
    assert dtype.parse(data, 1) == 127
    assert dtype.parse(data, 2) == -128
    assert dtype.parse(data, 3) == -1

    # Encode
    assert dtype.encode(0) == b"\x00"
    assert dtype.encode(127) == b"\x7f"
    assert dtype.encode(-128) == b"\x80"
    assert dtype.encode(-1) == b"\xff"


def test_uint16():
    """Test UInt16 parsing and encoding (big-endian)."""
    dtype = UInt16()

    # Parse (big-endian)
    data = bytes([0x00, 0x00, 0x12, 0x34, 0xFF, 0xFF])
    assert dtype.parse(data, 0) == 0
    assert dtype.parse(data, 2) == 0x1234
    assert dtype.parse(data, 4) == 65535

    # Encode
    assert dtype.encode(0) == b"\x00\x00"
    assert dtype.encode(0x1234) == b"\x12\x34"
    assert dtype.encode(65535) == b"\xff\xff"


def test_int16():
    """Test Int16 parsing and encoding (big-endian)."""
    dtype = Int16()

    # Parse
    data = bytes([0x00, 0x00, 0x7F, 0xFF, 0x80, 0x00, 0xFF, 0xFF])
    assert dtype.parse(data, 0) == 0
    assert dtype.parse(data, 2) == 32767
    assert dtype.parse(data, 4) == -32768
    assert dtype.parse(data, 6) == -1

    # Encode
    assert dtype.encode(0) == b"\x00\x00"
    assert dtype.encode(32767) == b"\x7f\xff"
    assert dtype.encode(-32768) == b"\x80\x00"
    assert dtype.encode(-1) == b"\xff\xff"


def test_uint32():
    """Test UInt32 parsing and encoding (big-endian)."""
    dtype = UInt32()

    # Parse
    data = bytes([0x00, 0x00, 0x00, 0x00, 0x12, 0x34, 0x56, 0x78])
    assert dtype.parse(data, 0) == 0
    assert dtype.parse(data, 4) == 0x12345678

    # Encode
    assert dtype.encode(0) == b"\x00\x00\x00\x00"
    assert dtype.encode(0x12345678) == b"\x12\x34\x56\x78"


def test_int32():
    """Test Int32 parsing and encoding (big-endian)."""
    dtype = Int32()

    # Parse
    data = bytes([0x00, 0x00, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0xFF])
    assert dtype.parse(data, 0) == 0
    assert dtype.parse(data, 4) == -1

    # Encode
    assert dtype.encode(0) == b"\x00\x00\x00\x00"
    assert dtype.encode(-1) == b"\xff\xff\xff\xff"


def test_string():
    """Test String parsing and encoding."""
    dtype = String(10)

    # Parse (null-terminated)
    data = b"Hello\x00\x00\x00\x00\x00Test"
    assert dtype.parse(data, 0) == "Hello"

    # Parse (no null)
    data2 = b"HelloWorld"
    assert dtype.parse(data2, 0) == "HelloWorld"

    # Encode
    assert dtype.encode("Hello") == b"Hello\x00\x00\x00\x00\x00"
    assert dtype.encode("Test") == b"Test\x00\x00\x00\x00\x00\x00"

    # Too long
    with pytest.raises(ValueError):
        dtype.encode("ThisIsTooLong")

    # Non-ASCII encode should fail fast
    with pytest.raises(ValueError, match="ASCII"):
        dtype.encode("Привет")

    # Non-ASCII bytes in payload should fail fast
    with pytest.raises(ValueError, match="non-ASCII"):
        dtype.parse(b"\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00", 0)


def test_bitmap():
    """Test Bitmap parsing."""
    # 8-bit
    dtype8 = Bitmap(8)
    data = bytes([0b10101010])
    assert dtype8.parse(data, 0) == 0b10101010

    # 16-bit
    dtype16 = Bitmap(16)
    data = bytes([0x12, 0x34])
    assert dtype16.parse(data, 0) == 0x1234

    # 32-bit
    dtype32 = Bitmap(32)
    data = bytes([0x12, 0x34, 0x56, 0x78])
    assert dtype32.parse(data, 0) == 0x12345678


def test_enum():
    """Test Enum parsing."""
    mapping = {0: "IDLE", 1: "CHARGING", 2: "DISCHARGING", 3: "FAULT"}

    dtype = Enum(mapping)

    # Parse known values
    data = bytes([0, 1, 2, 3, 99])
    assert dtype.parse(data, 0) == "IDLE"
    assert dtype.parse(data, 1) == "CHARGING"
    assert dtype.parse(data, 2) == "DISCHARGING"
    assert dtype.parse(data, 3) == "FAULT"

    # Parse unknown value
    assert dtype.parse(data, 4) == "UNKNOWN_99"

    # Encode
    assert dtype.encode("IDLE") == b"\x00"
    assert dtype.encode("CHARGING") == b"\x01"

    # Unknown value
    with pytest.raises(ValueError):
        dtype.encode("INVALID")


def test_offset_bounds():
    """Test that parsing respects offset boundaries."""
    dtype = UInt16()

    # Valid
    data = bytes([0x12, 0x34, 0x56])
    assert dtype.parse(data, 0) == 0x1234

    # Out of bounds
    with pytest.raises(IndexError):
        dtype.parse(data, 2)  # Would read bytes 2-3, but only 3 bytes total


def test_enum_bitmap_base_type():
    """Bitmap is an allowed base_type for Enum (frozen dataclass whitelist)."""
    dtype = Enum(mapping={0: "OFF", 1: "ON"}, base_type=Bitmap(bits=8))
    data = bytes([0x01])
    assert dtype.parse(data, 0) == "ON"


# ---------------------------------------------------------------------------
# ArrayField validation
# ---------------------------------------------------------------------------


def test_array_field_count_zero_raises():
    """ArrayField count=0 must raise ValueError."""
    from power_sdk.plugins.bluetti.v2.protocol.schema import ArrayField

    with pytest.raises(ValueError, match="count must be >= 1"):
        ArrayField(
            name="bad_array",
            offset=0,
            count=0,
            stride=2,
            item_type=UInt16(),
        )


def test_array_field_count_negative_raises():
    """ArrayField count=-1 must raise ValueError."""
    from power_sdk.plugins.bluetti.v2.protocol.schema import ArrayField

    with pytest.raises(ValueError, match="count must be >= 1"):
        ArrayField(
            name="bad_array",
            offset=0,
            count=-1,
            stride=2,
            item_type=UInt16(),
        )


def test_array_field_stride_zero_raises():
    """ArrayField stride=0 must raise ValueError."""
    from power_sdk.plugins.bluetti.v2.protocol.schema import ArrayField

    with pytest.raises(ValueError, match="stride must be >= 1"):
        ArrayField(
            name="bad_stride",
            offset=0,
            count=4,
            stride=0,
            item_type=UInt16(),
        )


def test_array_field_valid_construction():
    """ArrayField with valid count and stride must construct without error."""
    from power_sdk.plugins.bluetti.v2.protocol.schema import ArrayField

    af = ArrayField(name="cells", offset=0, count=4, stride=2, item_type=UInt16())
    assert af.count == 4
    assert af.stride == 2
    assert af.size() == 8


# ---------------------------------------------------------------------------
# PackedField SubField bit_end validation
# ---------------------------------------------------------------------------


def test_packed_field_subfield_bit_end_exceeds_base_raises():
    """PackedField raises ValueError when SubField bit_end exceeds base_type width."""
    from power_sdk.plugins.bluetti.v2.protocol.schema import PackedField, SubField

    # base_type=UInt16 → 16 bits; SubField bit_end=17 exceeds this
    with pytest.raises(ValueError, match="bit_end=17 exceeds base_type width of 16"):
        PackedField(
            name="packed",
            offset=0,
            count=1,
            stride=2,
            base_type=UInt16(),
            fields=[
                SubField(name="overshoot", bits="0:17"),
            ],
        )


def test_packed_field_subfield_bit_end_at_boundary_ok():
    """PackedField SubField with bit_end exactly at base_type width is valid."""
    from power_sdk.plugins.bluetti.v2.protocol.schema import PackedField, SubField

    # UInt16 = 16 bits; bit_end=16 is exactly at the boundary — must not raise
    pf = PackedField(
        name="packed",
        offset=0,
        count=1,
        stride=2,
        base_type=UInt16(),
        fields=[
            SubField(name="all_bits", bits="0:16"),
        ],
    )
    assert pf.name == "packed"


# ---------------------------------------------------------------------------
# TRANSFORMS immutability
# ---------------------------------------------------------------------------


def test_transforms_is_immutable():
    """TRANSFORMS must be a MappingProxyType (immutable global registry)."""
    from types import MappingProxyType

    from power_sdk.plugins.bluetti.v2.protocol.transforms import TRANSFORMS

    assert isinstance(TRANSFORMS, MappingProxyType), (
        "TRANSFORMS must be MappingProxyType to prevent external mutation"
    )


def test_transforms_mutation_raises():
    """Attempting to mutate TRANSFORMS must raise TypeError."""
    from power_sdk.plugins.bluetti.v2.protocol.transforms import TRANSFORMS

    with pytest.raises(TypeError):
        TRANSFORMS["injected"] = lambda v: v  # type: ignore[index]
