# ADR-004: Typed Transform System

**Status**: Proposed
**Date**: 2026-02-14
**Author**: Zeus Fabric Team

## Context

Current transform system uses **string-based DSL**:

```python
Field(
    name="voltage",
    offset=0,
    type=UInt16(),
    transform=["scale:0.1", "minus:40"],  # String DSL - no type safety
    unit="V"
)
```

### Problems

1. **No type safety**: Typos caught at runtime, not compile time
2. **No IDE support**: No autocomplete, no validation
3. **Hard to compose**: String concatenation, no composability
4. **Runtime parsing**: Parse strings on every field
5. **Limited validation**: Can't validate transform chains at schema definition

### Examples of Issues

```python
# Typo - only caught at runtime
transform=["scael:0.1"]  # Should be "scale"

# Wrong parameter type - only caught at runtime
transform=["scale:abc"]  # Should be number

# Invalid chain - only caught at runtime
transform=["scale:0.1", "scale:2.0"]  # Redundant
```

## Decision

Implement **dual system**: Typed transforms + DSL compatibility:

### Architecture

```
Typed Transform API (new, type-safe)
  ↓ compiles to
Transform Pipeline (existing runtime)
  ↑ parses from
String DSL (existing, for backward compatibility)
```

### Design Goals

1. **Type-safe**: Transform chain validated at schema definition
2. **Composable**: Functional composition of transforms
3. **IDE-friendly**: Full autocomplete and type hints
4. **Backward compatible**: String DSL still works
5. **Zero runtime cost**: Pre-compile transforms

## Design

### Typed Transform API

```python
from power_sdk.transforms import Scale, Minus, Abs, Clamp

# NEW: Type-safe transforms
Field(
    name="voltage",
    offset=0,
    type=UInt16(),
    transform=Scale(0.1) | Minus(40),  # Composable, type-safe
    unit="V"
)

# OLD: String DSL (still works)
Field(
    name="voltage",
    offset=0,
    type=UInt16(),
    transform=["scale:0.1", "minus:40"],  # Backward compatible
    unit="V"
)
```

### Transform Classes

```python
from abc import ABC, abstractmethod
from typing import Any, Callable

class Transform(ABC):
    """Base transform class."""

    @abstractmethod
    def compile(self) -> Callable[[Any], Any]:
        """Compile to runtime function."""

    def __or__(self, other: "Transform") -> "Pipeline":
        """Compose transforms using | operator."""
        return Pipeline([self, other])


class Scale(Transform):
    """Scale by factor."""

    def __init__(self, factor: float):
        if factor == 0:
            raise ValueError("Scale factor cannot be zero")
        self.factor = factor

    def compile(self) -> Callable[[Any], Any]:
        return lambda x: x * self.factor


class Minus(Transform):
    """Subtract offset."""

    def __init__(self, offset: float):
        self.offset = offset

    def compile(self) -> Callable[[Any], Any]:
        return lambda x: x - self.offset


class Clamp(Transform):
    """Clamp value to range."""

    def __init__(self, min_val: float, max_val: float):
        if min_val >= max_val:
            raise ValueError("min must be less than max")
        self.min = min_val
        self.max = max_val

    def compile(self) -> Callable[[Any], Any]:
        return lambda x: max(self.min, min(self.max, x))


class Pipeline(Transform):
    """Compose multiple transforms."""

    def __init__(self, transforms: List[Transform]):
        self.transforms = transforms

    def compile(self) -> Callable[[Any], Any]:
        """Compile to single function (function composition)."""
        fns = [t.compile() for t in self.transforms]

        def composed(x):
            for fn in fns:
                x = fn(x)
            return x

        return composed

    def __or__(self, other: Transform) -> "Pipeline":
        """Extend pipeline."""
        return Pipeline([*self.transforms, other])
```

### Usage Examples

