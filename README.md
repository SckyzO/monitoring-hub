<div align="center">

# Monitoring Hub <img src=".github/icons/factory-blue.svg" width="45" height="45" style="vertical-align: middle; margin-bottom: 8px;">

**The definitive Software Factory for Prometheus Exporters.**

<p align="center">
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-fbbf24?style=flat-square&labelColor=18181b&logo=opensourceinitiative&logoColor=white" alt="MIT License"></a>
  <a href="https://github.com/SckyzO/monitoring-hub/actions/workflows/release.yml"><img src="https://img.shields.io/github/actions/workflow/status/SckyzO/monitoring-hub/release.yml?branch=main&style=flat-square&labelColor=18181b&logo=githubactions&logoColor=white&label=Release%20Pipeline" alt="Release Pipeline"></a>
  <a href="https://github.com/SckyzO/monitoring-hub/actions/workflows/auto-release.yml"><img src="https://img.shields.io/github/actions/workflow/status/SckyzO/monitoring-hub/auto-release.yml?branch=main&style=flat-square&labelColor=18181b&logo=githubactions&logoColor=white&label=Auto%20Release&color=f59e0b" alt="Auto Release"></a>
  <a href="https://github.com/SckyzO/monitoring-hub/actions/workflows/build-pr.yml"><img src="https://img.shields.io/github/actions/workflow/status/SckyzO/monitoring-hub/build-pr.yml?branch=main&style=flat-square&labelColor=18181b&logo=githubactions&logoColor=white&label=PR%20Validation&color=3b82f6" alt="PR Validation"></a>
  <a href="https://github.com/SckyzO/monitoring-hub/actions/workflows/security.yml"><img src="https://img.shields.io/github/actions/workflow/status/SckyzO/monitoring-hub/security.yml?branch=main&style=flat-square&labelColor=18181b&logo=trivy&logoColor=white&label=Security%20Scan&color=10b981" alt="Security Scan"></a>
  <a href="https://github.com/SckyzO/monitoring-hub/actions/workflows/scan-updates.yml"><img src="https://img.shields.io/github/actions/workflow/status/SckyzO/monitoring-hub/scan-updates.yml?branch=main&style=flat-square&labelColor=18181b&logo=dependabot&logoColor=white&label=Version%20Watcher&color=8b5cf6" alt="Version Watcher"></a>
  <a href="https://sckyzo.github.io/monitoring-hub/docs/"><img src="https://img.shields.io/badge/Docs-MkDocs-06b6d4?style=flat-square&labelColor=18181b&logo=materialformkdocs&logoColor=white" alt="Documentation"></a>
  <img src="https://img.shields.io/badge/RPM-Signed-ef4444?style=flat-square&labelColor=18181b&logo=redhat&logoColor=white" alt="RPM Signed">
  <img src="https://img.shields.io/badge/DEB-Signed-ef4444?style=flat-square&labelColor=18181b&logo=debian&logoColor=white" alt="DEB Signed">
  <img src="https://img.shields.io/badge/Multi--Arch-x86__64%20%7C%20ARM64-6366f1?style=flat-square&labelColor=18181b&logo=arm&logoColor=white" alt="Multi-Architecture">
  <img src="https://img.shields.io/badge/Containers-UBI9%20Minimal-ec4899?style=flat-square&labelColor=18181b&logo=redhat&logoColor=white" alt="UBI9 Minimal">
  <img src="https://img.shields.io/badge/Code%20Quality-Ruff%20%7C%20Mypy%20%7C%20Yamllint-22c55e?style=flat-square&labelColor=18181b&logo=python&logoColor=white" alt="Code Quality">
  <img src="https://img.shields.io/badge/Security-Trivy%20%7C%20Bandit%20%7C%20pip--audit-dc2626?style=flat-square&labelColor=18181b&logo=trivy&logoColor=white" alt="Security Tools">
</p>

---

