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

# Check linting
make lint

# Format code
make format

# Validate everything
make validate
```

## Running Locally

```bash
# Test building an exporter
./core/scripts/local_test.sh node_exporter

# Validate manifest
python3 -m core.engine.builder --manifest exporters/my_exporter/manifest.yaml --arch amd64 --output-dir /tmp/test
```

See [Testing Guide](testing.md) for more details.
