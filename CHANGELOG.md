# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.10.0] - 2025-12-31

### 🚀 Features
- **Custom Archive Naming:** Added support for `archive_name` patterns in manifests to handle non-standard release filenames (e.g., `{name}_{version}_linux_{arch}.tar.gz`).
- **Flexible Tagging:** Removed hardcoded 'v' prefix in engine URLs, allowing exact tag specification in manifests.
- **Improved Ping Monitoring:** Migrated `ping_exporter` to `czerwonk/ping_exporter` with full pattern support and ARM64 compatibility.

### 🐛 Fixes
- Resolved widespread 404 download errors by aligning manifest versions with precise upstream tags.

## [0.9.0] - 2025-12-31

### 🚀 Features
- **External Assets Support:** Implemented `extra_sources` in the build engine to download additional files (like `snmp.yml`) directly during the build process.
- **Automated SNMP Configuration:** `snmp_exporter` now automatically includes the latest official MIB-mapped configuration from upstream.

## [0.8.0] - 2025-12-31

### 🚀 Features
- **Container Smoke Tests:** Automated verification of Docker images during the CI pipeline.
    - Each container is automatically booted and its `/metrics` endpoint is verified.
    - Customizable `smoke_test_port` in `manifest.yaml`.
- **Portal UX Overhaul:**
    - Integrated **Dark Mode** with native support and local persistence.
    - Added **Grid/List view toggle** with persistent user preference.
    - New **Docker Pull Widget** with multi-line display for better visibility and instant copy.
    - Harmonized Header/Footer with GitHub repository integration and FontAwesome branding.
    - Direct "Full Documentation" links for each exporter pointing to their specific README.
- **Storage Optimization:** Reduced temporary build artifact retention to **1 day** to optimize GitHub Actions storage usage.

### 🐛 Fixes
- Fixed RPM build source indexing mismatch (`SOURCE1` vs `SOURCE2`).
- Fixed Bash syntax errors in recursive directory indexing script.
- Improved CSS alignment for long exporter names.

## [0.6.0] - 2025-12-31

### 🚀 Features
- **Advanced Customization Support:** Added the ability to override default build artifacts per exporter.
- **Local Template Overrides:** Exporters can now provide their own Jinja2 templates for RPM Specs and Dockerfiles in `exporters/<name>/templates/`.
- **Static File Overrides:** Support for custom `Dockerfile` detection.

## [0.5.0] - 2025-12-31

### 🚀 Features
- **Web Portal V2:** Complete redesign with a focus on User Experience.
- **Reality-Check Engine:** The portal now scans the physical repository storage to show only packages that were actually built successfully.
- **Compatibility Matrix:** Each exporter features a Dist x Arch grid with direct download links.
- **Instant Search:** Added a real-time search bar to filter exporters by name or description.
- **Automated Directory Browsing:** Recursive generation of `index.html` files across the entire YUM repository.

## [0.4.0] - 2025-12-31

### 🚀 Features
- **Parallel Matrix CI:** Refactored the release pipeline to use GitHub Actions Matrix for massive parallelism.
- **Native Multi-Arch (aarch64):** Full support for ARM64 (aarch64) builds across all EL targets.
- **QEMU Integration:** Implemented QEMU emulation for reliable cross-architecture RPM packaging.
- **Host-Side Extraction:** Resolved QEMU/EL10 extraction issues by moving archive processing from emulated containers to the host.

## [0.3.0] - 2025-12-31

### 🚀 Features
- **Enterprise Hardening:** Switched all base images to **Red Hat UBI 9 Minimal**.
- **Advanced RPM Packaging:** Added support for automated creation of system users, groups, and data directories.
- **Configuration Management:** Implemented the ability to include default configuration files protected by `%config(noreplace)`.
- **New Exporter:** Added full support for **Alertmanager**.

## [0.2.0] - 2025-12-31

### 🚀 Features
- **The Watcher:** Implemented a daily bot that scans upstream GitHub releases and automatically opens PRs for updates.
- **The RPM Factory:** Established the first functional RPM build pipeline using AlmaLinux containers.
- **Prometheus Support:** Added the first server-side tool (Prometheus) to the factory.

## [0.1.0] - 2025-12-31

### 🚀 Features
- **Core Engine:** Initial release of the Python build engine and Jinja2 template system.
- **Schema Validation:** Implemented manifest validation using `marshmallow`.
- **Docker Integration:** First automated push to GitHub Container Registry (GHCR).