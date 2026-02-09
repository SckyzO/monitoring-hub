# Development Setup

Get your development environment ready using our Docker-first workflow.

## Prerequisites

- **Docker** - The only requirement!
- **Git** - For version control

**Optional:**
- Python 3.9+ (only for local development without Docker)

## Quick Start (Recommended)

The simplest way to start is with our `./devctl` CLI:

```bash
# Clone repository
git clone https://github.com/SckyzO/monitoring-hub.git
cd monitoring-hub
git checkout -b feature/my-feature

# Build development Docker image
./devctl build

# Open interactive shell
./devctl shell

# Run tests
./devctl test

# Run linter
./devctl lint
```

That's it! No Python installation needed.

## Alternative: Local Python Setup

If you prefer developing without Docker:

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
make install

# This installs:
# - core/requirements.txt (engine dependencies)
# - requirements-dev.txt (ruff, pytest, mypy)
# - requirements-docs.txt (mkdocs)
# - pre-commit hooks
```

## Development Workflow

### Using devctl (Recommended)

All development tasks are available through `./devctl`:

```bash
# Code quality
./devctl test              # Run tests
./devctl test-cov          # Run tests with coverage
./devctl lint              # Check Python linting
./devctl lint-css          # Check CSS linting
./devctl lint-fix          # Auto-fix linting issues
./devctl format            # Format code
./devctl type-check        # Run type checker
./devctl ci                # Run all CI checks

# Working with exporters
./devctl create-exporter           # Create new exporter
./devctl list-exporters            # List all exporters
./devctl build-exporter <name>     # Build specific exporter
./devctl test-exporter <name>      # Test build exporter

# Documentation
./devctl generate-portal   # Generate web portal
./devctl docs-build        # Build MkDocs docs
./devctl docs-serve        # Serve docs at localhost:8000

# Utilities
./devctl shell             # Open interactive shell
./devctl python <cmd>      # Run Python command
./devctl help              # Show all commands
```

### Using Make

For convenience, most `devctl` commands are aliased in the Makefile:

```bash
make test              # Same as ./devctl test
make lint              # Same as ./devctl lint
make format            # Same as ./devctl format
make ci                # Same as ./devctl ci
```

### Local Python Workflow (Advanced)

If you have Python installed locally and want faster iteration:

```bash
make local-test        # Run tests locally
make local-lint        # Check linting locally
make local-format      # Format code locally
make pre-commit        # Run pre-commit hooks
```

**Note:** Local commands require `make install` first to set up the virtual environment.

## Testing Exporters Locally

### Quick Test

```bash
# Test build an exporter (RPM + Docker + validation)
./devctl test-exporter node_exporter

# With specific options
./devctl test-exporter node_exporter --arch arm64 --el10
```

### Build Artifacts Only

```bash
# Build just the artifacts (no RPM/Docker)
./devctl build-exporter node_exporter

# Output will be in: build/node_exporter/
```

### Validate Manifest

```bash
# Open shell and validate manifest
./devctl shell

# Inside container:
python3 -m core.engine.builder \
  --manifest exporters/my_exporter/manifest.yaml \
  --arch amd64 \
  --output-dir /tmp/test
```

See [Testing Guide](testing.md) for more details.
