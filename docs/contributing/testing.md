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
