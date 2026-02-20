# Go-Live Checklist — power_sdk v2.1.0

Run this checklist before every production release. All items must be checked.

---

## 1. Code Quality

- [ ] `python -m ruff check power_sdk/ tests/` — zero warnings
- [ ] `python -m ruff format --check power_sdk/ tests/` — no formatting diffs
- [ ] `python -m mypy power_sdk/ --ignore-missing-imports` — zero errors

## 2. Test Suite

- [ ] `python -m pytest tests/ --no-cov -q` — all tests green, zero failures
- [ ] No tests skipped unexpectedly (`-rs` to review skip reasons)
- [ ] Conformance suite: `pytest tests/conformance/ -v` — all manifests pass

## 3. Legacy API Guard

```bash
# Nothing legacy in public-facing artifacts
! grep -rn --include="*.md" --exclude="GO-LIVE-CHECKLIST.md" "build_all_clients\|build_client_from_entry\|V2Device\|--sn\|--cert" \
  README.md docs/ examples/

# Nothing legacy in source
! grep -rn --include="*.py" "build_all_clients\|V2Device" power_sdk/
```

Both commands must exit 0 (no matches).

## 4. Runtime Smoke Test

```bash
python -m power_sdk runtime --config examples/runtime.yaml --dry-run
```

Expected: table printed, exit 0.

## 5. Public API Guard

```bash
python -c "from power_sdk import build_all_clients"    # must raise ImportError
python -c "from power_sdk import load_config"          # must raise ImportError
python -c "from power_sdk.models import V2Device"      # must raise ImportError
```

## 6. Example Config Validation

```bash
python -c "
from power_sdk.bootstrap import load_config
from power_sdk.runtime.config import validate_runtime_config
cfg = load_config('examples/runtime.yaml')
validate_runtime_config(cfg)
print('OK')
"
```

## 7. CHANGELOG

- [ ] `## [2.1.0]` section present with correct date
- [ ] Breaking changes clearly listed under **Removed — BREAKING**

## 8. Version Bump

- [ ] `pyproject.toml` version updated to `2.1.0`
- [ ] `power_sdk/__init__.py` `__version__` matches

## 9. Git

- [ ] `git status` clean (no uncommitted changes)
- [ ] Release commit tagged: `git tag v2.1.0`
- [ ] Tag pushed: `git push origin v2.1.0`

## 10. CI (GitHub Actions)

- [ ] All CI jobs green on the release commit:
  - `Ruff (Lint + Format)`
  - `MyPy (Type Check)`
  - `Pytest (Python 3.10 / 3.11 / 3.12)`
  - `Runtime DSL Validation`
  - `Quality Gate (All Checks)`
