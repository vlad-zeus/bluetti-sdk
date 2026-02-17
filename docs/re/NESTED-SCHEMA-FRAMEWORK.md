# Nested Declarative Schema Framework

**Added**: Sprint 2026-02-17
**Status**: Implemented, backward compatible
**Files**: `bluetti_sdk/protocol/v2/schema.py`, `bluetti_sdk/schemas/declarative.py`, `bluetti_sdk/protocol/v2/parser.py`

---

## Problem

Some Bluetti protocol blocks (e.g., 17400 ATS_EVENT_EXT) use deeply nested Java bean
structures with sub-objects that cannot be accurately modeled by a flat list of `Field`
entries. Modeling them as flat fields either:

1. Requires fabricating offsets with no evidence (dangerous for write-capable blocks)
2. Forces an empty schema that produces no parsed values

The nested framework solves this without changing the public client API or breaking any
existing flat schemas.

---

## New Types

### `FieldGroup` (`bluetti_sdk/protocol/v2/schema.py`)

A named namespace container for a set of `Field` objects that share a logical group.

```python
@dataclass(frozen=True)
class FieldGroup:
    name: str                          # key in parsed values dict
    fields: Sequence[Field]            # sub-fields with absolute byte offsets
    required: bool = False
    description: Optional[str] = None
    evidence_status: Optional[str] = None

    @property
    def offset(self) -> int: ...       # min offset of sub-fields (0 if empty)
    def size(self) -> int: ...         # max_end - min_offset (0 if empty)
    def parse(self, data: bytes) -> Dict[str, Any]: ...  # returns sub-dict
```

Key behavior:

- Each sub-field uses its **absolute** byte offset within the full block data.
- Out-of-bounds sub-fields return `None` (not an error).
- An empty `fields=()` group parses to `{}`.
- The group itself has no `min_protocol_version` (unlike `Field`).

### `NestedGroupSpec` (`bluetti_sdk/schemas/declarative.py`)

An intermediate spec produced by `nested_group()`. Collected by `_generate_schema()` via
`vars(cls)` scan. Converted to a `FieldGroup` in the resulting `BlockSchema`.

---

## Declarative API

Use `nested_group()` as a **plain class attribute** (not a dataclass field - no type
annotation, no `block_field()` wrapper):

```python
@block_schema(block_id=17400, name="ATS_EVENT_EXT", ...)
@dataclass
class ATSEventExtBlock:
    # Regular flat field (dataclass field with type annotation)
    some_flat: int = block_field(offset=0, type=UInt8())

    # Nested group (plain class attribute, no type annotation)
    config_grid = nested_group(
        "config_grid",
        sub_fields=[
            Field(
                name="max_current",
                offset=84,
                type=UInt16(),
                required=False,
                description="Grid max current (smali: line 2578, data[84-85])",
            ),
        ],
        required=False,
        evidence_status="partial",
    )
```

`nested_group()` parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | required | Group name (key in parsed values) |
| `sub_fields` | `Sequence[Field]` | required | Fields with absolute byte offsets |
| `required` | `bool` | `False` | Whether group is required |
| `description` | `str \| None` | `None` | Evidence notes |
| `evidence_status` | `str \| None` | `None` | e.g. `"partial"`, `"smali_verified"` |

---

## Parser Output

The `V2Parser` produces a nested dict for each `FieldGroup`:

```python
parsed.values["config_grid"]      # -> {"max_current": 100}
parsed.values["simple_end_fields"] # -> {"volt_level_set": 3, "ac_supply_phase_num": 1, ...}
parsed.values["config_sl2"]       # -> {} (empty group)
```

Out-of-bounds sub-fields:

```python
# With 91-byte data and fields at offsets 176+:
parsed.values["simple_end_fields"]["volt_level_set"]  # -> None
```

---

## Backward Compatibility

- All existing flat schemas (only `block_field()` entries) are **completely unaffected**.
- `_generate_schema()` only collects `NestedGroupSpec` instances from `vars(cls)`.
  Dataclass `fields()` are processed identically to before.
- The parser handles `FieldGroup` before the protocol-version/bounds checks that only
  apply to `Field`-like objects. Existing `Field` / `ArrayField` / `PackedField` paths
  are unchanged.
- No changes to `V2Client`, `AsyncV2Client`, or any public API.

---

## Byte Offset Convention

Sub-fields in a `FieldGroup` use **absolute byte offsets** within the block data, not
offsets relative to any group base. This matches the evidence format where offsets come
directly from smali `data[N]` indices.

For Block 17400 specifically: `data_index = byte_offset` (1:1 mapping; each
`List<String>` element in the Java parser = 1 hex-string byte value).

---

## Empty Groups (Deferred Fields)

When a group's sub-fields cannot be proven from smali analysis, model it as an empty
group rather than guessing:

```python
config_sl2 = nested_group(
    "config_sl2",
    sub_fields=[],          # no proven absolute offsets yet
    required=False,
    evidence_status="partial",
)
```

Empty groups parse to `{}`. This is preferable to fabricated offsets, especially for
write-capable blocks.

---

## Testing

- `tests/unit/test_nested_schema_framework.py` - Framework unit + integration tests
  - `TestFieldGroup`: offset/size/parse behavior, transforms, OOB handling
  - `TestNestedGroupFunction`: `nested_group()` factory API
  - `TestGenerateSchemaWithNestedGroups`: `_generate_schema()` collection
  - `TestParserWithFieldGroup`: V2Parser integration
  - `TestBackwardCompatibility`: flat schemas unaffected

- `tests/unit/test_block_17400_nested.py` - Block 17400 contract + structure tests

---

## Upgrade Path for Deferred Fields

When device testing reveals absolute byte offsets for deferred sub-fields (e.g.,
`config_sl2.max_current`):

1. Add proven `Field` entries to the group's `sub_fields`.
2. Update `evidence_status` appropriately.
3. The parser output automatically includes the new field.

**hexStrToEnableList transform — DONE (2026-02-17)**:
The `hex_enable_list` transform was added to `bluetti_sdk/protocol/v2/transforms.py`.
Scalar fields (single index extraction) in Block 17400 have been unlocked:
- `top_level_enables`: `chg_from_grid_enable` (bytes 0-1, index [3]),
  `feed_to_grid_enable` (bytes 2-3, index [4])
- `startup_flags`: 4 fields at bytes 174-175 (indices [2-5])
- `config_grid`: `type` (index [0]), `linkage_enable` (index [0]) added
- `config_sl1`: `type` (index [1]), `linkage_enable` (index [1]) added

Still deferred: `delay_enable_1-3` (bytes 6-11) are `List<Integer>` full-list
outputs — not a single scalar index — so they cannot use `hex_enable_list`.

Full upgrade to `smali_verified` for Block 17400 requires:
1. ~~`hexStrToEnableList` transform implementation~~ ✅ DONE (2026-02-17)
2. Device validation confirming all field semantics
