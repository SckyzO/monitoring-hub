# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-12-31

### 🚀 Features
- **Core Engine:**
    - Python-based build system with Jinja2 templating.
    - Manifest validation using `marshmallow`.
    - Support for "Binary Repack" build method.
- **Multi-Architecture:**
    - RPM builds for `x86_64` (amd64) and `aarch64` (arm64).
    - Architecture-aware download logic.
- **Exporters:**
    - **Node Exporter:** Full support (RPM/Docker).
    - **Prometheus:** Full support including user creation, config, and data dirs.
    - **Alertmanager:** Full support including user creation, config, and data dirs.
- **Distribution:**
    - Automated YUM repository generation on GitHub Pages.
    - Automated Website/Portal generation with Dark Mode.
    - Docker images published to GHCR.
- **Enterprise Grade:**
    - All Docker images based on Red Hat UBI 9 Minimal.
    - RPMs create system users and systemd services.
- **Automation:**
    - "Watcher" script to detect upstream updates and auto-patch manifests.
    - CI/CD pipelines via GitHub Actions.

### 🐛 Fixes
- Fixed Docker build context issues.
- Fixed RPM build path mapping in containers.
- Fixed `TarFile` closed error in builder.
- Fixed YAML indentation in release workflow.

### 📚 Documentation
- Added comprehensive Architecture documentation.
- Added Vision and Notes.
- Updated README with usage instructions.
