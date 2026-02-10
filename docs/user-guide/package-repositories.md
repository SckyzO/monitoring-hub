# Package Repositories

Monitoring Hub provides multiple distribution channels for installing exporters on different platforms.

## Distribution Overview

| Platform | Package Format | Distributions | Architectures |
|----------|---------------|---------------|---------------|
| Red Hat | RPM | EL8, EL9, EL10 | x86_64, aarch64 |
| Debian/Ubuntu | DEB | Ubuntu 22.04/24.04, Debian 12/13 | amd64, arm64 |
| Containers | OCI | All | amd64, arm64 |

## YUM Repository (RPM)

### Supported Distributions

- RHEL 8, 9, 10
- CentOS Stream 8, 9, 10
- AlmaLinux 8, 9, 10
- Rocky Linux 8, 9, 10

### Installation

```bash
# Add repository (replace el9 with your version)
sudo dnf config-manager --add-repo https://sckyzo.github.io/monitoring-hub/el9/$(arch)/

# Install exporter
sudo dnf install node_exporter

# Enable and start service
sudo systemctl enable --now node_exporter
```

### Repository Structure

```
https://sckyzo.github.io/monitoring-hub/
├── el8/
│   ├── x86_64/
│   │   ├── repodata/
│   │   └── *.rpm
│   └── aarch64/
├── el9/
│   ├── x86_64/
│   └── aarch64/
└── el10/
    ├── x86_64/
    └── aarch64/
```

### Manual RPM Installation

Download directly from GitHub Releases:

```bash
# Find the latest release
curl -s https://api.github.com/repos/SckyzO/monitoring-hub/releases | \
  jq -r '.[0].assets[] | select(.name | contains("node_exporter")) | .browser_download_url'

# Install directly
sudo dnf install https://github.com/SckyzO/monitoring-hub/releases/download/node_exporter-v1.8.0/node_exporter-1.8.0-1.el9.x86_64.rpm
```

## APT Repository (DEB)

### Supported Distributions

- Ubuntu 22.04 (Jammy Jellyfish)
- Ubuntu 24.04 (Noble Numbat)
- Debian 12 (Bookworm)
- Debian 13 (Trixie)

### Installation

#### 1. Add GPG Key

```bash
curl -fsSL https://sckyzo.github.io/monitoring-hub/apt/monitoring-hub.asc | \
  sudo gpg --dearmor -o /usr/share/keyrings/monitoring-hub.gpg
```

#### 2. Add Repository

Choose your distribution codename:

```bash
# Ubuntu 24.04 (Noble)
echo "deb [signed-by=/usr/share/keyrings/monitoring-hub.gpg] \
  https://sckyzo.github.io/monitoring-hub/apt noble main" | \
  sudo tee /etc/apt/sources.list.d/monitoring-hub.list

# Ubuntu 22.04 (Jammy)
echo "deb [signed-by=/usr/share/keyrings/monitoring-hub.gpg] \
  https://sckyzo.github.io/monitoring-hub/apt jammy main" | \
  sudo tee /etc/apt/sources.list.d/monitoring-hub.list

# Debian 13 (Trixie)
echo "deb [signed-by=/usr/share/keyrings/monitoring-hub.gpg] \
  https://sckyzo.github.io/monitoring-hub/apt trixie main" | \
  sudo tee /etc/apt/sources.list.d/monitoring-hub.list

# Debian 12 (Bookworm)
echo "deb [signed-by=/usr/share/keyrings/monitoring-hub.gpg] \
  https://sckyzo.github.io/monitoring-hub/apt bookworm main" | \
  sudo tee /etc/apt/sources.list.d/monitoring-hub.list
```

#### 3. Install Exporter

```bash
sudo apt update
sudo apt install node-exporter
sudo systemctl enable --now node-exporter
```

!!! warning "Package Naming Convention"
    DEB packages use dashes instead of underscores:

    - RPM: `node_exporter`
    - DEB: `node-exporter`

### Repository Structure

```
https://sckyzo.github.io/monitoring-hub/apt/
├── monitoring-hub.asc         # GPG public key
├── pool/main/                 # Package pool
│   ├── node-exporter_1.8.0_amd64.deb
│   └── blackbox-exporter_0.28.0_arm64.deb
└── dists/
    ├── jammy/                 # Ubuntu 22.04
    │   ├── InRelease
    │   ├── Release
    │   └── main/
    │       ├── binary-amd64/
    │       │   ├── Packages
    │       │   └── Packages.gz
    │       └── binary-arm64/
    ├── noble/                 # Ubuntu 24.04
    ├── bookworm/              # Debian 12
    └── trixie/                # Debian 13
```

