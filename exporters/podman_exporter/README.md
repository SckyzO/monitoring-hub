# Podman Exporter

[![Upstream](https://img.shields.io/badge/Upstream-SckyzO/prometheus--podman--exporter-blue)](https://github.com/SckyzO/prometheus-podman-exporter)

Prometheus exporter for Podman containers.

## Overview
This exporter exposes metrics about Podman containers, images, and volumes. It connects to the Podman socket to gather information.

## Configuration
The exporter connects to the Podman socket (default `unix:///run/podman/podman.sock`).

### Common Flags
*   `--collector.enable-all`: Enable all available collectors.
*   `--web.listen-address`: Address to listen on (default `:9882`).

## Usage

### RPM
```bash
sudo dnf install podman_exporter
sudo systemctl enable --now podman_exporter
```

### Docker
To monitor the host's Podman instance from a container, you must mount the Podman socket.

```bash
docker run -d -p 9882:9882 \
  -v /run/podman/podman.sock:/run/podman/podman.sock \
  -e CONTAINER_HOST=unix:///run/podman/podman.sock \
  ghcr.io/sckyzo/monitoring-hub/podman_exporter:latest
```
