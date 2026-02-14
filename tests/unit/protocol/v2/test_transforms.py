"""Unit tests for V2 transform pipeline."""

import pytest
from bluetti_sdk.protocol.v2.transforms import (
    TransformChain,
    TransformError,
    TransformStep,
    abs_,
    apply_transform,
    apply_transform_pipeline,
    bitmask,
    clamp,
    compile_transform_pipeline,
    minus,
    parse_transform_spec,
    scale,
    shift,
)


def test_transform_abs():
    """Test abs transform."""
    assert apply_transform("abs", -52) == 52
    assert apply_transform("abs", 42) == 42
    assert apply_transform("abs", 0) == 0


def test_transform_scale():
    """Test scale transform."""
    assert apply_transform("scale:0.1", 520) == 52.0
    assert apply_transform("scale:10", 5) == 50
    assert apply_transform("scale:0.001", 3245) == 3.245


def test_transform_minus():
    """Test minus transform."""
    assert apply_transform("minus:40", 80) == 40
    assert apply_transform("minus:40", 0) == -40
    assert apply_transform("minus:273.15", 300) == pytest.approx(26.85)


def test_transform_bitmask():
    """Test bitmask transform."""
    # Extract lower 14 bits
    assert apply_transform("bitmask:0x3FFF", 0xFFFF) == 0x3FFF
    assert apply_transform("bitmask:0x3FFF", 0xC000) == 0x0000

    # Extract upper 2 bits (need shift after)
    assert apply_transform("bitmask:0xC000", 0xFFFF) == 0xC000


def test_transform_shift():
    """Test shift transform."""
    assert apply_transform("shift:14", 0xC000) == 3
    assert apply_transform("shift:8", 0x1234) == 0x12
    assert apply_transform("shift:1", 8) == 4


def test_transform_clamp():
    """Test clamp transform."""
    assert apply_transform("clamp:0:100", 150) == 100
    assert apply_transform("clamp:0:100", -50) == 0
    assert apply_transform("clamp:0:100", 50) == 50


def test_pipeline_abs_scale():
    """Test pipeline: abs then scale."""
    pipeline = ["abs", "scale:0.1"]
    assert apply_transform_pipeline(pipeline, -52) == 5.2
    assert apply_transform_pipeline(pipeline, 520) == 52.0


def test_pipeline_bitmask_shift_scale():
    """Test complex pipeline: extract bits, shift, scale."""
    # Cell voltage encoding: 14-bit voltage + 2-bit status
    raw_value = 0xC000 | 3245  # status=3, voltage=3245mV

    # Extract voltage (lower 14 bits)
    voltage_pipeline = ["bitmask:0x3FFF", "scale:0.001"]
    voltage = apply_transform_pipeline(voltage_pipeline, raw_value)
    assert voltage == pytest.approx(3.245)

    # Extract status (upper 2 bits)
    status_pipeline = ["shift:14"]
    status = apply_transform_pipeline(status_pipeline, raw_value)
    assert status == 3


def test_pipeline_temperature():
    """Test temperature conversion pipeline."""
    # Temperature: raw_byte - 40 = temp_C
    pipeline = ["minus:40"]
    assert apply_transform_pipeline(pipeline, 80) == 40
    assert apply_transform_pipeline(pipeline, 20) == -20


def test_compile_pipeline():
    """Test compiled pipeline for performance."""
    specs = ["abs", "scale:0.1"]
    compiled = compile_transform_pipeline(specs)

    assert compiled(-52) == 5.2
    assert compiled(520) == 52.0


def test_parse_transform_spec():
    """Test transform spec parsing."""
    # No args
    name, args = parse_transform_spec("abs")
    assert name == "abs"
    assert args == []

    # Single arg
    name, args = parse_transform_spec("scale:0.1")
    assert name == "scale"
    assert args == ["0.1"]

    # Multiple args
    name, args = parse_transform_spec("clamp:0:100")
    assert name == "clamp"
    assert args == ["0", "100"]


def test_unknown_transform():
    """Test error on unknown transform."""
    with pytest.raises(TransformError, match="Unknown transform"):
        apply_transform("invalid_transform", 42)


