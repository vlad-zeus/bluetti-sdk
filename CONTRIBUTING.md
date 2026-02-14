# Contributing to Bluetti SDK

Thank you for your interest in contributing to the Bluetti SDK! This document provides guidelines and requirements for contributions.

---

## Code of Conduct

- Be respectful and professional
- Focus on constructive feedback
- Collaborate openly and transparently
- Follow project conventions and standards

---

## Development Setup

### Prerequisites

- Python 3.10, 3.11, or 3.12
- Git for version control
- Virtual environment tool (venv or conda)

### Setup Steps

```bash
# Clone repository
git clone https://github.com/yourusername/bluetti-sdk.git
cd bluetti-sdk

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Verify setup
pytest
```

---

## Pull Request Requirements

### Before Submitting

All PRs must pass the following checks:

#### 1. Quality Gates (Mandatory)

```bash
# Run all quality checks
ruff check bluetti_sdk tests           # Linting
ruff format --check bluetti_sdk tests  # Format check
mypy bluetti_sdk                       # Type checking
pytest -q --maxfail=1                  # All tests passing
```

**All checks must pass before PR submission.** The CI workflow will enforce these checks.

#### 2. Test Coverage

- **New features**: Must include unit tests with ≥80% coverage
- **Bug fixes**: Must include regression tests demonstrating the fix
- **Refactoring**: Existing tests must continue passing
- **Integration tests**: Required for protocol or transport changes

Example test structure:
```python
def test_feature_name():
    """Test that feature X does Y correctly."""
    # Arrange
    client = create_test_client()

    # Act
    result = client.do_something()

    # Assert
    assert result.success is True
```

#### 3. Code Quality Standards

**Linting (ruff)**
- No errors allowed
- Warnings should be addressed or documented
- Use `ruff check --fix` for auto-fixable issues

**Type Hints (mypy)**
- All functions must have type hints
- No `Any` types without justification
- Use strict mode (enabled in pyproject.toml)

**Formatting (ruff format)**
- Auto-format before committing
- Line length: 88 characters (Black-compatible)
- Consistent style across codebase

#### 4. Documentation

**Code Documentation**
- Docstrings for all public APIs (classes, functions, modules)
- Use Google-style docstrings
- Include examples for complex APIs

Example docstring:
```python
def read_block(self, block_id: int, register_count: int | None = None) -> ParsedBlock:
    """Read and parse a protocol block.

    Args:
        block_id: Block ID to read (e.g., 100, 1300, 6000)
        register_count: Number of registers to read (default: auto-detect)

    Returns:
        ParsedBlock with field values extracted

    Raises:
        TransportError: If communication fails
        ParserError: If block parsing fails

    Example:
        >>> client.connect()
        >>> block = client.read_block(1300, register_count=16)
        >>> print(block.values['frequency'])
        50.0
    """
```

**README Updates**
- Update README.md if adding user-facing features
- Add examples for new public APIs
- Update Supported Blocks table if adding schemas

#### 5. Commit Message Format

Follow conventional commits format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code restructuring without behavior change
- `docs`: Documentation updates
- `test`: Test additions or corrections
- `ci`: CI/CD pipeline changes
- `chore`: Maintenance tasks
- `security`: Security improvements

**Example:**
```
feat(client): add async retry mechanism for transient failures

Implement exponential backoff retry logic for AsyncV2Client to handle
transient network failures gracefully.

- Add configurable max_retries parameter (default: 3)
- Use exponential backoff: 1s, 2s, 4s
- Preserve original exception in retry exhaustion

Closes #42

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

---

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-number-description
```

### 2. Make Changes

- Follow existing code patterns and architecture
- Keep changes focused (single responsibility)
- Write tests alongside code (TDD encouraged)

### 3. Test Locally

```bash
# Run tests
pytest -v

# Run with coverage
pytest --cov=bluetti_sdk --cov-report=html

# Check quality
ruff check bluetti_sdk tests
ruff format bluetti_sdk tests
mypy bluetti_sdk
```

