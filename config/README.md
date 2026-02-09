# config/ - Configuration Directory

This directory contains all configuration files for the Monitoring Hub project, organized by category.

## Structure

```
config/
├── docker/          # Docker-related configuration
│   └── Dockerfile.dev    # Development container definition
├── docs/            # Documentation configuration
│   └── mkdocs.yml        # MkDocs configuration
├── linting/         # Code quality and linting configuration
│   ├── .pre-commit-config.yaml  # Pre-commit hooks configuration
│   ├── .stylelintrc.json        # CSS linting rules (Stylelint)
│   └── .stylelintignore         # CSS linting ignore patterns
└── python/          # Python-specific configuration
    ├── pyproject.toml      # Python project config (ruff, build)
    └── pytest.ini          # PyTest configuration
```

## File Descriptions

### docker/Dockerfile.dev
Development Docker image definition with:
- Python 3.12
- Node.js + npm (for Stylelint)
- All Python dependencies (base, dev, docs)
- Git configuration for mounted volumes

**Build**: `./devctl build` or `docker build -f config/docker/Dockerfile.dev -t monitoring-hub-dev:latest .`

### docs/mkdocs.yml
MkDocs configuration for generating project documentation:
- Theme: Material for MkDocs
- Plugins: search, git-revision-date, minify, autorefs
- Extensions: admonitions, code highlighting, content tabs

**Usage**: `./devctl docs-build` or `mkdocs build`

### linting/.pre-commit-config.yaml
Pre-commit hooks for automated code quality checks:
- Trailing whitespace removal
- EOF fixer
- YAML validation
- File size limits
- Ruff (Python linting and formatting)
- Mypy (type checking)

**Install**: `pre-commit install`
**Run**: `pre-commit run --all-files`

### linting/.stylelintrc.json
Stylelint configuration for CSS/HTML linting:
- Base: `stylelint-config-standard`
- Order plugin for property sorting
- Ignores: Generated files, external assets
- Validates: `**/*.css`, `**/*.html.j2`

**Usage**: `./devctl lint-css`

### python/pyproject.toml
Python project configuration:
- **Build system**: setuptools
- **Ruff config**: Python linting and formatting
  - Target: Python 3.9+
  - Line length: 100
  - Rules: pyflakes, pycodestyle, isort
- **Black**: Code formatting (via ruff)

**Usage**: `./devctl lint` or `ruff check .`

### python/pytest.ini
PyTest configuration:
- Test paths: `core/tests`
- Markers: unit, integration, slow
- Coverage settings
- Output formatting

**Usage**: `./devctl test`

## Symlinks

Some tools expect configuration files at the root. Symlinks are created for backward compatibility:
- `.stylelintrc.json` → `config/linting/.stylelintrc.json`
- `.stylelintignore` → `config/linting/.stylelintignore`

## Modifying Configurations

When modifying configuration files, ensure:
1. Changes are tested with `./devctl ci`
2. Docker image is rebuilt if dependencies change
3. Documentation is updated if behavior changes
4. Symlinks remain valid if files are renamed

## Related Directories

- `requirements/` - Python dependencies (base, dev, docs)
- `scripts/` - Utility scripts (setup, build helpers)
- `core/` - Core engine configuration (runtime settings)
