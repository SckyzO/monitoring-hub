# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Language Preference

**IMPORTANT**: All responses and explanations must be in French. However, all code and code comments must be in English.

## Project Overview

Monitoring Hub is an automated Software Factory that transforms YAML manifests into production-ready Prometheus exporters. The system builds both RPM packages (for EL8/9/10) and Docker images (OCI) for multiple architectures (x86_64, aarch64), all distributed through automated GitHub Pages hosting and GHCR registry.

## Essential Commands

### Development Setup
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate
pip install -r core/requirements.txt
```

### Creating New Exporters
```bash
# Interactive mode (recommended)
./core/scripts/create_exporter.py

# With arguments
./core/scripts/create_exporter.py --name my_exporter --repo owner/repo --category System
```

### Local Testing
```bash
# Test full build pipeline (generate + RPM + Docker)
./core/scripts/local_test.sh <exporter_name>

# Specific options
./core/scripts/local_test.sh <exporter_name> --arch arm64 --el9 --docker --validate
```

### Manual Build Steps (Advanced)
```bash
# 1. Generate build artifacts from manifest
export PYTHONPATH=$(pwd)
python3 -m core.engine.builder --manifest exporters/<name>/manifest.yaml --arch amd64 --output-dir build/<name>

# 2. Build RPM
./core/scripts/build_rpm.sh build/<name>/<name>.spec build/<name>/rpms amd64 almalinux:9

# 3. Build Docker image
docker build -t monitoring-hub/<name>:local build/<name>
```

### Testing & Quality

```bash
# Run all tests with coverage
pytest

# Run specific test file
pytest core/tests/test_builder.py

# Run with verbose output
pytest -v

# Run tests in parallel
pytest -n auto

# Check code coverage
pytest --cov=core --cov-report=html

# Run linting
ruff check core/

# Auto-fix linting issues
ruff check --fix core/

# Format code
ruff format core/

# Type checking
mypy core/

# Run pre-commit on all files
pre-commit run --all-files

