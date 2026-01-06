# Podman Exporter

![Build Status](https://img.shields.io/github/actions/workflow/status/SckyzO/monitoring-hub/release.yml?label=Build)
![Version](https://img.shields.io/github/v/release/SckyzO/prometheus-podman-exporter?label=Upstream)

> Prometheus exporter for Podman containers.

This exporter exposes metrics about Podman containers, images, and volumes by connecting to the Podman service socket.

## 🚀 Installation

### RPM (Enterprise Linux)
```bash
sudo dnf config-manager --add-repo https://sckyzo.github.io/monitoring-hub/el9/$(arch)/
sudo dnf install podman_exporter
sudo systemctl enable --now podman_exporter
```

### Docker
```bash
docker pull ghcr.io/sckyzo/monitoring-hub/podman_exporter:latest

# Requires access to the Podman socket
docker run -d \
  -p 9882:9882 \
  -v /run/podman/podman.sock:/run/podman/podman.sock \
  -e CONTAINER_HOST=unix:///run/podman/podman.sock \
  ghcr.io/sckyzo/monitoring-hub/podman_exporter:latest
```

## ⚙️ Configuration

The exporter connects to the Podman socket (default `unix:///run/podman/podman.sock`).

See upstream documentation: [SckyzO/prometheus-podman-exporter](https://github.com/SckyzO/prometheus-podman-exporter)