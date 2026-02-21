"""V2 Protocol Data Types

Base types for parsing V2 protocol blocks.
All types parse from normalized big-endian byte buffers.
"""

import struct
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping, Optional, cast


class DataType(ABC):
    """Base class for V2 protocol data types."""

    @abstractmethod
    def parse(self, data: bytes, offset: int) -> Any:
        """Parse value from normalized byte buffer.

        Args:
            data: Normalized byte buffer (big-endian, no Modbus framing)
            offset: Byte offset to start parsing

        Returns:
            Parsed value

        Raises:
            IndexError: If offset + size exceeds data length
            ValueError: If data is invalid for this type
        """

    @abstractmethod
    def size(self) -> int:
        """Size in bytes."""

    @abstractmethod
    def encode(self, value: Any) -> bytes:
        """Encode value for writing.

        Args:
            value: Value to encode

        Returns:
            Encoded bytes (big-endian)

        Raises:
            ValueError: If value is invalid for this type
        """


class UInt8(DataType):
    """8-bit unsigned integer (0-255)."""

    def parse(self, data: bytes, offset: int) -> int:
        if offset + 1 > len(data):
            raise IndexError(
                f"UInt8 at offset {offset} exceeds data length {len(data)}"
            )
        return data[offset]

    def size(self) -> int:
        return 1

    def encode(self, value: int) -> bytes:
        if not 0 <= value <= 255:
            raise ValueError(f"UInt8 value {value} out of range [0, 255]")
        return bytes([value])


class Int8(DataType):
    """8-bit signed integer (-128 to 127)."""

    def parse(self, data: bytes, offset: int) -> int:
        if offset + 1 > len(data):
            raise IndexError(f"Int8 at offset {offset} exceeds data length {len(data)}")
        return cast(int, struct.unpack_from(">b", data, offset)[0])

    def size(self) -> int:
        return 1

    def encode(self, value: int) -> bytes:
        if not -128 <= value <= 127:
            raise ValueError(f"Int8 value {value} out of range [-128, 127]")
        return struct.pack(">b", value)


class UInt16(DataType):
    """16-bit unsigned integer, big-endian (0-65535)."""

    def parse(self, data: bytes, offset: int) -> int:
        if offset + 2 > len(data):
            raise IndexError(
                f"UInt16 at offset {offset} exceeds data length {len(data)}"
            )
        return cast(int, struct.unpack_from(">H", data, offset)[0])

    def size(self) -> int:
        return 2

    def encode(self, value: int) -> bytes:
        if not 0 <= value <= 65535:
            raise ValueError(f"UInt16 value {value} out of range [0, 65535]")
        return struct.pack(">H", value)


class Int16(DataType):
    """16-bit signed integer, big-endian (-32768 to 32767)."""

    def parse(self, data: bytes, offset: int) -> int:
        if offset + 2 > len(data):
            raise IndexError(
                f"Int16 at offset {offset} exceeds data length {len(data)}"
            )
        return cast(int, struct.unpack_from(">h", data, offset)[0])

    def size(self) -> int:
        return 2

    def encode(self, value: int) -> bytes:
        if not -32768 <= value <= 32767:
            raise ValueError(f"Int16 value {value} out of range [-32768, 32767]")
        return struct.pack(">h", value)


class UInt32(DataType):
    """32-bit unsigned integer, big-endian (0-4294967295)."""

    def parse(self, data: bytes, offset: int) -> int:
        if offset + 4 > len(data):
            raise IndexError(
                f"UInt32 at offset {offset} exceeds data length {len(data)}"
            )
        return cast(int, struct.unpack_from(">I", data, offset)[0])

    def size(self) -> int:
        return 4

    def encode(self, value: int) -> bytes:
        if not 0 <= value <= 4294967295:
            raise ValueError(f"UInt32 value {value} out of range [0, 4294967295]")
        return struct.pack(">I", value)


class Int32(DataType):
    """32-bit signed integer, big-endian (-2147483648 to 2147483647)."""

    def parse(self, data: bytes, offset: int) -> int:
        if offset + 4 > len(data):
            raise IndexError(
                f"Int32 at offset {offset} exceeds data length {len(data)}"
            )
        return cast(int, struct.unpack_from(">i", data, offset)[0])

    def size(self) -> int:
        return 4

    def encode(self, value: int) -> bytes:
        if not -2147483648 <= value <= 2147483647:
            raise ValueError(
                f"Int32 value {value} out of range [-2147483648, 2147483647]"
            )
        return struct.pack(">i", value)


@dataclass(frozen=True)
class String(DataType):
    """Fixed-length ASCII string (immutable)."""

    length: int

    def parse(self, data: bytes, offset: int) -> str:
        if offset + self.length > len(data):
            raise IndexError(
                f"String({self.length}) at offset {offset} exceeds "
                f"data length {len(data)}"
            )

        raw = data[offset : offset + self.length]
        # Null-terminated string
        null_pos = raw.find(b"\x00")
        if null_pos >= 0:
            raw = raw[:null_pos]

        try:
            return raw.decode("ascii", errors="strict")
        except UnicodeDecodeError as exc:
            raise ValueError(
                f"String({self.length}) contains non-ASCII bytes at offset {offset}"
            ) from exc

    def size(self) -> int:
        return self.length

    def encode(self, value: str) -> bytes:
        try:
            encoded = value.encode("ascii", errors="strict")
        except UnicodeEncodeError as exc:
            raise ValueError("String value must be ASCII encodable") from exc
        if len(encoded) > self.length:
            raise ValueError(f"String '{value}' exceeds max length {self.length}")

        # Pad with nulls
        return encoded.ljust(self.length, b"\x00")