### Manual DEB Installation

Download directly from GitHub Releases:

```bash
# Find the latest release
curl -s https://api.github.com/repos/SckyzO/monitoring-hub/releases | \
  jq -r '.[0].assets[] | select(.name | contains("node-exporter")) | .browser_download_url'

# Install directly
wget https://github.com/SckyzO/monitoring-hub/releases/download/node_exporter-v1.8.0/node-exporter_1.8.0-1_amd64.deb
sudo dpkg -i node-exporter_1.8.0-1_amd64.deb
sudo apt-get install -f  # Fix dependencies if needed
```

## Container Registry (OCI)

### Pull Image

```bash
# Latest version
docker pull ghcr.io/sckyzo/monitoring-hub/node_exporter:latest

# Specific version
docker pull ghcr.io/sckyzo/monitoring-hub/node_exporter:1.8.0

# Specific architecture
docker pull --platform linux/amd64 ghcr.io/sckyzo/monitoring-hub/node_exporter:latest
docker pull --platform linux/arm64 ghcr.io/sckyzo/monitoring-hub/node_exporter:latest
```

### Run Container

```bash
docker run -d \
  --name node_exporter \
  --restart unless-stopped \
  -p 9100:9100 \
  ghcr.io/sckyzo/monitoring-hub/node_exporter:latest
```

### Docker Compose

```yaml
version: '3.8'

services:
  node_exporter:
    image: ghcr.io/sckyzo/monitoring-hub/node_exporter:latest
    container_name: node_exporter
    restart: unless-stopped
    ports:
      - "9100:9100"
    networks:
      - monitoring

  blackbox_exporter:
    image: ghcr.io/sckyzo/monitoring-hub/blackbox_exporter:latest
    container_name: blackbox_exporter
    restart: unless-stopped
    ports:
      - "9115:9115"
    volumes:
      - ./blackbox.yml:/etc/blackbox_exporter/config.yml:ro
    networks:
      - monitoring

networks:
  monitoring:
    driver: bridge
```

### Multi-Arch Support

All container images are published as multi-arch manifests supporting both amd64 and arm64:

```bash
# Inspect manifest
docker manifest inspect ghcr.io/sckyzo/monitoring-hub/node_exporter:latest

# Docker automatically pulls the correct architecture
docker pull ghcr.io/sckyzo/monitoring-hub/node_exporter:latest
```

## Version Pinning

### RPM

```bash
# List available versions
dnf list --showduplicates node_exporter

# Install specific version
sudo dnf install node_exporter-1.8.0
```

### DEB

```bash
# List available versions
apt-cache madison node-exporter

# Install specific version
sudo apt install node-exporter=1.8.0-1
```

### Container

```bash
# Always use version tags in production
docker pull ghcr.io/sckyzo/monitoring-hub/node_exporter:1.8.0

# Avoid :latest in production
```

## Repository Metadata

All repositories are updated automatically on every release. The catalog is available at:

```
https://sckyzo.github.io/monitoring-hub/catalog.json
```

This JSON file contains:

- Exporter metadata (name, version, description)
- Package availability per distribution and architecture
- Build dates and statuses
- Download URLs

## Troubleshooting

### YUM: GPG Check Failed

```bash
# Temporarily disable GPG check
sudo dnf install --nogpgcheck node_exporter

# Or disable GPG check permanently (not recommended)
echo "gpgcheck=0" | sudo tee -a /etc/yum.repos.d/monitoring-hub.repo
```

### APT: GPG Error

```bash
# Re-add the GPG key
curl -fsSL https://sckyzo.github.io/monitoring-hub/apt/monitoring-hub.asc | \
  sudo gpg --dearmor -o /usr/share/keyrings/monitoring-hub.gpg

# Update package lists
sudo apt update
```

### Package Not Found

Check the [Portal](https://sckyzo.github.io/monitoring-hub/) to see if the package is available for your distribution and architecture.

### Container Pull Failed

```bash
# Check if you're authenticated (for private registries)
docker login ghcr.io

# Verify image exists
curl -s https://ghcr.io/v2/sckyzo/monitoring-hub/node_exporter/tags/list | jq
```

## Next Steps

- [Adding Exporters](adding-exporters.md) - Learn how to add new exporters
- [Manifest Reference](manifest-reference.md) - Understand the manifest schema
- [Troubleshooting](troubleshooting.md) - Common issues and solutions
