# Monitoring Hub 🏭

**The definitive Software Factory for Prometheus Exporters.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build and Publish](https://github.com/SckyzO/monitoring-hub/actions/workflows/release.yml/badge.svg)](https://github.com/SckyzO/monitoring-hub/actions/workflows/release.yml)
[![Watcher - Scan Updates](https://github.com/SckyzO/monitoring-hub/actions/workflows/scan-updates.yml/badge.svg)](https://github.com/SckyzO/monitoring-hub/actions/workflows/scan-updates.yml)

---

### 🔗 Quick Links

| Resource | Description | URL |
| :--- | :--- | :--- |
| **🌐 Web Portal** | Browser, Installation Guide, Dark Mode | [**sckyzo.github.io/monitoring-hub**](https://sckyzo.github.io/monitoring-hub/) |
| **📦 YUM Repo** | Direct file access (EL9/x86_64) | [**.../el9/x86_64/**](https://sckyzo.github.io/monitoring-hub/el9/x86_64/) |
| **🐳 Docker Images** | GitHub Container Registry | [**ghcr.io/sckyzo/monitoring-hub**](https://github.com/SckyzO/monitoring-hub/pkgs/container/monitoring-hub%2Fnode_exporter) |
| **🐛 Issues** | Report bugs or request exporters | [**GitHub Issues**](https://github.com/SckyzO/monitoring-hub/issues) |

---

## 🎯 Project Goal

**Monitoring Hub** is an automated "Software Factory" designed to package Prometheus exporters and monitoring tools with a focus on enterprise-grade standards.

By defining an exporter's intent in a simple `manifest.yaml`, the system automatically handles:
- 🛠️ **Building:** Cross-architecture support (x86_64, aarch64).
- 📦 **Packaging:** Professional RPMs (EL8, EL9, EL10) and Docker Images.
- 🚀 **Publishing:** Automated YUM repository and Container Registry.
- 🤖 **Updating:** Daily scans for new upstream releases.

## 🚀 Key Features

*   **Multi-Arch by Design:** Native support for `x86_64` and `aarch64` (ARM64) for all RPM packages.
*   **Enterprise Security:** All Docker images are based on **Red Hat Universal Base Image (UBI 9 Minimal)**.
*   **Full Automation:** A "Watcher" bot detects new versions and opens PRs automatically.
*   **Production Ready:** Packages include dedicated system users, configuration files, and systemd units.
*   **Modern Portal:** Browse our exporters on our [Automated Portal](https://sckyzo.github.io/monitoring-hub/) with built-in Dark Mode.

## 📦 Usage

### 1. Using RPM Packages (Alma/Rocky/RHEL)

Add the repository for your architecture and OS version:

```bash
# Example for EL9 on x86_64
sudo dnf config-manager --add-repo https://sckyzo.github.io/monitoring-hub/el9/x86_64/
sudo dnf install node_exporter
```

Browse all available packages at: [sckyzo.github.io/monitoring-hub/](https://sckyzo.github.io/monitoring-hub/)

### 2. Using Docker Images

Images are published to **GHCR** and are linked to this repository:

```bash
docker pull ghcr.io/sckyzo/monitoring-hub/node_exporter:latest
```

## 🛠️ Development & Contributing

### Adding a new Exporter

Adding a tool is as simple as creating a folder in `exporters/` with a `manifest.yaml`:

```yaml
name: my_exporter
description: "My awesome exporter"
version: "1.0.0"
upstream:
  type: github
  repo: owner/my_exporter
build:
  method: binary_repack
  binary_name: my_exporter
artifacts:
  rpm:
    enabled: true
    system_user: my_user
  docker:
    enabled: true
```

### Local Build

```bash
# Setup
python3 -m venv .venv && source .venv/bin/activate
pip install -r core/requirements.txt

# Build (generates spec, dockerfile and downloads binary)
python core/builder.py --manifest exporters/node_exporter/manifest.yaml --arch amd64
```

## 📂 Repository Structure

- **`core/`**: The Python engine, Jinja2 templates, and build scripts.
- **`exporters/`**: Manifests and custom assets for each tool.
- **`ARCHITECTURE/`**: Detailed design documents and roadmap.

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.