### 4. Commit Changes

```bash
git add <files>
git commit -m "type(scope): description"
```

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Create PR via GitHub with:
- Clear title following commit format
- Description of changes and motivation
- Link to related issues
- Screenshots/examples if applicable

### 6. Address Review Feedback

- Respond to all review comments
- Push additional commits to address feedback
- Request re-review when ready

### 7. Merge

- Squash commits if requested
- Ensure CI checks pass
- Maintainer will merge when approved

---

## Testing Guidelines

### Unit Tests

Location: `tests/unit/`

**Requirements:**
- Fast execution (<1s per test)
- No external dependencies (use mocks)
- Isolated (no shared state)
- Deterministic (no randomness)

**Example:**
```python
from unittest.mock import Mock
import pytest

@pytest.fixture
def mock_transport():
    transport = Mock()
    transport.connect = Mock()
    transport.is_connected = Mock(return_value=True)
    return transport

def test_client_connect(mock_transport):
    """Test that client calls transport.connect()."""
    client = V2Client(mock_transport, profile)
    client.connect()
    mock_transport.connect.assert_called_once()
```

### Integration Tests

Location: `tests/integration/`

**Requirements:**
- Test layer interactions
- May use real dependencies (but not hardware)
- Should complete in <10s

**Example:**
```python
def test_full_read_parse_flow():
    """Test complete flow: transport → protocol → parser."""
    transport = MockMQTTTransport()
    client = V2Client(transport, get_device_profile("EL100V2"))

    # Simulate device response
    transport.set_mock_response(1300, mock_grid_data_bytes)

    # Test full flow
    result = client.read_block(1300)
    assert result.values['frequency'] == 50.0
```

### Test Organization

```
tests/
├── unit/                    # Fast, isolated unit tests
│   ├── protocol/            # Protocol layer tests
│   ├── transport/           # Transport layer tests
│   ├── models/              # Model tests
│   └── test_client.py       # Client tests
├── integration/             # Integration tests
│   └── test_v2_integration.py
└── conftest.py              # Shared fixtures
```

---

## Architecture Principles

### Layer Separation

Follow strict layer boundaries:

```
V2Client (orchestration)
    ↓
┌──────────┬──────────┬──────────┬──────────┐
│  MQTT    │ PROTOCOL │V2 PARSER │  DEVICE  │
│TRANSPORT │  LAYER   │  LAYER   │  MODEL   │
└──────────┴──────────┴──────────┴──────────┘
```

- **Transport**: No Modbus/protocol knowledge
- **Protocol**: No schema knowledge
- **Parser**: No transport knowledge
- **Device**: No byte manipulation

### Design Patterns

- **Dependency Injection**: Inject dependencies via constructors
- **Interface Contracts**: Define clear interfaces between layers
- **Immutability**: Prefer frozen dataclasses for data models
- **Instance-scoped state**: Avoid global mutable state
- **Fail-fast**: Validate early, raise specific exceptions

### Code Quality Rules

- **DRY**: Don't Repeat Yourself (extract common logic)
- **SOLID**: Follow SOLID principles
- **YAGNI**: You Aren't Gonna Need It (no premature optimization)
- **KISS**: Keep It Simple, Stupid (simplicity over cleverness)

---

## Release Process

1. **Version Bump**: Update `__version__` in `bluetti_sdk/__init__.py`
2. **Changelog**: Update CHANGELOG.md with changes
3. **Tag**: Create git tag (e.g., `v2.1.0`)
4. **Build**: `python -m build`
5. **Publish**: `python -m twine upload dist/*`

---

## Getting Help

- 📖 [Documentation](docs/)
- 🐛 [Issue Tracker](https://github.com/yourusername/bluetti-sdk/issues)
- 💬 [Discussions](https://github.com/yourusername/bluetti-sdk/discussions)

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
