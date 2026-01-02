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
*   **Always Up-to-Date:** An automated Watcher opens PRs as soon as a new version is released upstream.

---

## 🛠️ Developer Guide: Adding an Exporter

Adding a new tool takes less than 5 minutes.

### 1. Create the Directory
```bash
mkdir -p exporters/my_exporter/assets
```

### 2. Create the `manifest.yaml`
Define your tool's identity and requirements using the full schema below:

```yaml
name: my_exporter
description: "Brief description of the tool"
version: "1.0.0" # Watcher will update this automatically

upstream:
  type: github
  repo: owner/repo
  # Optional: Custom archive pattern if upstream uses non-standard naming
  # Available vars: {name}, {version}, {clean_version}, {arch}, {rpm_arch}
  # archive_name: "{name}_{version}_{arch}.tar.gz" 

build:
  method: binary_repack
  binary_name: my_exporter
  extra_binaries: [tool_helper] # Optional: other binaries to include from the archive
  # Optional: Download external files not present in the release tarball
  extra_sources:
    - url: https://raw.githubusercontent.com/.../config.yml
      filename: config.yml
  # Optional: Restrict architectures if upstream doesn't support all
  # archs: [amd64] 

artifacts:
  rpm:
    enabled: true
    targets: [el8, el9, el10]
    system_user: my_user # Automates user/group creation
    # Install files (local assets or downloaded extra_sources)
    extra_files:
      - source: assets/config.yml
        dest: /etc/my_exporter/config.yml
        config: true # Protects from overwrite on update (%config(noreplace))
    # Create directories with permissions
    directories:
      - path: /var/lib/my_exporter
        owner: my_user
        group: my_user
        mode: "0755"

  docker:
    enabled: true
    # Default is UBI 9 Minimal, can be overridden but not recommended
    # base_image: registry.access.redhat.com/ubi9/ubi-minimal
    entrypoint: ["/usr/bin/my_exporter"]
    cmd: ["--config=/etc/my_exporter/config.yml"]
    # Port to check for automated smoke testing (metrics endpoint)
    smoke_test_port: 9100 
```

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

1. **Install Python dependencies:**
   ```bash
   pip install -r core/requirements.txt
   ```

2. **Generate build files:**
   This downloads the upstream binary and renders the `.spec` and `Dockerfile`.
   ```bash
   python core/builder.py --manifest exporters/node_exporter/manifest.yaml --arch amd64 --output-dir build/node_exporter
   ```

3. **Build the RPM:**
   Uses a containerized environment (AlmaLinux) to build the package.
   ```bash
   ./core/build_rpm.sh build/node_exporter/node_exporter.spec build/node_exporter/rpms
   ```

4. **Build the Docker Image:**
   ```bash
   docker build -t monitoring-hub/node_exporter:local build/node_exporter
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