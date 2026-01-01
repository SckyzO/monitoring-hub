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
| **🐳 Docker Hub** | Container Registry (GHCR) | [**Packages List**](https://github.com/SckyzO/monitoring-hub/packages) |
| **📜 Changelog** | Version history and updates | [**CHANGELOG.md**](CHANGELOG.md) |

---

## 🎯 Project Goal

**Monitoring Hub** is an automated Factory that transforms simple YAML manifests into production-ready monitoring tools. It focuses on **Enterprise Standards**, **Multi-Architecture support**, and **Full Automation**.

## 🚀 Key Features

*   **Native Multi-Arch:** Every tool is built for `x86_64` and `aarch64` (ARM64).
*   **Hardened Security:** All Docker images use **Red Hat UBI 9 Minimal**.
*   **Linux Standard (FHS):** RPMs include system users, standard paths (`/etc`, `/var/lib`), and systemd integration.
*   **Always Up-to-Date:** An automated Watcher opens PRs as soon as a new version is released upstream.

---

## 🛠️ Developer Guide: Adding an Exporter

Adding a new tool takes less than 5 minutes.

### 1. Create the Directory
```bash
mkdir -p exporters/my_exporter/assets
```

### 2. Create the `manifest.yaml`
Define your tool's identity and requirements:

```yaml
name: my_exporter
description: "Brief description of the tool"
version: "1.0.0" # Watcher will update this automatically
upstream:
  type: github
  repo: owner/repo
build:
  method: binary_repack
  binary_name: my_exporter
  extra_binaries: [tool_helper] # Optional
artifacts:
  rpm:
    enabled: true
    targets: [el8, el9, el10]
    system_user: my_user # Automates user/group creation
    extra_files:
      - source: assets/config.yml
        dest: /etc/my_exporter/config.yml
        config: true # Protects from overwrite on update
  docker:
    enabled: true
    entrypoint: ["/usr/bin/my_exporter"]
    cmd: ["--config=/etc/my_exporter/config.yml"]
```

### 3. Add Optional Assets
Place any configuration files or scripts in the `assets/` folder and reference them in the manifest.

### 4. Local Validation (Optional)
```bash
# Generate build files
python core/builder.py --manifest exporters/my_exporter/manifest.yaml --arch amd64
```

---

## 🏗️ Architecture

The "Magic" happens in the `core/` engine:
1.  **Parser:** Reads the YAML and validates it against a strict schema (`marshmallow`).
2.  **Fetcher:** Downloads the correct architecture-specific binary from GitHub.
3.  **Templater:** Uses **Jinja2** to render professional `.spec` files and `Dockerfiles`.
4.  **Publisher:** A parallelized Matrix CI builds all targets and updates the YUM repository.

## 📦 Distribution

### YUM Repository (RPM)
```bash
# Example for EL9
sudo dnf config-manager --add-repo https://sckyzo.github.io/monitoring-hub/el9/$(arch)/
sudo dnf install <exporter_name>
```

### Container Registry (Docker)
```bash
docker pull ghcr.io/sckyzo/monitoring-hub/<exporter_name>:latest
```

## 🤝 Contributing

We welcome new exporters! Feel free to open a Pull Request following the guide above.

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.
