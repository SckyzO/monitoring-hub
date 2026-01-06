<div align="center">

# Monitoring Hub <img src="https://icongr.am/lucide/factory.svg?size=42&color=3b82f6" align="center">

**The definitive Software Factory for Prometheus Exporters.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge&logo=opensourceinitiative)](https://opensource.org/licenses/MIT)
[![Build Status](https://img.shields.io/github/actions/workflow/status/SckyzO/monitoring-hub/release.yml?branch=main&label=Factory%20Build&style=for-the-badge&logo=githubactions)](https://github.com/SckyzO/monitoring-hub/actions/workflows/release.yml)
[![Watcher](https://img.shields.io/github/actions/workflow/status/SckyzO/monitoring-hub/scan-updates.yml?branch=main&label=Watcher&style=for-the-badge&logo=github&color=blue)](https://github.com/SckyzO/monitoring-hub/actions/workflows/scan-updates.yml)

<br>

| <a href="https://sckyzo.github.io/monitoring-hub/"><img src="https://icongr.am/lucide/globe.svg?size=24&color=3b82f6"><br><b>Explore Portal</b></a> | <a href="https://github.com/SckyzO/monitoring-hub/packages"><img src="https://icongr.am/lucide/container.svg?size=24&color=f59e0b"><br><b>OCI Registry</b></a> | <a href="https://github.com/SckyzO/monitoring-hub/issues/new"><img src="https://icongr.am/lucide/bug.svg?size=24&color=f43f5e"><br><b>Report Bug</b></a> | <a href="CHANGELOG.md"><img src="https://icongr.am/lucide/history.svg?size=24&color=8b5cf6"><br><b>Changelog</b></a> |
| :---: | :---: | :---: | :---: |

</div>

---

## <img src="https://icongr.am/lucide/target.svg?size=24&color=10b981" vertical-align="middle"> Project Goal

**Monitoring Hub** is an automated Factory that transforms simple YAML manifests into production-ready monitoring tools. It focuses on **Enterprise Standards**, **Multi-Architecture support**, and **Full Automation**.

## <img src="https://icongr.am/lucide/rocket.svg?size=24&color=f59e0b" vertical-align="middle"> Key Features

*   **Native Multi-Arch:** Every tool is built for `x86_64` and `aarch64` (ARM64).
*   **Hardened Security:** All Docker images use **Red Hat UBI 9 Minimal**.
*   **Linux Standard (FHS):** RPMs include system users, standard paths (`/etc`, `/var/lib`), and systemd integration.
*   **Zero-Click Updates:** An automated Watcher opens PRs, triggers CI validation, and merges automatically when tests pass.
*   **Always Up-to-Date:** Never worry about upstream releases again.

---

## <img src="https://icongr.am/lucide/hammer.svg?size=24&color=ef4444" vertical-align="middle"> Developer Guide: Adding an Exporter

Adding a new tool takes less than 1 minute using our CLI tool.

### 1. Run the Creator Script
We provide a helper script to scaffold a new exporter following the [Reference Manifest](manifest.reference.yaml).

```bash
# Interactive mode
./core/scripts/create_exporter.py

# Or via arguments
./core/scripts/create_exporter.py --name my_exporter --repo owner/repo --category System
```

This will automatically:
- Create the directory structure (`exporters/my_exporter/`).
- Generate a clean `manifest.yaml`.
- Generate a standard `README.md`.

### 2. Customize `manifest.yaml`
Edit the generated file to match specific needs (binary names, config files).
See [manifest.reference.yaml](manifest.reference.yaml) for the full schema and all available options.

### 3. Add Optional Assets
Place any configuration files or scripts in the `assets/` folder and reference them in the manifest.

### 4. Template Overrides (Advanced)
If the default templates don't fit your needs, you can provide your own **Jinja2** templates. The engine will automatically detect these and use them instead of the global defaults while still providing all dynamic variables from the manifest.

- **Custom RPM Spec:** Place a template named `<exporter_name>.spec.j2` in `exporters/<exporter_name>/templates/`.
- **Custom Dockerfile:** Place a template named `Dockerfile.j2` in `exporters/<exporter_name>/templates/`.

### 5. Local Build Guide (Optional)
You can build RPMs and Docker images locally for testing or custom use.

#### Prerequisites
- **Python 3.9+**
- **Docker** (used for RPM isolation and image building)

#### Step-by-Step Example (node_exporter)

1. **Setup a Virtual Environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r core/requirements.txt
   ```

2. **Run the Test Script:**
   ```bash
   ./core/scripts/local_test.sh node_exporter
   ```

   *That's it!* Artifacts will be in `build/node_exporter/`.

---

## <img src="https://icongr.am/lucide/layers.svg?size=24&color=8b5cf6" vertical-align="middle"> Architecture

The "Magic" happens in the `core/` engine:
1.  **Smart Filter:** Compares local manifests against the deployed `catalog.json` (State Management).
2.  **Modular Engine (`core/engine/`):** **Builder**, **Schema**, **State Manager**.
3.  **Templater:** Uses **Jinja2** to render `.spec` files and `Dockerfiles`.
4.  **Publisher:** A parallelized Matrix CI builds all targets and updates the YUM repository.

## <img src="https://icongr.am/lucide/package.svg?size=24&color=06b6d4" vertical-align="middle"> Distribution

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

## <img src="https://icongr.am/lucide/users.svg?size=24&color=ec4899" vertical-align="middle"> Contributing

We welcome new exporters! Feel free to open a Pull Request following the guide above.

---

## <img src="https://icongr.am/lucide/scale.svg?size=24&color=64748b" vertical-align="middle"> License

Distributed under the MIT License. See `LICENSE` for more information.