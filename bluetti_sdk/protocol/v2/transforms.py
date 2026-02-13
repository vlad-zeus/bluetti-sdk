"""V2 Protocol Transform Pipeline

Transform operations for field values after type parsing.
Transforms are applied in sequence: raw_value → transform1 → transform2 → ... → final_value

Example:
    transform=["abs", "scale:0.1"]
    -52 → abs() → 52 → scale(0.1) → 5.2
"""

from typing import Any, Callable, List, Tuple
import re


class TransformError(Exception):
    """Error during transform execution."""
    pass


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
        raise TransformError(f"Invalid scale factor: {factor}")

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
        raise TransformError(f"Invalid minus offset: {offset}")

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
        # Support both "0x3FFF" and "3FFF"
        if mask.startswith("0x") or mask.startswith("0X"):
            mask_value = int(mask, 16)
        else:
            mask_value = int(mask, 16)
    except ValueError:
        raise TransformError(f"Invalid bitmask: {mask}")

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
        raise TransformError(f"Invalid shift bits: {bits}")

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
        raise TransformError(f"Invalid clamp range: [{min_val}, {max_val}]")

    return max(min_v, min(max_v, value))


# Transform registry
# Maps transform name to function
TRANSFORMS: dict[str, Callable] = {
    "abs": _transform_abs,
    "scale": _transform_scale,
    "minus": _transform_minus,
    "bitmask": _transform_bitmask,
    "shift": _transform_shift,
    "clamp": _transform_clamp,
}


def parse_transform_spec(spec: str) -> Tuple[str, List[str]]:
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
    if ':' not in spec:
        return (spec, [])

    parts = spec.split(':', 1)
    transform_name = parts[0]
    args_str = parts[1]

    # Split args by colon
    args = args_str.split(':')

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
        raise TransformError(f"Transform {transform_name} error: {e}")


def compile_transform_pipeline(specs: List[str]) -> Callable[[Any], Any]:
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
    for spec in specs:
        transform_name, args = parse_transform_spec(spec)

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


def apply_transform_pipeline(specs: List[str], value: Any) -> Any:
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
    for spec in specs:
        result = apply_transform(spec, result)
    return result