# Validate manifest schema
python3 -m core.engine.builder --manifest exporters/<name>/manifest.yaml --arch amd64 --output-dir /tmp/test
```

### State Management
```bash
# Check what needs rebuilding (compares local vs deployed)
export PYTHONPATH=$(pwd)
python3 -m core.engine.state_manager
```

## Architecture

### Core Components

**`core/engine/`** - The build orchestration system:
- **`builder.py`** - Downloads upstream binaries, extracts them, renders Jinja2 templates (Dockerfile, .spec files), and produces build artifacts in `build/` directory
- **`schema.py`** - Marshmallow-based manifest validation (enforces YAML structure defined in `manifest.reference.yaml`)
- **`state_manager.py`** - Smart incremental builds: compares local manifests against deployed `catalog.json` to determine what changed
- **`site_generator.py`** - Generates the static portal (index.html) from all manifests
- **`watcher.py`** - Automated upstream version checker that opens PRs when new releases are detected

**`core/templates/`** - Jinja2 templates used for all exporters:
- **`default.spec.j2`** - RPM spec file template (creates systemd services, system users, directory structure)
- **`Dockerfile.j2`** - Multi-stage Docker build template (uses Red Hat UBI 9 Minimal)
- **`index.html.j2`** - Portal page template

**`core/scripts/`** - Helper utilities:
- **`create_exporter.py`** - Interactive scaffolding tool for new exporters
- **`local_test.sh`** - End-to-end local build tester with validation
- **`build_rpm.sh`** - Docker-based RPM builder (uses rpmbuild in isolation)
- **`rpm_entrypoint.sh`** - Internal script for RPM build container
- **`validate_site.py`** - Validates generated portal HTML

### Build Flow

1. **Discovery Phase** (`state_manager.py`):
   - Fetches deployed `catalog.json` from GitHub Pages
   - Compares with local `exporters/*/manifest.yaml` files
   - Outputs JSON list of changed exporters for CI matrix

2. **Generation Phase** (`builder.py`):
   - Downloads upstream binary from GitHub releases (handles various naming conventions via `archive_name` pattern)
   - Extracts binaries (supports `.tar.gz` and `.gz` formats)
   - Renders templates with manifest variables
   - Copies assets from `exporters/<name>/assets/` to build directory

3. **Build Phase** (CI workflows):
   - **RPM**: Parallel builds per distro (el8/el9/el10) and arch (x86_64/aarch64)
   - **Docker**: Multi-platform builds (amd64/arm64) with automated validation

4. **Validation Phase**:
   - Port checks: Container starts and serves metrics on expected port
   - Command checks: Binary runs with `--version` or custom validation command

5. **Distribution Phase**:
   - RPMs pushed to GitHub Pages YUM repository (`el{8,9,10}/<arch>/`)
   - Docker images pushed to GHCR (`ghcr.io/sckyzo/monitoring-hub/<name>:latest`)
   - Portal regenerated with updated catalog

### Manifest System

Each exporter is defined by `exporters/<name>/manifest.yaml` following the schema in `manifest.reference.yaml`. The manifest is the single source of truth for:
- Upstream source (GitHub repo, version, release naming pattern)
- Build configuration (binary names, architectures, extra sources)
- RPM packaging (systemd services, config files, directories, dependencies)
- Docker image (base image, entrypoint, validation tests)

**Template Overrides**: Exporters can provide custom Jinja2 templates in `exporters/<name>/templates/`:
- `<exporter>.spec.j2` - Custom RPM spec
- `Dockerfile.j2` - Custom Docker build

These override global templates while still receiving all manifest variables.

### CI/CD Workflows

**`.github/workflows/release.yml`** - Main build pipeline:
- Triggered on push to main or manual dispatch
- Uses `state_manager.py` for incremental builds
- Parallel matrix builds for RPM and Docker
- Automatic catalog and portal updates

**`.github/workflows/scan-updates.yml`** - Automated watcher:
- Runs on schedule (checks upstream for new versions)
- Opens PRs with version bumps
- Auto-merges if CI passes

**`.github/workflows/build-pr.yml`** - PR validation:
- Builds only changed exporters
- Runs validation tests

**`.github/workflows/update-site.yml`** - Portal regeneration:
- Rebuilds static site when catalog changes

## Key Conventions

### Version Handling
- Manifest versions should match upstream tags (keep 'v' prefix if upstream uses it)
- `state_manager.py` strips 'v' prefix for comparison with catalog
- `builder.py` handles both prefixed and non-prefixed versions via `{version}` and `{clean_version}` template variables

### Architecture Mapping
- Upstream/Docker: `amd64`, `arm64`
- RPM: `x86_64`, `aarch64`
- Mapping defined in `core/config/settings.py:ARCH_MAP`

### File Paths (FHS Compliant)
- Binaries: `/usr/bin/<name>` (can override with `artifacts.rpm.install_path`)
- Config files: `/etc/<name>/` (defined in `artifacts.rpm.extra_files`)
- Data directories: `/var/lib/<name>/` (defined in `artifacts.rpm.directories`)
- Systemd units: `/usr/lib/systemd/system/<name>.service`

### Systemd Services
When `artifacts.rpm.systemd.enabled: true`:
- Service runs as system user (if `system_user` specified, otherwise root)
- Automatically created with `After=network.target`
- Default restart policy: `on-failure`
- ExecStart uses binary at install path with optional arguments

### Asset Management
Files in `exporters/<name>/assets/` are automatically available during build:
- Referenced in manifest via `source: assets/filename`
- Copied to RPM build tree
- Can be included in Docker images via custom templates
- Config files should use `config: true` for `%config(noreplace)` directive

## Common Patterns

### Simple Exporter (No Config)
```yaml
name: example_exporter
description: Simple metrics exporter
version: v1.0.0
upstream:
  type: github
  repo: owner/example_exporter
build:
  method: binary_repack
  binary_name: example_exporter
artifacts:
  rpm:
    enabled: true
    systemd:
      enabled: true
  docker:
    enabled: true
    entrypoint: ["/usr/bin/example_exporter"]
    validation:
      port: 9100
```

### Exporter with Config File
```yaml
artifacts:
  rpm:
    enabled: true
    system_user: example_exporter
    systemd:
      enabled: true
      arguments: ["--config.file=/etc/example_exporter/config.yml"]
    extra_files:
      - source: assets/config.yml
        dest: /etc/example_exporter/config.yml
        mode: "0640"
        config: true
    directories:
      - path: /var/lib/example_exporter
        owner: example_exporter
        group: example_exporter
```

### Custom Archive Naming
```yaml
upstream:
  repo: owner/repo
  archive_name: "{name}-{clean_version}-linux-{arch}.tar.gz"
```

### Multi-Binary Package
```yaml
build:
  binary_name: main_tool
  extra_binaries: [helper_tool, cli_tool]
```

## Commit Conventions

Le projet utilise les conventions Conventional Commits. Format : `type(scope): description`

### Types de commits

- **feat** : Nouvelle fonctionnalité
  - `feat(exporters): add redis_exporter support`
  - `feat(builder): add retry logic for downloads`

- **fix** : Correction de bug
  - `fix(state_manager): handle version comparison edge case`
  - `fix(builder): correct archive extraction for arm64`

- **chore** : Maintenance, dépendances, configuration
  - `chore(deps): update Python dependencies`
  - `chore: update exporters versions`

- **docs** : Documentation uniquement
  - `docs(readme): update installation instructions`
  - `docs: add architecture diagram`

- **test** : Ajout ou modification de tests
  - `test(builder): add unit tests for download logic`
  - `test: increase coverage to 60%`

- **refactor** : Refactoring sans changement de fonctionnalité
  - `refactor(builder): simplify archive extraction`
  - `refactor: extract common validation logic`

- **perf** : Amélioration de performance
  - `perf(state_manager): cache remote catalog results`

- **ci** : Modifications CI/CD
  - `ci: add security scanning workflow`
  - `ci(release): optimize build matrix`

- **style** : Formatage, linting (pas de changement de code)
  - `style: apply ruff formatting`
  - `style: fix linting issues`

### Scopes communs

- `exporters` : Modifications liées aux exporters
- `builder` : Module builder
- `state_manager` : Module state management
- `watcher` : Module watcher
- `ci` : GitHub Actions workflows
- `deps` : Dépendances
- `dev` : Outils de développement

### Exemples

```bash
# Feature
git commit -m "feat(exporters): add nginx_exporter with custom config"

# Bug fix
git commit -m "fix(ping_exporter): fix release URL pattern"

# Multiple changes
git commit -m "chore: update exporters versions (#21)"

# Breaking change (ajouter ! après le type)
git commit -m "feat(builder)!: change manifest schema structure"
```

## Important Notes

- Always validate manifests before committing: changes trigger full CI builds
- The `catalog.json` in repository root is auto-generated; never edit manually
- GitHub Pages serves from `gh-pages` branch (managed by CI)
- Docker builds always use amd64 for generation, then multi-platform build
- Local testing uses Docker for RPM isolation (no need for rpmbuild on host)
- Version updates should be done via automated watcher or manual manifest edits
- **Ne jamais** ajouter "Co-Authored-By: Claude" dans les commits