def test_invalid_scale_factor():
    """Test error on invalid scale factor."""
    with pytest.raises(TransformError, match="Invalid scale factor"):
        apply_transform("scale:not_a_number", 42)


def test_invalid_bitmask():
    """Test error on invalid bitmask."""
    with pytest.raises(TransformError, match="Invalid bitmask"):
        apply_transform("bitmask:not_hex", 42)


def test_grid_current_example():
    """Test real-world example: grid current with abs and scale."""
    # Grid current: INT16, abs(), /10.0 → A
    # Raw value: -52 (negative indicates direction)
    raw_value = -52

    pipeline = ["abs", "scale:0.1"]
    current_a = apply_transform_pipeline(pipeline, raw_value)

    assert current_a == pytest.approx(5.2)


def test_cell_voltage_example():
    """Test real-world example: cell voltage extraction."""
    # Cell voltage: 16-bit packed value
    # Bits 0-13: voltage in mV
    # Bits 14-15: status
    raw_value = 0x8000 | 3245  # status=2, voltage=3245mV

    # Extract voltage
    voltage_pipeline = ["bitmask:0x3FFF", "scale:0.001"]
    voltage_v = apply_transform_pipeline(voltage_pipeline, raw_value)

    assert voltage_v == pytest.approx(3.245)

    # Extract status
    status_pipeline = ["bitmask:0xC000", "shift:14"]
    status = apply_transform_pipeline(status_pipeline, raw_value)

    assert status == 2


def test_typed_transform_step_to_spec():
    step = scale(0.1)
    assert isinstance(step, TransformStep)
    assert step.to_spec() == "scale:0.1"


def test_typed_transform_chain_pipe_operator():
    chain = abs_() | scale(0.1) | minus(2)
    assert isinstance(chain, TransformChain)
    assert chain.to_specs() == ["abs", "scale:0.1", "minus:2"]


def test_compile_pipeline_accepts_typed_chain():
    chain = bitmask(0x3FFF) | scale(0.001)
    compiled = compile_transform_pipeline([chain])
    assert compiled(3245) == pytest.approx(3.245)


def test_apply_pipeline_mixed_dsl_and_typed():
    result = apply_transform_pipeline(["abs", scale(0.1), clamp(0, 10)], -520)
    assert result == 10


def test_shift_typed_factory():
    assert shift(14).to_spec() == "shift:14"


def test_scale_factory_validation():
    with pytest.raises(ValueError, match="cannot be zero"):
        scale(0)
    with pytest.raises(ValueError, match="must be finite"):
        scale(float("inf"))


def test_clamp_factory_validation():
    with pytest.raises(ValueError, match="min must be < max"):
        clamp(10, 10)
    with pytest.raises(ValueError, match="min must be < max"):
        clamp(11, 10)


def test_typed_minus_transform():
    """Test typed minus() transform factory."""
    step = minus(40)
    assert isinstance(step, TransformStep)
    assert step.name == "minus"
    assert "40" in step.to_spec()  # Can be "40" or "40.0"

    # Apply via pipeline
    compiled = compile_transform_pipeline([step])
    assert compiled(80) == 40
    assert compiled(0) == -40


def test_typed_and_legacy_equivalent_output():
    """Test that typed and legacy DSL produce equivalent results."""
    test_value = -52

    # Legacy string DSL
    legacy_pipeline = ["abs", "scale:0.1"]
    legacy_result = apply_transform_pipeline(legacy_pipeline, test_value)

    # Typed transforms
    typed_pipeline = [abs_(), scale(0.1)]
    typed_result = apply_transform_pipeline(typed_pipeline, test_value)

    assert legacy_result == typed_result == 5.2


def test_typed_bitmask_factory():
    """Test typed bitmask() factory."""
    step = bitmask(0x3FFF)
    assert step.to_spec() == "bitmask:0x3fff"

    # Apply
    compiled = compile_transform_pipeline([step])
    assert compiled(0xFFFF) == 0x3FFF


def test_typed_abs_factory():
    """Test typed abs_() factory."""
    step = abs_()
    assert step.to_spec() == "abs"

    # Apply
    compiled = compile_transform_pipeline([step])
    assert compiled(-42) == 42
    assert compiled(42) == 42
