# Keepalived Exporter

![Build Status](https://img.shields.io/github/actions/workflow/status/SckyzO/monitoring-hub/release.yml?label=Build)
![Version](https://img.shields.io/github/v/release/mehdy/keepalived-exporter?label=Upstream)

> Prometheus exporter for Keepalived metrics.

## 🚀 Installation

### RPM (Enterprise Linux)
```bash
sudo dnf config-manager --add-repo https://sckyzo.github.io/monitoring-hub/el9/$(arch)/
sudo dnf install keepalived_exporter
sudo systemctl enable --now keepalived_exporter
```

### Docker
```bash
docker pull ghcr.io/sckyzo/monitoring-hub/keepalived_exporter:latest
```

## ⚙️ Configuration

The exporter can scrape metrics from Keepalived running on the host or in a container.

### Metrics
By default, it exposes metrics on port `9165`.

See upstream documentation: [mehdy/keepalived-exporter](https://github.com/mehdy/keepalived-exporter)
