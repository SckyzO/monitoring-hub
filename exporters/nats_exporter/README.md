# Nats Exporter

![Build Status](https://img.shields.io/github/actions/workflow/status/SckyzO/monitoring-hub/release.yml?label=Build)
![Version](https://img.shields.io/github/v/release/nats-io/prometheus-nats-exporter?label=Upstream)

> NATS metrics exporter for Prometheus.

## 🚀 Installation

### RPM (Enterprise Linux)
```bash
sudo dnf config-manager --add-repo https://sckyzo.github.io/monitoring-hub/el9/$(arch)/
sudo dnf install nats_exporter
sudo systemctl enable --now nats_exporter
```

### Docker
```bash
docker pull ghcr.io/sckyzo/monitoring-hub/nats_exporter:latest
```

## ⚙️ Configuration

The exporter aggregates metrics from NATS server monitoring endpoints.

### Metrics
By default, it exposes metrics on port `7777`.

### Usage example
```bash
prometheus-nats-exporter -varz "http://localhost:8222"
```

See upstream documentation: [nats-io/prometheus-nats-exporter](https://github.com/nats-io/prometheus-nats-exporter)
