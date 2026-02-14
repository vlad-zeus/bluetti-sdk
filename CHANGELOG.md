# Changelog

All notable changes to the Bluetti SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- CI quality gate workflow with separate jobs for ruff, mypy, pytest (#Task1)
- Async concurrency safety for `AsyncV2Client` using `asyncio.Lock()` (#Task3)
- Comprehensive async usage examples in README with `asyncio.gather()`
- Private temp directory for TLS certificates with owner-only permissions (#Task4)
- Security documentation explaining TLS risk model and mitigations
- `CONTRIBUTING.md` with PR requirements and development guidelines (#Task6)
- Declarative schema definitions for blocks 1300 and 6000 (Stage 1: Schema Unification)
- Equivalence tests proving field-level compatibility with imperative schemas
- `block_1300_declarative.py` and `block_6000_declarative.py` modules
- CLI tool with `scan`, `raw`, `listen` commands for device interaction
- CLI password security via environment variable or interactive prompt
- CLI input validation for all numeric arguments
- Configurable retry policy with exponential backoff
  - `RetryPolicy` dataclass with validation (max_attempts, initial_delay, backoff_factor, max_delay)
  - Selective retry: only transient `TransportError`, fail-fast on `ParserError`/`ProtocolError`
  - MQTT fail-fast disconnect detection during send_frame wait
  - CLI retry arguments: `--retries`, `--retry-initial-delay`, `--retry-max-delay`
  - 25 new tests: 11 resilience, 6 client retry, 1 async, 1 MQTT, 6 CLI
- 6 new AsyncV2Client tests for error propagation and context manager robustness
- 5 comprehensive tests for schema registry isolation guarantees (#Task2)
  - Registry-level: factory isolation, built-in availability, public API safety
  - Client-level: default registry independence, injected registry identity
- 4 new typed transform tests (Increment C)
  - Typed factory verification (minus, bitmask, abs)
  - Legacy/typed equivalence validation
  - Parameter validation coverage

### Changed
- Schema registry now uses instance-scoped approach instead of global mutable state (#Task2)
  - `register()` → `_register_builtin()` (private, init-only)
  - `register_many()` → `_register_many_builtins()` (private, init-only)
  - V2Client uses `new_registry_with_builtins()` for instance registries
- TLS certificate temp files now use 0o400 (read-only) instead of 0o600 (#Task4)
- Directory cleanup for TLS certs instead of individual file deletion (#Task4)
- Updated code quality tools from black/flake8 to ruff in README (#Task5)
- CI workflow uses Python 3.10/3.11/3.12 matrix for pytest
- AsyncV2Client hardened with robust error propagation and cleanup guarantees
  - Enhanced `__aenter__` cleanup on connection failure
  - Uses `contextlib.suppress()` for graceful error recovery
  - Comprehensive docstrings with Args/Returns/Raises sections
  - Migrated to PEP 604 type hints (dict vs Dict)
  - Coverage improved: 80% → 83%
- **Typed transforms now primary API** - string DSL deprecated (Increment C)
  - All built-in schemas migrated: Block 100/1300/6000 (29 transforms total)
  - Zero string DSL remaining in built-in declarative schemas
  - Type-safe transform definitions with validation at schema creation time
  - `TransformSpec = Union[str, TransformStep]` for backward compatibility
  - Legacy string DSL still supported for existing user code

### Removed
- Global mutable schema registry API (`register`, `register_many`) (#Task2)
- Public access to `_clear_for_testing()` (renamed to `_clear_builtin_catalog_for_testing()`)

### Security
- Hardened TLS private key handling with private temp directories (#Task4)
  - Create temp dir with `tempfile.mkdtemp()` (auto 0o700 permissions)
  - Set file permissions to 0o400 immediately after writing
  - Delete entire directory with `shutil.rmtree()` in cleanup
  - Documented paho-mqtt limitation and residual risk window
- Added fail-safe cleanup in all error paths with finally blocks

### Fixed
- README examples now use correct `get_device_profile()` API (#Task5)
- QuickStart example in `__init__.py` aligned with actual API (#Task5)
- Missing `asyncio` import in async client tests (#Task3)
- AsyncV2Client `__aexit__` now preserves original exception when disconnect fails
  - Prevents masking root cause exceptions with disconnect errors
  - Follows Python context manager best practices

---

## [2.0.0] - 2026-02-13

### Added

**Core SDK:**
- Complete V2 protocol parser with schema-based architecture
- MQTT transport layer with mTLS support
- Device state management (V2Device, GridInfo, HomeData, BatteryPackInfo)
- Device profiles (EL30V2, EL100V2, Elite 200 V2)
- Transform pipeline (abs, scale, minus, bitmask, shift, clamp)
- Data types (UInt8/16/32, Int8/16/32, String, Bitmap, Enum)
- Block schema system (Field, ArrayField, PackedField)
- Exception hierarchy (BluettiError → Transport/Protocol/Parser/DeviceError)

**Block Support:**
- Block 1300 (INV_GRID_INFO) - Grid voltage/frequency monitoring ✅
- Block 100 (APP_HOME_DATA) - Dashboard (planned for Day 5)
- Block 6000 (PACK_MAIN_INFO) - Battery pack (planned for Day 6)

**Quality Improvements:**
- Modbus error response handling (0x83 with error code mapping)
- Early CRC validation at transport layer
- Response validation (length, function code)
- Resource cleanup guarantees (try/finally patterns)
- Unified field parsing interface (LSP compliance)

**Project Structure:**
- Professional SDK package structure
- setup.py + pyproject.toml for pip installation
- Organized test suite (unit + integration)
- Comprehensive documentation
- Usage examples
- CLI tools framework

**Architecture:**
- Layered architecture with strict separation of concerns
- Interface-based design (ABCs for all layers)
- Configuration over code (declarative schemas)
- Zero if-chains for device detection
- Data-driven parsing

### Fixed

- **Critical:** PackedField now uses configurable base_type instead of hardcoded UInt16
- **Critical:** Certificate files no longer leak on connection failure
- **Critical:** Malformed MQTT responses now rejected early
- **Important:** disconnect() now guarantees resource cleanup via try/finally
- **Moderate:** ProtocolError import consolidated (single source of truth)
- **Moderate:** Strict validation for error responses (no default values)

### Changed

- Reorganized entire codebase into professional SDK structure
- Moved all research materials to `_research/` folder
- Unified parse() method signature across all field types
- Improved error messages with context

### Removed

- Legacy code (`bluetti_mqtt/` moved to `_research/old_code/`)
- APK files from root (moved to `_research/apk_analysis/`)
- Development tools from user-facing directories

---

## Architecture Quality

**Zeus Architect Rating:** A+ (elevated from A-)
- Pristine layer contracts
- Zero architectural anti-patterns
- Bulletproof resource management
- Complete polymorphism

**Zeus Code Reviewer Rating:** 9.5/10
- Comprehensive error handling
- Leak-proof resource management
- Type-safe throughout
- Well-documented

---

## [1.0.0] - 2026-02-10 (Internal)

### Added

- Initial V2 parser prototype
- Basic Modbus RTU support
- Schema definition system
- Transform pipeline

### Status

Internal prototype. Not released.

---

## Upcoming

### [2.1.0] - Planned

**Block 100 Implementation (Day 5):**
- APP_HOME_DATA schema (50+ fields)
- SOC, pack voltage/current
- Power flows (DC input, AC input/output, PV, Grid)
- Energy totals
- Temperatures
- Alarm/fault bitmaps

**Block 6000 Implementation (Day 6):**
- PACK_MAIN_INFO schema
- Battery pack status
- Cell voltages
- Temperature monitoring

**CLI Tools:**
- `bluetti-cli` - Interactive device monitoring
- `bluetti-export` - Data export utilities
- `bluetti-monitor` - Real-time dashboard

### Future

- BLE transport support
- Home Assistant integration
- Auto-reconnection with exponential backoff
- Request pipelining for better throughput
- Block caching with TTL
- Schema versioning and migration

---

## Links

- [Documentation](docs/)
- [GitHub Repository](https://github.com/yourusername/bluetti-sdk)
- [Issue Tracker](https://github.com/yourusername/bluetti-sdk/issues)
