"""V2 Protocol Transform Pipeline

Transform operations for field values after type parsing.
Transforms are applied in sequence:
    raw_value → transform1 → transform2 → ... → final_value

Example:
    transform=["abs", "scale:0.1"]
    -52 → abs() → 52 → scale(0.1) → 5.2
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Callable, Sequence, Union


class TransformError(Exception):
    """Error during transform execution."""


@dataclass(frozen=True)
class TransformStep:
    """Typed transform step."""

    name: str
    args: tuple[str, ...] = ()

    def to_spec(self) -> str:
        if not self.args:
            return self.name
        return f"{self.name}:{':'.join(self.args)}"

    def __or__(self, other: TransformInput) -> TransformChain:
        return TransformChain((self,)).__or__(other)


@dataclass(frozen=True)
class TransformChain:
    """Composable chain of typed transform steps."""

    steps: tuple[TransformStep, ...]

    def __or__(self, other: TransformInput) -> TransformChain:
        return TransformChain(self.steps + tuple(_normalize_transforms([other])))

    def to_specs(self) -> list[str]:
        return [step.to_spec() for step in self.steps]


TransformInput = Union[str, TransformStep, TransformChain]


def _transform_abs(value: Any) -> Any:
    """Absolute value transform."""
    return abs(value)


def _transform_scale(value: Any, factor: str) -> Any:
    """Scale (multiply) transform.

    Args:
        value: Input value
        factor: Scale factor as string (e.g., "0.1", "10", "0.001")

    Returns:
        value * factor
    """
    try:
        scale_factor = float(factor)
    except ValueError:
        raise TransformError(f"Invalid scale factor: {factor}") from None

    return value * scale_factor


def _transform_minus(value: Any, offset: str) -> Any:
    """Subtract constant transform.

    Common use: Temperature conversion (raw_byte - 40 = temp_C)

    Args:
        value: Input value
        offset: Constant to subtract (e.g., "40")

    Returns:
        value - offset
    """
    try:
        subtract_value = float(offset)
    except ValueError:
        raise TransformError(f"Invalid minus offset: {offset}") from None

    return value - subtract_value


def _transform_bitmask(value: Any, mask: str) -> Any:
    """Bitwise AND mask transform.

    Args:
        value: Input value
        mask: Hex mask (e.g., "0x3FFF", "0xC000")

    Returns:
        value & mask
    """
    try:
        # Support both "0x3FFF" and "3FFF" (int with base 16 handles both)
        mask_value = int(mask, 16)
    except ValueError:
        raise TransformError(f"Invalid bitmask: {mask}") from None

    return int(value) & mask_value


def _transform_shift(value: Any, bits: str) -> Any:
    """Right bit shift transform.

    Args:
        value: Input value
        bits: Number of bits to shift right (e.g., "14")

    Returns:
        value >> bits
    """
    try:
        shift_bits = int(bits)
    except ValueError:
        raise TransformError(f"Invalid shift bits: {bits}") from None

    return int(value) >> shift_bits


def _transform_clamp(value: Any, min_val: str, max_val: str) -> Any:
    """Clamp value to range [min, max].

    Args:
        value: Input value
        min_val: Minimum value
        max_val: Maximum value

    Returns:
        Clamped value
    """
    try:
        min_v = float(min_val)
        max_v = float(max_val)
    except ValueError:
        raise TransformError(f"Invalid clamp range: [{min_val}, {max_val}]") from None

    return max(min_v, min(max_v, value))


def _transform_hex_enable_list(value: Any, mode_str: str, index_str: str) -> int:
    """Extract one element from hexStrToEnableList result.

    Replicates Java/Kotlin hexStrToEnableList(hexStr, chunkMode)[index].

    The Java parser concatenates two byte values as hex strings (e.g.,
    data[0]+data[1] → "0A"+"F3" → "0AF3"), converts to a 16-bit binary
    list (MSB first), then chunks into groups of 2 or 3 bits.  Each chunk
    is treated as a little-endian binary number: chunk[0] is the LSB.

    Algorithm verified from ProtocolParserV2$hexStrToEnableList$2.reference
    (2-bit lambda) and ProtocolParserV2.reference lines 6818-6873 (main method).
    Block 17400 always uses chunkMode=0 (2-bit), confirmed AT1Parser.reference.

    DSL format: ``hex_enable_list:<mode>:<index>``

    Args:
        value: UInt16 integer (0-65535) parsed from 2 big-endian bytes
        mode_str: ``"3"`` for 3-bit chunks; any other value for 2-bit chunks
        index_str: Which element to extract (0-based string integer)

    Returns:
        Integer chunk value at the requested index

    Raises:
        TransformError: If mode/index are non-integer or index is out of range
    """
    try:
        mode = int(mode_str)
    except ValueError:
        raise TransformError(f"Invalid hex_enable_list mode: {mode_str!r}") from None

    try:
        index = int(index_str)
    except ValueError:
        raise TransformError(f"Invalid hex_enable_list index: {index_str!r}") from None

    raw = int(value)
    if raw < 0 or raw > 0xFFFF:
        raise TransformError(f"hex_enable_list expects UInt16 (0-65535), got {raw}")

    chunk_size = 3 if mode == 3 else 2

    # Build bit list from UInt16: bit i = (raw >> (15 - i)) & 1, MSB first.
    bits = [(raw >> (15 - i)) & 1 for i in range(16)]

    # Each full chunk value = sum(bits[start+j] * 2**j for j in range(chunk_size)).
    # This matches the reference lambda which builds the string in reverse index order
    # (high index first) and parses as binary, giving chunk[1]*2 + chunk[0] for 2-bit.
    results: list[int] = []
    for start in range(0, 16, chunk_size):
        chunk = bits[start : start + chunk_size]
        if len(chunk) == chunk_size:
            results.append(sum(chunk[j] * (1 << j) for j in range(chunk_size)))

    if index < 0 or index >= len(results):
        raise TransformError(
            f"hex_enable_list index {index} out of range "
            f"(valid: 0-{len(results) - 1} for chunk_size={chunk_size})"
        )

    return results[index]


# Transform registry
# Maps transform name to function
TRANSFORMS: dict[str, Callable[..., Any]] = {
    "abs": _transform_abs,
    "clamp": _transform_clamp,
    "bitmask": _transform_bitmask,
    "hex_enable_list": _transform_hex_enable_list,
    "minus": _transform_minus,
    "scale": _transform_scale,
    "shift": _transform_shift,
}


def parse_transform_spec(spec: str) -> tuple[str, list[str]]:
    """Parse transform specification string.

    Args:
        spec: Transform spec (e.g., "abs", "scale:0.1", "clamp:0:100")

    Returns:
        Tuple of (transform_name, [arg1, arg2, ...])

    Examples:
        "abs" → ("abs", [])
        "scale:0.1" → ("scale", ["0.1"])
        "clamp:0:100" → ("clamp", ["0", "100"])
    """
    if ":" not in spec:
        return (spec, [])

    parts = spec.split(":", 1)
    transform_name = parts[0]
    args_str = parts[1]

    # Split args by colon
    args = args_str.split(":")

    return (transform_name, args)


def apply_transform(spec: str, value: Any) -> Any:
    """Apply a single transform to a value.

    Args:
        spec: Transform specification (e.g., "abs", "scale:0.1")
        value: Input value

    Returns:
        Transformed value

    Raises:
        TransformError: If transform is unknown or execution fails
    """
    transform_name, args = parse_transform_spec(spec)

    if transform_name not in TRANSFORMS:
        raise TransformError(f"Unknown transform: {transform_name}")

    transform_func = TRANSFORMS[transform_name]

    try:
        return transform_func(value, *args)
    except TypeError as e:
        raise TransformError(f"Transform {transform_name} error: {e}") from e


def _normalize_transforms(specs: Sequence[TransformInput]) -> list[TransformStep]:
    normalized: list[TransformStep] = []
    for spec in specs:
        if isinstance(spec, TransformChain):
            normalized.extend(spec.steps)
        elif isinstance(spec, TransformStep):
            normalized.append(spec)
        else:
            transform_name, args = parse_transform_spec(spec)
            normalized.append(TransformStep(transform_name, tuple(args)))
    return normalized


def compile_transform_pipeline(
    specs: Sequence[TransformInput],
) -> Callable[[Any], Any]:
    """Compile a list of transform specs into a single function.

    This allows for performance optimization by pre-parsing transform specs.

    Args:
        specs: List of transform specifications (e.g., ["abs", "scale:0.1"])

    Returns:
        Function that applies all transforms in sequence

    Example:
        >>> pipeline = compile_transform_pipeline(["abs", "scale:0.1"])
        >>> pipeline(-52)
        5.2
    """
    # Pre-parse all transform specs
    compiled_transforms = []
    for step in _normalize_transforms(specs):
        transform_name, args = step.name, list(step.args)

        if transform_name not in TRANSFORMS:
            raise TransformError(f"Unknown transform: {transform_name}")

        transform_func = TRANSFORMS[transform_name]
        compiled_transforms.append((transform_func, args))

    # Return closure that applies all transforms
    def execute_pipeline(value: Any) -> Any:
        result = value
        for transform_func, args in compiled_transforms:
            result = transform_func(result, *args)
        return result

    return execute_pipeline


def apply_transform_pipeline(specs: Sequence[TransformInput], value: Any) -> Any:
    """Apply a sequence of transforms to a value.

    Args:
        specs: List of transform specifications (e.g., ["abs", "scale:0.1"])
        value: Input value

    Returns:
        Final transformed value

    Example:
        >>> apply_transform_pipeline(["abs", "scale:0.1"], -52)
        5.2
    """
    result = value
    for step in _normalize_transforms(specs):
        result = apply_transform(step.to_spec(), result)
    return result


def abs_() -> TransformStep:
    return TransformStep("abs")


def scale(factor: float) -> TransformStep:
    if factor == 0:
        raise ValueError("Scale factor cannot be zero")
    if not math.isfinite(factor):
        raise ValueError(f"Scale factor must be finite, got {factor}")
    return TransformStep("scale", (str(factor),))


def minus(offset: float) -> TransformStep:
    return TransformStep("minus", (str(offset),))


def bitmask(mask: int) -> TransformStep:
    return TransformStep("bitmask", (hex(mask),))


def shift(bits: int) -> TransformStep:
    return TransformStep("shift", (str(bits),))


def clamp(min_val: float, max_val: float) -> TransformStep:
    if min_val >= max_val:
        raise ValueError(f"min must be < max, got [{min_val}, {max_val}]")
    return TransformStep("clamp", (str(min_val), str(max_val)))


def hex_enable_list(mode: int, index: int) -> TransformStep:
    """Extract one element from hexStrToEnableList result.

    Replicates Java's hexStrToEnableList(hexStr, chunkMode)[index].
    Input must be a UInt16 value parsed from 2 big-endian bytes.

    Args:
        mode: Chunk mode: ``3`` = 3-bit chunks; any other value (default
              Bluetti: ``0``) = 2-bit chunks.  2-bit mode yields 8 elements
              from a UInt16; 3-bit mode yields 5 elements.
        index: Which element to extract (0-based).

    Returns:
        TransformStep for use in a Field ``transform=`` parameter.

    Example::

        # Block 17400: black_start_enable at bytes 174-175, element [2]
        hex_enable_list(mode=0, index=2)  # DSL: "hex_enable_list:0:2"
    """
    if index < 0:
        raise ValueError(f"hex_enable_list index must be >= 0, got {index}")
    return TransformStep("hex_enable_list", (str(mode), str(index)))

