# Testing Guide

How to write and run tests for Monitoring Hub.

## Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test file
pytest core/tests/test_builder.py

# Run specific test
pytest core/tests/test_builder.py::test_load_valid_manifest
```

## Writing Tests

### Unit Tests

```python
def test_my_function():
    result = my_function("input")
    assert result == "expected"
```

### Using Fixtures

```python
def test_with_manifest(sample_manifest):
    assert sample_manifest['name'] == 'test_exporter'
```

## Test Structure

- `core/tests/` - Test files
- `core/tests/fixtures/` - Test data
- `core/tests/conftest.py` - Shared fixtures

See [conftest.py](https://github.com/SckyzO/monitoring-hub/blob/main/core/tests/conftest.py) for available fixtures.

## Code Quality Checks

### Python Linting

Using `ruff` for fast linting and formatting:

```bash
# Check linting
make lint

# Auto-fix issues
make lint-fix

# Format code
make format

# Type checking
make type-check
```

### CSS Linting

Using `stylelint` for CSS quality in portal and templates:

```bash
# Check CSS linting
make docker-lint-css

# Auto-fix CSS issues
make docker-lint-fix
```

Configuration files:
- `.stylelintrc.json` - Stylelint rules (standard + order plugin)
- `.stylelintignore` - Ignored files (generated files, external assets)

Stylelint validates:
- Standalone CSS files
- Embedded `<style>` blocks in Jinja2 templates
- Portal CSS (`core/templates/index.html.j2`)

### Pre-commit Hooks

Pre-commit hooks automatically run before each commit:

```bash
# Install hooks
pre-commit install

# Run manually
make pre-commit

# Update hook versions
pre-commit autoupdate
```

Hooks enforce:
- Trailing whitespace removal
- YAML validation
- Python linting (ruff)
- Type checking (mypy)
- File size limits