@dataclass(frozen=True)
class Bitmap(DataType):
    """Bit field type (immutable)."""

    bits: int
    _bytes: int = field(init=False)  # Computed in __post_init__
    _base_type: Optional[DataType] = field(init=False)  # Computed in __post_init__

    def __post_init__(self) -> None:
        """Validate and compute derived attributes."""
        if self.bits not in (8, 16, 32, 64):
            raise ValueError(f"Bitmap bits must be 8, 16, 32, or 64, got {self.bits}")

        # Compute derived attributes (frozen-safe)
        object.__setattr__(self, "_bytes", self.bits // 8)

        # Select appropriate base type
        base_type: Optional[DataType]
        if self.bits == 8:
            base_type = UInt8()
        elif self.bits == 16:
            base_type = UInt16()
        elif self.bits == 32:
            base_type = UInt32()
        else:  # 64
            base_type = None  # Manual parsing

        object.__setattr__(self, "_base_type", base_type)

    def parse(self, data: bytes, offset: int) -> int:
        if self.bits == 64:
            # 64-bit requires manual parsing
            if offset + 8 > len(data):
                raise IndexError(
                    f"Bitmap(64) at offset {offset} exceeds data length {len(data)}"
                )
            return cast(int, struct.unpack_from(">Q", data, offset)[0])
        else:
            if self._base_type is None:
                raise RuntimeError(
                    f"{type(self).__name__}._base_type is None"
                    " — __post_init__ invariant violated"
                )
            return cast(int, self._base_type.parse(data, offset))

    def size(self) -> int:
        return self._bytes

    def encode(self, value: int) -> bytes:
        max_val = (1 << self.bits) - 1
        if not 0 <= value <= max_val:
            raise ValueError(
                f"Bitmap({self.bits}) value {value} out of range [0, {max_val}]"
            )

        if self.bits == 64:
            return struct.pack(">Q", value)
        else:
            if self._base_type is None:
                raise RuntimeError(
                    f"{type(self).__name__}._base_type is None"
                    " — __post_init__ invariant violated"
                )
            return self._base_type.encode(value)


@dataclass(frozen=True)
class Enum(DataType):
    """Enum type with integer → string mapping (immutable)."""

    mapping: Mapping[int, str]
    base_type: Optional[DataType] = None
    _reverse_mapping: Mapping[str, int] = field(init=False)  # Computed in __post_init__

    def __post_init__(self) -> None:
        """Make mapping immutable and compute reverse mapping."""
        # ALWAYS make defensive copy (unconditional)
        # This prevents mutation via external references, even if input is
        # MappingProxyType wrapping a mutable dict
        object.__setattr__(self, "mapping", MappingProxyType(dict(self.mapping)))

        # Compute reverse mapping (also defensive copy)
        reverse = {v: k for k, v in self.mapping.items()}
        object.__setattr__(self, "_reverse_mapping", MappingProxyType(reverse))

        # Set default base_type if not provided
        if self.base_type is None:
            object.__setattr__(self, "base_type", UInt8())

        # Validate base_type immutability (architectural defense-in-depth)
        # Strict contract: only allow SDK built-in immutable types or frozen dataclasses
        if self.base_type is not None:
            from dataclasses import is_dataclass

            base_type_class = type(self.base_type)

            # Whitelist: SDK built-in immutable types
            _ALLOWED_BASE_TYPES = (UInt8, UInt16, UInt32, Int8, Int16, Int32)

            is_builtin_immutable = isinstance(self.base_type, _ALLOWED_BASE_TYPES)
            is_frozen_dataclass = False

            if is_dataclass(base_type_class) and hasattr(
                base_type_class, "__dataclass_params__"
            ):
                # Check if dataclass is frozen via __dataclass_params__
                is_frozen_dataclass = base_type_class.__dataclass_params__.frozen

            if not (is_builtin_immutable or is_frozen_dataclass):
                raise ValueError(
                    f"Enum.base_type must be immutable. "
                    f"Got {base_type_class.__name__}. "
                    f"Allowed: SDK built-in types (UInt8, UInt16, UInt32, "
                    f"Int8, Int16, Int32) or custom @dataclass(frozen=True) "
                    f"subclasses of DataType."
                )

    def parse(self, data: bytes, offset: int) -> str:
        if self.base_type is None:
            raise RuntimeError(
                f"{type(self).__name__}.base_type is None"
                " — __post_init__ invariant violated"
            )
        raw_value = self.base_type.parse(data, offset)

        # Return mapped string or "UNKNOWN_<value>"
        return self.mapping.get(raw_value, f"UNKNOWN_{raw_value}")

    def size(self) -> int:
        if self.base_type is None:
            raise RuntimeError(
                f"{type(self).__name__}.base_type is None"
                " — __post_init__ invariant violated"
            )
        return self.base_type.size()

    def encode(self, value: str) -> bytes:
        if value not in self._reverse_mapping:
            raise ValueError(f"Enum value '{value}' not in mapping")

        int_value = self._reverse_mapping[value]
        if self.base_type is None:
            raise RuntimeError(
                f"{type(self).__name__}.base_type is None"
                " — __post_init__ invariant violated"
            )
        return self.base_type.encode(int_value)
