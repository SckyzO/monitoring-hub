# Installation

Choose your preferred installation method based on your environment.

## Prerequisites

- **For YUM/DNF:** Enterprise Linux 8, 9, or 10 (RHEL, CentOS Stream, AlmaLinux, Rocky Linux)
- **For APT:** Ubuntu 22.04/24.04 or Debian 12/13
- **For Docker:** Docker or Podman installed
- **Architectures:** x86_64 (amd64) or aarch64 (arm64)

## YUM Repository

### Add GPG Key

First, import the repository GPG key to verify package signatures:

```bash
sudo rpm --import https://sckyzo.github.io/monitoring-hub/RPM-GPG-KEY-monitoring-hub
```

### Configure Repository

=== "EL9 (Recommended)"

    ```bash
    sudo dnf config-manager --add-repo https://sckyzo.github.io/monitoring-hub/el9/$(arch)/
    ```

=== "EL10"

    ```bash
    sudo dnf config-manager --add-repo https://sckyzo.github.io/monitoring-hub/el10/$(arch)/
    ```

=== "EL8"

    ```bash
    sudo dnf config-manager --add-repo https://sckyzo.github.io/monitoring-hub/el8/$(arch)/
    ```

### Install Exporter

```bash
# Install any exporter
sudo dnf install node_exporter

# Enable and start service
sudo systemctl enable --now node_exporter

# Check status
sudo systemctl status node_exporter
```

### List Available Packages

```bash
dnf search monitoring-hub
# or
dnf list available | grep exporter
```

## APT Repository

### Add GPG Key

First, add the repository GPG key to verify package signatures:

```bash
curl -fsSL https://sckyzo.github.io/monitoring-hub/apt/monitoring-hub.asc | \
  sudo gpg --dearmor -o /usr/share/keyrings/monitoring-hub.gpg
```

### Configure Repository

=== "Ubuntu 24.04 (Noble)"

    ```bash
    echo "deb [signed-by=/usr/share/keyrings/monitoring-hub.gpg] \
      https://sckyzo.github.io/monitoring-hub/apt noble main" | \
      sudo tee /etc/apt/sources.list.d/monitoring-hub.list
    ```

=== "Ubuntu 22.04 (Jammy)"

    ```bash
    echo "deb [signed-by=/usr/share/keyrings/monitoring-hub.gpg] \
      https://sckyzo.github.io/monitoring-hub/apt jammy main" | \
      sudo tee /etc/apt/sources.list.d/monitoring-hub.list
    ```

=== "Debian 13 (Trixie)"

    ```bash
    echo "deb [signed-by=/usr/share/keyrings/monitoring-hub.gpg] \
      https://sckyzo.github.io/monitoring-hub/apt trixie main" | \
      sudo tee /etc/apt/sources.list.d/monitoring-hub.list
    ```

=== "Debian 12 (Bookworm)"

    ```bash
    echo "deb [signed-by=/usr/share/keyrings/monitoring-hub.gpg] \
      https://sckyzo.github.io/monitoring-hub/apt bookworm main" | \
      sudo tee /etc/apt/sources.list.d/monitoring-hub.list
    ```

### Install Exporter

```bash
# Update package lists
sudo apt update

# Install any exporter
sudo apt install node-exporter

# Enable and start service
sudo systemctl enable --now node-exporter

# Check status
sudo systemctl status node-exporter
```

!!! note "Package Naming"
    DEB packages use dashes instead of underscores (e.g., `node-exporter` instead of `node_exporter`).

### List Available Packages

```bash
apt-cache search monitoring-hub
# or
apt list | grep exporter
```

## Docker / Podman

### Pull Image

```bash
# Using Docker
docker pull ghcr.io/sckyzo/monitoring-hub/node_exporter:latest

# Using Podman
podman pull ghcr.io/sckyzo/monitoring-hub/node_exporter:latest
```

### Run Container

```bash
docker run -d \
  --name node_exporter \
  -p 9100:9100 \
  --restart unless-stopped \
  ghcr.io/sckyzo/monitoring-hub/node_exporter:latest
```

### Docker Compose

```yaml
version: '3.8'

services:
  node_exporter:
    image: ghcr.io/sckyzo/monitoring-hub/node_exporter:latest
    container_name: node_exporter
    ports:
      - "9100:9100"
    restart: unless-stopped
```

## Verification

Test that the exporter is running:

```bash
# Check metrics endpoint
curl http://localhost:9100/metrics

# Or
wget -qO- http://localhost:9100/metrics
```

You should see Prometheus metrics output.

## Next Steps

- [Quick Start Guide](quick-start.md) - Get started with your first exporter
- [User Guide](../user-guide/adding-exporters.md) - Learn how to add exporters
- [Troubleshooting](../user-guide/troubleshooting.md) - Common issues and solutions
