"""Unit tests for V2 datatypes."""

import pytest
from bluetti_sdk.protocol.v2.datatypes import (
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
