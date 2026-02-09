# requirements/ - Python Dependencies

This directory contains all Python dependency files for the Monitoring Hub project.

## Files

### base.txt
Core dependencies required for the builder engine:
- `click` - CLI framework
- `Jinja2` - Template engine
- `marshmallow` - Schema validation
- `PyYAML` - YAML parsing
- `requests` - HTTP client
- `tenacity` - Retry logic
- `packaging` - Version comparison
- `semver` - Semantic versioning

**Usage**: `pip install -r requirements/base.txt`

**Used by**:
- Core engine (`core/engine/`)
- Production builds
- CI/CD workflows

### dev.txt
Development tools and testing dependencies:
- `pytest` - Test framework
- `pytest-cov` - Coverage reporting
- `pytest-mock` - Mocking support
- `pytest-xdist` - Parallel test execution
- `ruff` - Fast Python linter and formatter
- `mypy` - Static type checker
- `pre-commit` - Git hooks framework
- `black` - Code formatter (legacy, replaced by ruff)

**Usage**: `pip install -r requirements/dev.txt`

**Used by**:
- Local development
- Pre-commit hooks
- CI quality checks

### docs.txt
Documentation generation dependencies:
- `mkdocs` - Documentation generator
- `mkdocs-material` - Material theme
- `mkdocs-material-extensions` - Theme extensions
- `mkdocs-autorefs` - Cross-references
- `mkdocstrings` - API documentation from code
- `mkdocstrings-python` - Python language support
- `mkdocs-git-revision-date-localized-plugin` - Git dates
- `mkdocs-minify-plugin` - HTML/CSS/JS minification

**Usage**: `pip install -r requirements/docs.txt`

**Used by**:
- Documentation builds (`./devctl docs-build`)
- GitHub Pages deployment

## Installation

### Docker-First (Recommended)
All dependencies are pre-installed in the development container:
```bash
./devctl build    # Build container with all dependencies
./devctl shell    # Access environment
```

### Local Python Environment
```bash
# Install all dependencies
pip install -r requirements/base.txt -r requirements/dev.txt -r requirements/docs.txt

# Or use make
make install
```

## Updating Dependencies

### Adding a New Dependency

1. **Identify the category**:
   - Core functionality → `base.txt`
   - Testing/linting → `dev.txt`
   - Documentation → `docs.txt`

2. **Add with version pin**:
   ```bash
   echo "new-package==1.2.3" >> requirements/base.txt
   ```

3. **Rebuild Docker image**:
   ```bash
   ./devctl rebuild
   ```

4. **Test**:
   ```bash
   ./devctl ci
   ```

### Upgrading Dependencies

```bash
# Check for outdated packages
pip list --outdated

# Update specific package
pip install --upgrade package-name
pip freeze | grep package-name >> requirements/base.txt

# Rebuild and test
./devctl rebuild
./devctl ci
```

### Security Audits

Dependencies are automatically scanned for vulnerabilities:
- **pip-audit** runs in CI (`security.yml` workflow)
- **Dependabot** opens PRs for updates
- **Trivy** scans Docker images

To manually check:
```bash
pip-audit -r requirements/base.txt
```

## Dependency Management Best Practices

1. **Always pin versions** (`package==1.2.3`, not `package>=1.2.3`)
2. **Test before committing** dependency changes
3. **Document breaking changes** in CHANGELOG.md
4. **Review security advisories** before upgrading
5. **Keep dependencies minimal** - only add what's necessary

## Troubleshooting

### Permission Denied When Installing
Use Docker workflow instead:
```bash
./devctl build
```

### Version Conflicts
Clear cache and reinstall:
```bash
pip cache purge
pip install --no-cache-dir -r requirements/base.txt
```

### Docker Image Size Too Large
Review dependencies and remove unused packages:
```bash
docker images monitoring-hub-dev:latest
```

## Related Files

- `config/docker/Dockerfile.dev` - Docker image definition
- `Makefile` - Installation targets (`make install`)
- `.github/workflows/` - CI dependency installation
