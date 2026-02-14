# Pull Request

## Description

<!-- Provide a clear and concise description of your changes -->

## Type of Change

<!-- Mark the relevant option with an "x" -->

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to change)
- [ ] Documentation update
- [ ] Code refactoring (no functional changes)
- [ ] Performance improvement
- [ ] Security fix

## Related Issues

<!-- Link to related issues using #issue_number -->

Fixes #
Relates to #

## Changes Made

<!-- List the key changes made in this PR -->

-
-
-

## Testing

### Test Coverage

<!-- Describe the tests you've added or modified -->

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] All existing tests pass

### Manual Testing

<!-- Describe any manual testing performed -->

-
-

## Quality Checklist

<!-- Verify all items before submitting -->

### Required Checks

- [ ] `ruff check bluetti_sdk tests` passes
- [ ] `ruff format --check bluetti_sdk tests` passes
- [ ] `mypy bluetti_sdk` passes
- [ ] `pytest -q --maxfail=1` passes (all tests)
- [ ] No decrease in test coverage

### Code Quality

- [ ] Added docstrings for all new public APIs
- [ ] Followed existing code patterns and architecture
- [ ] Updated README.md if adding user-facing features
- [ ] Updated CHANGELOG.md with changes

### Commit Message

- [ ] Follows conventional commits format: `type(scope): description`
- [ ] Includes `Co-Authored-By` if applicable

## Screenshots / Examples

<!-- If applicable, add screenshots or code examples -->

```python
# Example usage

```

## Breaking Changes

<!-- If this is a breaking change, describe the impact and migration path -->

**Impact:**


**Migration Guide:**


## Additional Notes

<!-- Any additional information reviewers should know -->


---

## Reviewer Checklist

<!-- For maintainers -->

- [ ] Code follows project architecture and patterns
- [ ] Tests are comprehensive and pass
- [ ] Documentation is clear and complete
- [ ] No security vulnerabilities introduced
- [ ] CHANGELOG.md updated
- [ ] Ready to merge
