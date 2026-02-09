# Requirements

## For Using Exporters

### System Requirements

- **OS:** Enterprise Linux 8, 9, or 10 (RHEL, AlmaLinux, Rocky Linux, CentOS Stream)
- **Architecture:** x86_64 or aarch64 (ARM64)
- **Disk Space:** ~50MB per exporter
- **Memory:** Varies by exporter (typically 10-50MB)

### Runtime Requirements

- **systemd:** For managing services
- **Network:** Internet access for DNF repository (or local mirror)

## For Development

### Required Software

- **Python:** 3.9 or higher
- **Docker:** 20.10+ or Podman 3.0+
- **Git:** 2.0+

### Python Dependencies

Install via `requirements.txt`:

```bash
pip install -r requirements/base.txt
```

Dependencies include:

- `PyYAML` - YAML parsing
- `Jinja2` - Template rendering
- `marshmallow` - Schema validation
- `requests` - HTTP client
- `click` - CLI framework

### Development Dependencies

For running tests and linting:

```bash
pip install -r requirements/dev.txt
```

Includes:

- `pytest` - Testing framework
- `ruff` - Linting and formatting
- `mypy` - Type checking
- `pre-commit` - Git hooks

### Documentation Dependencies

For building docs locally:

```bash
pip install -r requirements/docs.txt
```

## For Building Exporters

### Build Environment

- **Docker/Podman:** Required for RPM builds
- **rpmbuild:** Containerized (no host installation needed)
- **Multi-arch:** Requires QEMU for cross-compilation (handled by Docker)

### Disk Space

- **Per build:** ~500MB temporary space
- **Cache:** ~2GB for Docker images

## Network Requirements

### For CI/CD

- Access to `github.com` (releases, API)
- Access to `ghcr.io` (container registry)
- Access to GitHub Pages (publishing)

### For Local Development

- Internet access for downloading upstream binaries
- Optional: GitHub CLI (`gh`) for enhanced features

## Optional Tools

- **gh CLI:** Enhanced GitHub integration
- **make:** For using Makefile commands
- **jq:** JSON processing in scripts
- **curl/wget:** Testing endpoints

## Browser Requirements (Portal)

- **Modern browsers:** Chrome 90+, Firefox 88+, Safari 14+
- **JavaScript:** Required
- **Responsive:** Works on mobile devices
