# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.12.0] - 2026-01-02

### 🚀 Major Features
*   **Smart Incremental Build:** Introduced state management via `catalog.json` to only rebuild updated exporters, drastically reducing CI time.
*   **Podman Exporter:** Added support for `prometheus-podman-exporter` (v1.20.0) via custom upstream build.

### 🐛 Fixes & Improvements
*   **Documentation:** Updated Architecture, Vision, and Notes to reflect the new stateful build system.
*   **Core:** `gen_site.py` now exports a machine-readable `catalog.json`.
*   **CI:** Updated `release.yml` to use `smart_filter.py`.

## [0.11.0] - 2026-01-02

### 🚀 Features
- **New Exporter:** Added **podman_exporter** support.
    - Integrated via custom automated build upstream (SckyzO fork).
    - Custom Dockerfile with default `CONTAINER_HOST` socket path.
- **Flexible Image Validation:** Refactored the smoke test system into a more powerful `validation` schema.
    - Support for port-based HTTP checks.
    - Support for command-based validation (e.g., `--version`).
    - Ability to disable validation per exporter.
- **Local Build Utility:** Added `core/local_test.sh` to allow developers to test the full pipeline (Generation -> RPM -> Docker) locally before committing.

### 🐛 Fixes & Improvements
- **Schema Hardening:** Migrated all manifests to the new nested validation structure.
- **Documentation:** Updated local build guide and manifest schema references.

## [0.10.1] - 2026-01-01

### 🚀 Features
- **New Exporter:** Added full support for **eseries_exporter** (NetApp E-Series storage systems).
    - Automated user creation, default configuration and multi-arch builds.

### 🐛 Fixes & Improvements
- **Ping Exporter:** Added default configuration file to fix startup crash and smoke test failure.
- **Slurm Exporter:** Fixed archive naming pattern to match upstream (using hyphens instead of dots).
- **SNMP Exporter:** Removed `snmp_generator` from Docker extra binaries as it's not included in the release archive.
- **GPFS Exporter:** Disabled smoke test as it requires a specific environment not available in CI, preventing unnecessary build failures.
- **Core Engine:** Improved `builder.py` with architectural comments and docstrings.
- **Documentation:** Added developer guide and advanced features to `README.md`.

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
- **Portal UX Overhaul:** Dark Mode, Grid/List toggle, and improved Docker Pull widget.
- **Storage Optimization:** Reduced temporary build artifact retention to 1 day.

## [0.6.0] - 2025-12-31

### 🚀 Features
- **Advanced Customization Support:** Added the ability to override default build artifacts per exporter.
- **Local Template Overrides:** Exporters can now provide their own Jinja2 templates for RPM Specs and Dockerfiles.

## [0.5.0] - 2025-12-31

### 🚀 Features
- **Web Portal V2:** Complete redesign with "Reality-Check Engine" to only show successful builds.
- **Compatibility Matrix:** Per-exporter status grid (OS x Architecture) with direct download links.
- **Instant Search:** Added a real-time search bar to filter exporters.

## [0.4.0] - 2025-12-31

### 🚀 Features
- **Parallel Matrix CI:** Refactored the release pipeline for massive parallelism.
- **Native Multi-Arch (aarch64):** Full support for ARM64 builds via QEMU emulation.
- **Host-Side Extraction:** Resolved QEMU/EL10 extraction issues by moving archive processing to the host.

## [0.3.0] - 2025-12-31

### 🚀 Features
- **Enterprise Hardening:** Switched all base images to **Red Hat UBI 9 Minimal**.
- **Advanced RPM Packaging:** Added support for system users, groups, and data directories.
- **New Exporter:** Added full support for **Alertmanager**.

## [0.2.0] - 2025-12-31

### 🚀 Features
- **The Watcher:** Implemented a daily bot to scan for upstream updates.
- **The RPM Factory:** Established the first functional RPM build pipeline.
- **Prometheus Support:** Added the Prometheus server to the factory.

## [0.1.0] - 2025-12-31

### 🚀 Features
- **Core Engine:** Initial release of the Python build engine and Jinja2 template system.
- **Schema Validation:** Implemented manifest validation using `marshmallow`.
- **Docker Integration:** First automated push to GitHub Container Registry (GHCR).
- **Proof of Concept:** Initial `node_exporter` manifest and build.