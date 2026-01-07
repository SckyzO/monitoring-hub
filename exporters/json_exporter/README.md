# Json Exporter

![Build Status](https://img.shields.io/github/actions/workflow/status/SckyzO/monitoring-hub/release.yml?label=Build)
![Version](https://img.shields.io/github/v/release/prometheus-community/json_exporter?label=Upstream)

> A prometheus exporter which scrapes remote JSON by JSONPath.

## 🚀 Installation

### RPM (Enterprise Linux)
```bash
sudo dnf config-manager --add-repo https://sckyzo.github.io/monitoring-hub/el9/$(arch)/ 
sudo dnf install json_exporter
sudo systemctl enable --now json_exporter
```

### Docker
```bash
docker pull ghcr.io/sckyzo/monitoring-hub/json_exporter:latest
```

## ⚙️ Configuration

The exporter requires a configuration file to define how to parse the JSON data.

### Metrics
By default, it exposes metrics on port `7979`.

### Usage example
```bash
json_exporter --config.file config.yml
```

See upstream documentation: [prometheus-community/json_exporter](https://github.com/prometheus-community/json_exporter)
