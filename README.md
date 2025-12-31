# Monitoring Hub 🏭

**A centralized factory for Prometheus Exporters.**

> **Note:** This project is currently under active development/refactoring.

## 🎯 Goal

This repository acts as a "Source of Truth" to automatically build, package, and publish Prometheus exporters.
Instead of maintaining manual build scripts for each tool, **Monitoring Hub** uses a configuration-driven approach to generate:

*   📦 **RPM Packages** (for Rocky Linux 8, 9, RHEL, CentOS)
*   🐳 **Docker Images** (Multi-arch x86_64/ARM64)

## 🚀 Key Features

*   **Automated Updates:** A "Watcher" system detects new upstream releases (GitHub Releases) and triggers builds automatically.
*   **Dual Output:** One configuration generates both native packages and container images.
*   **Configuration-as-Code:** Adding an exporter is as simple as creating a `manifest.yaml` file. No complex scripts required.
*   **Batteries Included:** (Planned) Optional inclusion of Grafana Dashboards and Prometheus Alerting rules.

## 📂 Repository Structure

*   `core/`: The build engine (Python scripts & Jinja2 templates) responsible for parsing manifests and generating build artifacts.
*   `exporters/`: The definitions of available exporters. Each subdirectory contains the `manifest.yaml` for a specific tool.
*   `artifacts/`: (CI generated) Location where RPMs and SRPMs are stored before publication.

## 🛠️ Usage

### Adding a new Exporter

1.  Create a folder in `exporters/<exporter_name>/`.
2.  Add a `manifest.yaml`:

```yaml
name: node_exporter
description: "Prometheus exporter for machine metrics"
upstream:
  type: github
  repo: prometheus/node_exporter
build:
  method: binary_repack
artifacts:
  rpm:
    enabled: true
  docker:
    enabled: true
```

3.  The CI pipeline handles the rest!

## 📦 Installation

### RPM (YUM/DNF)
*Coming soon via GitHub Pages hosting.*

```bash
dnf config-manager --add-repo https://.../monitoring-hub.repo
dnf install node_exporter
```

### Docker
*Coming soon via GHCR.*

```bash
docker pull ghcr.io/sckyzo/monitoring-hub/node_exporter:latest
```

## 📜 License

[MIT](LICENSE)