<table align="center" width="90%">
<tr>
<td align="center" style="vertical-align: top;">
<a href="https://sckyzo.github.io/monitoring-hub/">
<img src=".github/icons/globe-blue.svg" width="64" height="64">
<br><br>
<b>Catalog</b>
<br><br>
<sub>Browse all exporters</sub>
</a>
</td>
<td align="center" style="vertical-align: top;">
<a href="https://sckyzo.github.io/monitoring-hub/docs/">
<img src=".github/icons/book-emerald.svg" width="64" height="64">
<br><br>
<b>Documentation</b>
<br><br>
<sub>User guides & API</sub>
</a>
</td>
<td align="center" style="vertical-align: top;">
<a href="https://github.com/SckyzO/monitoring-hub/packages">
<img src=".github/icons/container-amber.svg" width="64" height="64">
<br><br>
<b>Registry</b>
<br><br>
<sub>Container images</sub>
</a>
</td>
<td align="center" style="vertical-align: top;">
<a href="https://github.com/SckyzO/monitoring-hub/issues/new">
<img src=".github/icons/bug-rose.svg" width="64" height="64">
<br><br>
<b>Issues</b>
<br><br>
<sub>Report bugs</sub>
</a>
</td>
<td align="center" style="vertical-align: top;">
<a href="CHANGELOG.md">
<img src=".github/icons/history-purple.svg" width="64" height="64">
<br><br>
<b>Changelog</b>
<br><br>
<sub>Release notes</sub>
</a>
</td>
</tr>
</table>

</div>

---

## <img src=".github/icons/target-emerald.svg" width="24" height="24" style="vertical-align: bottom;"> Project Goal

**Monitoring Hub** is an automated Software Factory that transforms simple YAML manifests into production-ready monitoring tools. It focuses on **Enterprise Standards**, **Multi-Architecture support**, **GPG Security**, and **Full Automation**.

## <img src=".github/icons/rocket-amber.svg" width="24" height="24" style="vertical-align: bottom;"> Key Features

*   **Native Multi-Arch:** Every tool is built for `x86_64` and `aarch64` (ARM64).
*   **Multi-Format Packages:** RPM (RHEL/CentOS/Rocky/Alma), DEB (Ubuntu/Debian), and OCI containers.
*   **GPG-Signed Packages:** All RPM and DEB packages are cryptographically signed for integrity verification.
*   **Security-First:** Container images scanned with Trivy, Python code with Bandit, dependencies with pip-audit.
*   **Hardened Containers:** All Docker images use Red Hat UBI 9 Minimal base.
*   **Linux Standards (FHS):** Packages include system users, standard paths (`/etc`, `/var/lib`), and systemd integration.
*   **Zero-Touch Automation:** Version watcher opens PRs, triggers CI validation, and auto-merges when tests pass.
*   **Always Up-to-Date:** Never worry about upstream releases again.

---

## <img src=".github/icons/hammer-red.svg" width="24" height="24" style="vertical-align: bottom;"> Developer Guide: Adding an Exporter

Adding a new tool takes less than 1 minute using our Docker-first CLI tool.

### Prerequisites

- **Docker** - The only requirement! No Python installation needed.

### 1. Run the Creator Script

We provide `./devctl` - a unified Docker-first CLI for all development tasks:

```bash
# Interactive mode (recommended)
./devctl create-exporter

# Or specify name and repository
./devctl create-exporter my_exporter --repo owner/repo --category System
```

This will automatically:
- Create the directory structure (`exporters/my_exporter/`).
- Generate a clean `manifest.yaml`.
- Generate a standard `README.md`.

**Alternative:** If you prefer using Make:
```bash
make create-exporter
```

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

### 5. Local Testing (Docker-First Workflow)

Test your exporter locally using our Docker-based development environment:

#### Quick Test (Recommended)
```bash
# Test build an exporter (generates artifacts + builds RPM + Docker image)
./devctl test-exporter node_exporter

# Test with specific options
./devctl test-exporter node_exporter --arch arm64 --el10
```

**Or using Make:**
```bash
make test-exporter EXPORTER=node_exporter
```

#### Individual Build Steps

**Build artifacts only:**
```bash
./devctl build-exporter node_exporter
# Output: build/node_exporter/
```

**List all available exporters:**
```bash
./devctl list-exporters
```

#### Advanced: Local Python Development

If you need to debug or develop the core engine locally:

```bash
# Install dependencies locally
make install

# Run tests locally
make local-test

# Run linter locally
make local-lint
```

**Note:** For most development tasks, the Docker workflow (`./devctl`) is recommended as it requires no Python installation and ensures consistency.

### 6. Custom/Proprietary Binaries

For proprietary or custom exporters not available on GitHub:

```bash
# Create exporter directory structure
mkdir -p exporters/my_exporter/assets

# Place your binary in the assets directory
cp /path/to/my_exporter exporters/my_exporter/assets/
chmod +x exporters/my_exporter/assets/my_exporter

# Create manifest interactively
./devctl create-exporter
```

