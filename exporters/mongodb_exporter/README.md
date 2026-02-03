# Mongodb Exporter

![Build Status](https://img.shields.io/github/actions/workflow/status/SckyzO/monitoring-hub/release.yml?label=Build)
![Version](https://img.shields.io/github/v/release/percona/mongodb_exporter?label=Upstream)

> MongoDB exporter for Prometheus.

## 🚀 Installation

### RPM (Enterprise Linux)
```bash
sudo dnf config-manager --add-repo https://sckyzo.github.io/monitoring-hub/el9/$(arch)/
sudo dnf install mongodb_exporter
sudo systemctl enable --now mongodb_exporter
```

### Docker
```bash
docker pull ghcr.io/sckyzo/monitoring-hub/mongodb_exporter:latest
```

## ⚙️ Configuration

The exporter requires access to a MongoDB instance.

### Metrics
By default, it exposes metrics on port `9216`.

### Usage example
```bash
mongodb_exporter --mongodb.uri="mongodb://user:pass@localhost:27017"
```

See upstream documentation: [percona/mongodb_exporter](https://github.com/percona/mongodb_exporter)
