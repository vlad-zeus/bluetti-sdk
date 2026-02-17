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
    hex_enable_list,
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


# ---------------------------------------------------------------------------
# hex_enable_list transform (hexStrToEnableList equivalent)
# ---------------------------------------------------------------------------


def test_hex_enable_list_2bit_all_ones():
    """All-ones input: every 2-bit chunk = 3 (1*1 + 1*2)."""
    for i in range(8):
        assert apply_transform(f"hex_enable_list:0:{i}", 0xFFFF) == 3


def test_hex_enable_list_2bit_all_zeros():
    """All-zeros input: every 2-bit chunk = 0."""
    for i in range(8):
        assert apply_transform(f"hex_enable_list:0:{i}", 0x0000) == 0


def test_hex_enable_list_2bit_specific_value():
    """Verify chunk extraction for a concrete UInt16 value.

    0x1234 = 0001 0010 0011 0100 (MSB first)
    bits = [0,0,0,1, 0,0,1,0, 0,0,1,1, 0,1,0,0]
    2-bit chunks (each chunk[j] * 2**j):
      [0,0]→0, [0,1]→2, [0,0]→0, [1,0]→1, [0,0]→0, [1,1]→3, [0,1]→2, [0,0]→0
    """
    value = 0x1234
    expected = [0, 2, 0, 1, 0, 3, 2, 0]
    for i, exp in enumerate(expected):
        assert apply_transform(f"hex_enable_list:0:{i}", value) == exp, (
            f"index {i}: expected {exp}"
        )


def test_hex_enable_list_3bit_all_ones():
    """3-bit mode: all-ones gives 7 (1+2+4) per chunk; 5 full chunks from UInt16."""
    for i in range(5):
        assert apply_transform(f"hex_enable_list:3:{i}", 0xFFFF) == 7


def test_hex_enable_list_3bit_partial_chunk_dropped():
    """3-bit mode: 16/3 = 5 full chunks; index 5 is out of range."""
    with pytest.raises(TransformError, match="out of range"):
        apply_transform("hex_enable_list:3:5", 0xFFFF)


def test_hex_enable_list_index_out_of_range_2bit():
    """2-bit mode: 8 elements (0-7); index 8 raises TransformError."""
    with pytest.raises(TransformError, match="out of range"):
        apply_transform("hex_enable_list:0:8", 0x1234)


def test_hex_enable_list_negative_index():
    """Negative index raises TransformError."""
    with pytest.raises(TransformError, match="out of range"):
        apply_transform("hex_enable_list:0:-1", 0x1234)


def test_hex_enable_list_invalid_mode_string():
    """Non-integer mode string raises TransformError."""
    with pytest.raises(TransformError, match="Invalid hex_enable_list mode"):
        apply_transform("hex_enable_list:x:0", 0x1234)


def test_hex_enable_list_invalid_index_string():
    """Non-integer index string raises TransformError."""
    with pytest.raises(TransformError, match="Invalid hex_enable_list index"):
        apply_transform("hex_enable_list:0:x", 0x1234)


def test_hex_enable_list_out_of_uint16_range():
    """Values outside 0-65535 raise TransformError."""
    with pytest.raises(TransformError, match="UInt16"):
        apply_transform("hex_enable_list:0:0", 0x10000)
    with pytest.raises(TransformError, match="UInt16"):
        apply_transform("hex_enable_list:0:0", -1)


def test_hex_enable_list_typed_factory_spec():
    """Typed hex_enable_list() factory produces correct DSL spec."""
    step = hex_enable_list(mode=0, index=3)
    assert isinstance(step, TransformStep)
    assert step.to_spec() == "hex_enable_list:0:3"


def test_hex_enable_list_typed_factory_applies():
    """Typed factory result can be applied via compiled pipeline."""
    step = hex_enable_list(mode=0, index=3)
    compiled = compile_transform_pipeline([step])
    # 0xFFFF: all chunks = 3
    assert compiled(0xFFFF) == 3
    # 0x0000: all chunks = 0
    assert compiled(0x0000) == 0


def test_hex_enable_list_factory_negative_index_raises():
    """Factory raises ValueError for negative index."""
    with pytest.raises(ValueError, match="index must be >= 0"):
        hex_enable_list(mode=0, index=-1)


def test_hex_enable_list_block17400_bytes174_175():
    """Block 17400 startup flags from bytes 174-175.

    Scenario: bytes [0x12, 0x34] → UInt16 big-endian = 0x1234.
    Indices [2,3,4,5] → [0, 1, 0, 3] per the chunk computation above.
    """
    value = 0x1234
    assert apply_transform("hex_enable_list:0:2", value) == 0  # black_start_enable
    assert apply_transform("hex_enable_list:0:3", value) == 1  # black_start_mode
    assert apply_transform("hex_enable_list:0:4", value) == 0  # gen_auto_start_enable
    assert apply_transform("hex_enable_list:0:5", value) == 3  # off_grid_power_priority


def test_hex_enable_list_boundary_index_0_and_7():
    """Boundary: index 0 (first chunk) and index 7 (last chunk, 2-bit mode)."""
    # 0xA000 = 1010 0000 0000 0000
    # bits = [1,0,1,0, 0,0,0,0, 0,0,0,0, 0,0,0,0]
    # chunk[0] = [1,0] → 1*1 + 0*2 = 1
    # chunk[1] = [1,0] → 1*1 + 0*2 = 1
    # chunk[7] = [0,0] → 0
    value = 0xA000
    assert apply_transform("hex_enable_list:0:0", value) == 1
    assert apply_transform("hex_enable_list:0:7", value) == 0


def test_hex_enable_list_mode_2_is_2bit():
    """Non-3 mode values (including 2) all select 2-bit chunking."""
    # Modes 0, 1, 2, 4 should all give 8 chunks (2-bit mode)
    for mode in (0, 1, 2, 4):
        # All-ones: every chunk = 3 in 2-bit mode
        assert apply_transform(f"hex_enable_list:{mode}:7", 0xFFFF) == 3
