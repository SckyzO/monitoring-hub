# Contributing to Monitoring Hub

Thank you for your interest in contributing to Monitoring Hub! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Adding a New Exporter](#adding-a-new-exporter)
- [Testing](#testing)
- [Code Quality](#code-quality)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

### Prerequisites

- **Docker** (required) - All development happens in containers
- **Git** - For version control
- No local Python installation needed!

### Setup

1. **Fork the repository** on GitHub
2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/monitoring-hub.git
   cd monitoring-hub
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/SckyzO/monitoring-hub.git
   ```
4. **Build the dev image**:
   ```bash
   ./devctl build
   ```

## Development Workflow

### Available Commands

```bash
# Development checks
./devctl test                 # Run all tests
./devctl test-cov             # Run tests with coverage
./devctl lint                 # Check code with ruff
./devctl lint-fix             # Auto-fix linting issues
./devctl format               # Format code
./devctl type-check           # Run mypy type checking
./devctl ci                   # Run all CI checks

# Working with exporters
./devctl create-exporter      # Create new exporter interactively
./devctl build-exporter <name>  # Build specific exporter
./devctl test-rpm <name>      # Test RPM build
./devctl test-deb <name>      # Test DEB build

# Other utilities
./devctl shell                # Open interactive shell
./devctl clean                # Clean build artifacts
```

## Adding a New Exporter

### Using the Generator (Recommended)

```bash
./devctl create-exporter
```

The interactive tool will:
1. Ask for exporter details (name, GitHub repo, version, category)
2. Generate a complete `manifest.yaml`
3. Create the exporter directory structure
4. Validate the manifest

### Manual Creation

1. Create directory structure:
   ```bash
   mkdir -p exporters/my_exporter
   ```

2. Create `manifest.yaml`:
   ```yaml
   name: my_exporter
   version: "1.0.0"
   description: "Brief description"
   category: System

   upstream:
     type: github
     repo: owner/repo

   build:
     method: binary
     binary_name: my_exporter

   artifacts:
     rpm:
       enabled: true
       targets: [el8, el9, el10]
       systemd:
         enabled: true
         arguments: ["--config.file=/etc/my_exporter/config.yml"]

     docker:
       enabled: true
       entrypoint: ["/usr/bin/my_exporter"]
       validation:
         enabled: true
         port: 9100
   ```

3. Test the build:
   ```bash
   ./devctl build-exporter my_exporter
   ./devctl test-rpm my_exporter
   ```

### Manifest Reference

See [`manifest.reference.yaml`](manifest.reference.yaml) for complete documentation of all available fields and options.

## Testing

### Running Tests

```bash
# All tests
./devctl test

# With coverage
./devctl test-cov

# Specific test file
./devctl test core/tests/test_builder.py

# Specific test
./devctl test core/tests/test_builder.py::TestLoadManifest::test_load_valid_manifest
```

### Testing Exporters Locally

```bash
# Quick smoke test (generate + build + test)
./core/scripts/local_test.sh node_exporter

# Test specific distribution
./devctl test-rpm node_exporter --el10

# Test DEB build
./devctl test-deb node_exporter ubuntu-24.04
```

## Code Quality

### Pre-commit Checks

Before committing, ensure all checks pass:

```bash
./devctl ci
```

This runs:
- Linting (ruff)
- Formatting check (ruff)
- Type checking (mypy)
- CSS linting (stylelint)
- YAML linting (yamllint)
- All tests (pytest)

### Code Standards

- **Python**: Follow PEP 8, use type hints
- **Formatting**: Automatic with `ruff format`
- **Linting**: Zero warnings with `ruff check`
- **Type Safety**: Pass `mypy --strict` where possible
- **Tests**: Maintain >80% coverage

### Pre-commit Hooks

Install pre-commit hooks to catch issues early:

```bash
# Inside container
./devctl shell
pre-commit install
```

## Commit Guidelines

### Conventional Commits

Use [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `chore`: Maintenance tasks
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `ci`: CI/CD changes

**Examples:**

```bash
feat(exporters): add PostgreSQL exporter support

Add full support for PostgreSQL exporter with:
- RPM packages for el8/el9/el10
- Docker image with validation
- Systemd integration

Closes #42

---

fix(builder): handle missing archive_name gracefully

Previously crashed when archive_name was not specified.
Now defaults to standard Prometheus naming convention.

---

docs: update manifest reference with new fields

Add documentation for:
- archive_name dict format
- extra_sources configuration
- validation options
```

### Commit Message Rules

- **Subject line**: Max 72 characters, imperative mood
- **Body**: Wrap at 72 characters, explain *why* not *what*
- **Footer**: Reference issues/PRs (e.g., `Closes #123`, `Fixes #456`)
- **No AI/automation mentions**: All commits appear as authored by repository owner

## Pull Request Process

### Before Submitting

1. **Sync with upstream**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run all checks**:
   ```bash
   ./devctl ci
   ```

3. **Test your changes**:
   ```bash
   ./devctl test
   ```

### Creating a PR

1. **Push to your fork**:
   ```bash
   git push origin feature/my-feature
   ```

2. **Open a Pull Request** on GitHub

3. **Fill out the PR template** completely

4. **Wait for CI checks** to pass

5. **Respond to review feedback** promptly

### PR Requirements

- [ ] All CI checks pass
- [ ] Tests added/updated for changes
- [ ] Documentation updated if needed
- [ ] Commit messages follow conventions
- [ ] No merge commits (rebase instead)
- [ ] Branch is up-to-date with main

### PR Review Process

1. **Automated checks** run (build, test, lint)
2. **Maintainer review** within 2-3 days
3. **Feedback/changes** requested if needed
4. **Approval** from maintainer
5. **Merge** (squash & merge)

### After Merge

Your PR will be:
- Squashed into a single commit
- Merged to `main` branch
- Automatically deployed via CI/CD

## Questions?

- **General questions**: Open a [Discussion](https://github.com/SckyzO/monitoring-hub/discussions)
- **Bug reports**: Open an [Issue](https://github.com/SckyzO/monitoring-hub/issues/new/choose)
- **Feature requests**: Open an [Issue](https://github.com/SckyzO/monitoring-hub/issues/new/choose)

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (see [LICENSE](LICENSE)).
