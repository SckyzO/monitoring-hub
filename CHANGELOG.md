# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.8.0] - 2025-12-31

### 🚀 Features
- **Container Smoke Tests:** Automated verification of Docker images during the CI pipeline.
    - Each container is automatically booted and its `/metrics` endpoint is verified via `curl`.
    - Customizable `smoke_test_port` in `manifest.yaml`.
    - Automatic cleanup after tests.

## [0.6.0] - 2025-12-31

### 🚀 Features
- **Advanced Customization Support:** Added the ability to override default build artifacts per exporter.
- **Local Template Overrides:** Exporters can now provide their own Jinja2 templates for RPM Specs and Dockerfiles in `exporters/<name>/templates/`.
    - Support for `<name>.spec.j2` and `Dockerfile.j2`.
    - Local templates take priority over global core templates while still receiving all dynamic variables.
- **Static File Overrides:** Initial support for custom `Dockerfile` detection.

## [0.5.0] - 2025-12-31

### 🚀 Features
- **Web Portal V2:** Complete redesign with a focus on User Experience.
- **Dark Mode:** Added native support for dark mode with local persistence.
- **Reality-Check Engine:** The portal now scans the physical repository storage to show only packages that were actually built successfully.
- **Compatibility Matrix:** Each exporter now features a Dist x Arch grid with direct download links.
- **Instant Search:** Added a real-time search bar to filter exporters by name or description.
- **Automated Directory Browsing:** Recursive generation of `index.html` files across the entire YUM repository to allow direct file navigation.

### 📚 Documentation
- Added **Developer Guide** to the README: "Add an exporter in 5 minutes".
- Updated Architecture, Vision, and Notes in the `ARCHITECTURE/` directory.

## [0.4.0] - 2025-12-31

### 🚀 Features
- **Parallel Matrix CI:** Refactored the release pipeline to use GitHub Actions Matrix for massive parallelism.
- **Native Multi-Arch (aarch64):** Full support for ARM64 (aarch64) builds across all targets.
- **QEMU Integration:** Implemented QEMU emulation for reliable cross-architecture RPM packaging.
- **Host-Side Extraction:** Optimized build speed and reliability by moving archive processing from emulated containers to the host.

### 🐛 Fixes
- Resolved `TarFile is closed` errors during parallel extraction.
- Fixed YAML indentation and syntax errors in complex Matrix workflows.

## [0.3.0] - 2025-12-31

### 🚀 Features
- **Enterprise Hardening:** Switched all base images to **Red Hat UBI 9 Minimal**.
- **Advanced RPM Packaging:** Added support for automated creation of system users, groups, and data directories (`/var/lib`).
- **Configuration Management:** Implemented the ability to include default configuration files (`/etc`) protected by `%config(noreplace)`.
- **New Exporter:** Added full support for **Alertmanager**.

### 🐛 Fixes
- Fixed RPM source indexing mismatch (`SOURCE1` vs `SOURCE2`).
- Aligned container entrypoints with standard Linux paths (`/usr/bin`).

## [0.2.0] - 2025-12-31

### 🚀 Features
- **The Watcher:** Implemented a daily bot that scans upstream GitHub releases and automatically opens PRs for updates.
- **The RPM Factory:** Established the first functional RPM build pipeline using AlmaLinux containers.
- **Automated Landing Page:** Initial version of the automated portal generator.
- **Prometheus Support:** Added the first server-side tool (Prometheus) to the factory.

### 🐛 Fixes
- Fixed Docker build context and command-line flag errors.
- Improved OCI metadata with proper OpenContainers labels.

## [0.1.0] - 2025-12-31

### 🚀 Features
- **Core Engine:** Initial release of the Python build engine and Jinja2 template system.
- **Schema Validation:** Implemented manifest validation using `marshmallow` to ensure data integrity.
- **Docker Integration:** First automated push to GitHub Container Registry (GHCR).
- **Proof of Concept:** Initial `node_exporter` manifest and build.