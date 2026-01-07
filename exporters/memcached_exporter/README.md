# Memcached Exporter

![Build Status](https://img.shields.io/github/actions/workflow/status/SckyzO/monitoring-hub/release.yml?label=Build)
![Version](https://img.shields.io/github/v/release/prometheus/memcached_exporter?label=Upstream)

> Prometheus exporter for Memcached metrics.

## 🚀 Installation

### RPM (Enterprise Linux)
```bash
sudo dnf config-manager --add-repo https://sckyzo.github.io/monitoring-hub/el9/$(arch)/ 
sudo dnf install memcached_exporter
sudo systemctl enable --now memcached_exporter
```

### Docker
```bash
docker pull ghcr.io/sckyzo/monitoring-hub/memcached_exporter:latest
```

## ⚙️ Configuration

The exporter collects metrics from a Memcached server.

### Metrics
By default, it exposes metrics on port `9150`.

### Usage example
```bash
memcached_exporter --memcached.address="localhost:11211"
```

See upstream documentation: [prometheus/memcached_exporter](https://github.com/prometheus/memcached_exporter)