```python
# Simple transform
voltage = Field(
    name="voltage",
    offset=0,
    type=UInt16(),
    transform=Scale(0.1),  # Type-safe
    unit="V"
)

# Chained transforms
temperature = Field(
    name="temperature",
    offset=2,
    type=UInt16(),
    transform=Minus(40) | Clamp(-20, 60),  # Composable
    unit="°C"
)

# Complex transform
current = Field(
    name="current",
    offset=4,
    type=Int16(),
    transform=Abs() | Scale(0.1) | Clamp(0, 100),
    unit="A"
)
```

### Backward Compatibility

```python
# Field accepts both typed and string transforms
@dataclass
class Field:
    name: str
    offset: int
    type: DataType
    transform: Optional[Union[Transform, List[str]]] = None

    def __post_init__(self):
        # Normalize to compiled function
        if isinstance(self.transform, list):
            # Parse string DSL (existing code)
            self._compiled = parse_transform_pipeline(self.transform)
        elif isinstance(self.transform, Transform):
            # Compile typed transform (new)
            self._compiled = self.transform.compile()
        else:
            self._compiled = None
```

## Consequences

### Positive

✅ **Type safety**: Catch errors at schema definition time
✅ **IDE support**: Full autocomplete, validation
✅ **Composability**: Functional composition with |
✅ **Performance**: Pre-compiled, no runtime parsing
✅ **Testability**: Each transform is testable unit
✅ **Backward compatible**: String DSL still works

### Negative

⚠️ **More code**: Transform classes vs simple strings
⚠️ **Learning curve**: Users need to learn new API
⚠️ **Migration**: Existing schemas use string DSL

### Migration Strategy

**Phase 1**: Dual support (recommended)
- Both typed and string transforms work
- New schemas use typed transforms
- Old schemas keep string DSL
- Gradual migration

**Phase 2** (optional): Deprecate strings
- Emit warnings for string transforms
- Provide migration tool
- Eventually remove string DSL

## Implementation Plan

### Increment C

1. **Create transform classes**
   - `power_sdk/transforms/__init__.py`
   - Base `Transform` class
   - Concrete transforms: `Scale`, `Minus`, `Abs`, `Clamp`, etc.

2. **Update Field to accept typed transforms**
   - Support `Union[Transform, List[str]]`
   - Compile typed transforms in __post_init__
   - Keep string DSL parsing

3. **Write comprehensive tests**
   - Test each transform class
   - Test composition (|operator)
   - Test backward compatibility
   - Test error handling

4. **Migrate Block 100 declarative to typed transforms**
   - Show example of migration
   - Prove equivalence

5. **Documentation**
   - Migration guide
   - API reference
   - Examples

### Files to Create/Modify

**New**:
- `power_sdk/transforms/__init__.py` - Public API
- `power_sdk/transforms/base.py` - Transform base class
- `power_sdk/transforms/numeric.py` - Scale, Minus, Abs, Clamp
- `power_sdk/transforms/bitwise.py` - Bitmask, Shift
- `tests/unit/transforms/test_typed_transforms.py` - Tests

**Modified**:
- `power_sdk/protocol/v2/schema.py` - Field accepts typed transforms
- `power_sdk/schemas/block_100_declarative.py` - Example migration

### API Changes

```python
# New exports in power_sdk/__init__.py
from .transforms import (
    Transform,
    Scale,
    Minus,
    Abs,
    Clamp,
    Bitmask,
    Shift,
    Pipeline,
)

__all__ = [
    # ... existing
    # Typed transforms
    "Transform",
    "Scale",
    "Minus",
    "Abs",
    "Clamp",
    "Bitmask",
    "Shift",
    "Pipeline",
]
```

## References

- Functional composition in Python
- [Railway Oriented Programming](https://fsharpforfunandprofit.com/rop/)
- Type-safe builders pattern
- Scala/Haskell function composition

## Acceptance Criteria

- [ ] Transform base class with compile() method
- [ ] All numeric transforms implemented (Scale, Minus, Abs, Clamp)
- [ ] All bitwise transforms (Bitmask, Shift)
- [ ] Pipeline composition with | operator
- [ ] Field accepts Union[Transform, List[str]]
- [ ] Backward compatibility: string DSL still works
- [ ] 100% test coverage for typed transforms
- [ ] Block 100 migrated to typed transforms (example)
- [ ] Documentation with migration guide

