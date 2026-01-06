# Monitoring Hub 🕸️

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
*   **Zero-Click Updates:** An automated Watcher opens PRs, triggers CI validation, and merges automatically when tests pass.
*   **Always Up-to-Date:** Never worry about upstream releases again.

---

## 🛠️ Developer Guide: Adding an Exporter

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

This allows for complex packaging logic (e.g., custom `%post` scripts in RPM or multi-stage builds in Docker) while keeping the benefit of automated versioning.

#### Example: Custom Dockerfile
To install extra packages in your container, create `exporters/my_exporter/templates/Dockerfile.j2`:

```dockerfile
FROM {{ artifacts.docker.base_image }}

# Custom logic: Install specific tools
RUN microdnf install -y curl && microdnf clean all

# Standard logic (using variables from manifest)
COPY {{ build.binary_name }} /usr/bin/{{ name }}
ENTRYPOINT {{ artifacts.docker.entrypoint | tojson }}
```

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
   We provide a helper script to automate generation, RPM build, and Docker build in one go.
   ```bash
   # Usage: ./core/scripts/local_test.sh <exporter> [arch] [distro] [--smoke]
   ./core/scripts/local_test.sh node_exporter
   ```

   *That's it!* Artifacts will be in `build/node_exporter/`.

#### Manual Build (Advanced)
If you need to debug a specific step:

1. **Generate build files:**
   ```bash
   export PYTHONPATH=$(pwd)
   python3 -m core.engine.builder --manifest exporters/node_exporter/manifest.yaml --arch amd64 --output-dir build/node_exporter
   ```

2. **Build the RPM:**
   ```bash
   ./core/scripts/build_rpm.sh build/node_exporter/node_exporter.spec build/node_exporter/rpms amd64 almalinux:9
   ```

3. **Build the Docker Image:**
   ```bash
   docker build -t monitoring-hub/node_exporter:local build/node_exporter
   ```

---

## 🏗️ Architecture

The "Magic" happens in the `core/` engine:
1.  **Smart Filter:** Compares local manifests against the deployed `catalog.json` (State Management) to only rebuild what changed.
2.  **Modular Engine (`core/engine/`):**
    *   **Builder:** Downloads binaries and orchestrates the build.
    *   **Schema:** Validates YAML manifests (`marshmallow`).
    *   **State Manager:** Handles the incremental build logic.
3.  **Templater:** Uses **Jinja2** (with auto-escape enabled) to render `.spec` files and `Dockerfiles`.
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