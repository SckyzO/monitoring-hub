# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.10.1] - 2026-01-01

### 🐛 Fixes
- **Ping Exporter:** Added default configuration file to fix startup crash and smoke test failure.
- **Slurm Exporter:** Fixed archive naming pattern to match upstream (using hyphens instead of dots).
- **SNMP Exporter:** Removed `snmp_generator` from extra binaries as it's not included in the release archive.
- **GPFS Exporter:** Skipped smoke test as it requires specific environment capabilities not available in CI.

## [0.10.0] - 2025-12-31

### 🚀 Features
- **Custom Archive Naming:** Added support for `archive_name` patterns in manifests.
- **Flexible Tagging:** Removed hardcoded 'v' prefix in engine URLs.
- **Improved Ping Monitoring:** Migrated `ping_exporter` to `czerwonk/ping_exporter`.

### 🐛 Fixes
- Resolved widespread 404 download errors.

## [0.9.0] - 2025-12-31

### 🚀 Features
- **External Assets Support:** Implemented `extra_sources` download.
- **Automated SNMP Configuration:** Auto-fetch latest `snmp.yml`.

## [0.8.0] - 2025-12-31

### 🚀 Features
- **Container Smoke Tests:** Automated verification of Docker images.
- **Portal UX Overhaul:** Dark Mode, Grid/List toggle, Docker Pull Widget.
- **Storage Optimization:** Reduced artifact retention to 1 day.

### 🐛 Fixes
- Fixed RPM build source indexing and bash syntax errors.

## [0.6.0] - 2025-12-31
- Advanced Customization Support (Local Template Overrides).

## [0.5.0] - 2025-12-31
- Web Portal V2, Reality-Check Engine, Search, and Multi-Arch documentation.

## [0.4.0] - 2025-12-31
- Parallel Matrix CI, Native Multi-Arch (aarch64), QEMU Integration.

## [0.3.0] - 2025-12-31
- Enterprise Hardening (UBI 9), Advanced RPM Packaging, Alertmanager.

## [0.2.0] - 2025-12-31
- The Watcher, RPM Factory, Prometheus Support.

## [0.1.0] - 2025-12-31
- Core Engine, Schema Validation, Docker Integration.
