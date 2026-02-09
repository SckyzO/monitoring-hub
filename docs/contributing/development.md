# Development Setup

Get your development environment ready.

## Prerequisites

- Python 3.9+
- Docker or Podman
- Git

## Setup

```bash
# Clone repository
git checkout -b feature/my-feature
cd monitoring-hub

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r core/requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
make install
```

## Development Workflow

```bash
# Run tests
make test

# Check Python linting
make lint

# Check CSS linting (portal and templates)
make docker-lint-css

# Auto-fix linting issues (Python + CSS)
make docker-lint-fix

# Format code
make format

# Type checking
make type-check

# Validate everything
make validate
```

### Docker-based Development

If you prefer not to install Python locally, use Docker-based commands:

```bash
# Build dev container
make docker-build

# Run all checks in container
make docker-ci              # All CI checks
make docker-test            # Tests only
make docker-lint            # Python linting
make docker-lint-css        # CSS linting
make docker-format          # Code formatting
make docker-type-check      # Type checking
```

## Running Locally

```bash
# Test building an exporter
./core/scripts/local_test.sh node_exporter

# Validate manifest
python3 -m core.engine.builder --manifest exporters/my_exporter/manifest.yaml --arch amd64 --output-dir /tmp/test
```

See [Testing Guide](testing.md) for more details.