Edit the generated `manifest.yaml` to use local binary:
```yaml
upstream:
  type: local
  local_binary: assets/my_exporter
```

Build and test:
```bash
./devctl test-exporter my_exporter
```

**Note:** Local sources are not tracked by the automatic version watcher. Update the `version` field manually when your binary changes.

---

## <img src=".github/icons/layers-purple.svg" width="24" height="24" style="vertical-align: bottom;"> Architecture

### Project Structure

```
monitoring-hub/
├── config/              # Configuration files (Docker, linting, Python, docs)
├── requirements/        # Python dependencies (base, dev, docs)
├── scripts/             # Utility scripts
├── core/                # Core engine (builder, schema, templates, tests)
├── exporters/           # Exporter manifests (one per directory)
├── docs/                # MkDocs documentation
├── devctl               # Docker-first development CLI
├── Makefile             # Make commands (aliases to devctl)
└── manifest.reference.yaml  # Manifest schema reference
```

See [config/README.md](config/README.md) and [requirements/README.md](requirements/README.md) for detailed documentation.

### How It Works

The "Magic" happens in the `core/` engine:
1.  **Smart Filter:** Compares local manifests against the deployed `catalog.json` (State Management) to only rebuild what changed.
2.  **Modular Engine (`core/engine/`):**
    *   **Builder:** Downloads binaries and orchestrates the build.
    *   **Schema:** Validates YAML manifests (`marshmallow`).
    *   **State Manager:** Handles the incremental build logic.
3.  **Templater:** Uses **Jinja2** (with auto-escape enabled) to render `.spec` files and `Dockerfiles`.
4.  **Publisher:** A parallelized Matrix CI builds all targets and updates the YUM repository.

## <img src=".github/icons/package-cyan.svg" width="24" height="24" style="vertical-align: bottom;"> Distribution

### YUM Repository (RPM)
```bash
# RHEL/CentOS/Rocky/Alma 8, 9, 10
sudo rpm --import https://sckyzo.github.io/monitoring-hub/RPM-GPG-KEY-monitoring-hub
sudo dnf config-manager --add-repo https://sckyzo.github.io/monitoring-hub/el9/$(arch)/
sudo dnf install <exporter_name>
```

### APT Repository (DEB)
```bash
# Ubuntu 22.04/24.04, Debian 12/13
curl -fsSL https://sckyzo.github.io/monitoring-hub/apt/monitoring-hub.asc | \
  sudo gpg --dearmor -o /usr/share/keyrings/monitoring-hub.gpg

echo "deb [signed-by=/usr/share/keyrings/monitoring-hub.gpg] \
  https://sckyzo.github.io/monitoring-hub/apt jammy main" | \
  sudo tee /etc/apt/sources.list.d/monitoring-hub.list

sudo apt update && sudo apt install <exporter_name>
```

### Container Registry (OCI)
```bash
docker pull ghcr.io/sckyzo/monitoring-hub/<exporter_name>:latest
```

## <img src=".github/icons/users-pink.svg" width="24" height="24" style="vertical-align: bottom;"> Contributing

We welcome new exporters! Feel free to open a Pull Request following the guide above.

---

## 🔒 Security

Monitoring Hub takes security seriously. We implement multiple layers of protection:

### Security Measures

- **Code Scanning**: Automated Bandit security scanner on all PRs
- **Dependency Scanning**: pip-audit and Dependabot for vulnerability detection
- **Container Scanning**: Trivy scans all container images with SARIF upload to GitHub Security
- **YAML Validation**: yamllint ensures configuration file integrity
- **Network Security**: All HTTP requests include timeouts and exponential backoff retry logic
- **SSL/TLS Resilience**: Automatic retry on SSL errors and connection failures
- **Template Security**: Jinja2 templates use autoescape to prevent injection attacks
- **Input Validation**: Strict manifest schema validation with marshmallow
- **Package Signing**: GPG-signed RPM and DEB packages for integrity verification

### Reporting Vulnerabilities

If you discover a security vulnerability, please follow our [Security Policy](SECURITY.md) for responsible disclosure. **Do not open public issues for security vulnerabilities.**

For more details, see:
- [SECURITY.md](SECURITY.md) - Vulnerability reporting process
- [Security Guidelines](docs/contributing/security.md) - Development security best practices

---

## <img src=".github/icons/scale-slate.svg" width="24" height="24" style="vertical-align: bottom;"> License

Distributed under the MIT License. See `LICENSE` for more information.
