# Monitoring Hub 🏭

**A centralized factory for Prometheus Exporters.**

> **Status:** 🚧 Beta / Active Development

## 🎯 Goal

**Monitoring Hub** aims to be the definitive "Software Factory" for Prometheus Exporters.
While Prometheus is the standard for monitoring, installing and maintaining the vast ecosystem of exporters on bare-metal (RPM/DEB) or distinct architectures remains fragmented.

**Our goal is to treat Exporter packaging as Code.**
By defining *what* we want (a manifest), the system automatically handles the *how* (fetching, building, testing, publishing).

## 🚀 Features

*   **Automated Updates:** A "Watcher" system scans upstream repositories daily. If a new version is detected, it automatically creates a Pull Request to update the package.
*   **One Manifest, All Targets:** A single `manifest.yaml` configuration generates:
    *   📦 **RPM Packages** (EL8, EL9, EL10) with systemd integration.
    *   🐳 **Docker Images** (Multi-arch) published to GHCR.
*   **Public Repository:**
    *   **YUM/DNF Repo:** Hosted on GitHub Pages.
    *   **Container Registry:** Hosted on GitHub Container Registry (GHCR).

## 📦 Usage

### 1. Using RPM Packages (Rocky Linux / AlmaLinux / RHEL)

Add the repository (example for EL9):

```bash
# Add repository config
sudo cat <<EOF > /etc/yum.repos.d/monitoring-hub.repo
[monitoring-hub]
name=Monitoring Hub
baseurl=https://sckyzo.github.io/monitoring-hub/el9/x86_64/
enabled=1
gpgcheck=0
repo_gpgcheck=0
EOF

# Install an exporter
sudo dnf install node_exporter
```

### 2. Using Docker Images

Images are published to GHCR:

```bash
docker pull ghcr.io/sckyzo/monitoring-hub/node_exporter:latest
```

## 🛠️ Development

### Setup

```bash
# Clone repository
git clone https://github.com/SckyzO/monitoring-hub.git
cd monitoring-hub

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r core/requirements.txt
```

### Build an Exporter Manually

To generate the `.spec` file and `Dockerfile` locally:

```bash
python core/builder.py --manifest exporters/node_exporter/manifest.yaml --output-dir build/node_exporter
```

### Run the Watcher

Check for updates:

```bash
# Dry-run
python core/watcher.py

# Apply updates (modifies manifest.yaml)
python core/watcher.py --update
```

### Build RPM locally (requires Docker)

```bash
./core/build_rpm.sh build/node_exporter/node_exporter.spec build/node_exporter/rpms
```

## 📂 Architecture

- **`core/`**: The build engine (Python) & Jinja2 templates.
- **`exporters/`**: Source of truth. One folder per exporter containing `manifest.yaml`.
- **`.github/workflows/`**:
    - `scan-updates.yml`: Runs the Watcher daily.
    - `release.yml`: Builds and publishes artifacts on Push to Main.

## 🤝 Contributing

1.  Create a new folder in `exporters/<new_exporter_name>`.
2.  Add a `manifest.yaml` (copy `node_exporter` as a template).
3.  Open a Pull Request.