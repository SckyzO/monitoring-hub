# E-Series Exporter

![Build Status](https://img.shields.io/github/actions/workflow/status/SckyzO/monitoring-hub/release.yml?label=Build)
![Version](https://img.shields.io/github/v/release/sckyzo/eseries_exporter?label=Upstream)

> Prometheus exporter for NetApp/Lenovo E-Series storage systems.

This exporter collects metrics from E-Series storage arrays via their REST API (Web Services Proxy).

## 🚀 Installation

### RPM (Enterprise Linux)
```bash
sudo dnf config-manager --add-repo https://sckyzo.github.io/monitoring-hub/el9/$(arch)/
sudo dnf install eseries_exporter
sudo systemctl enable --now eseries_exporter
```

### Docker
```bash
docker pull ghcr.io/sckyzo/monitoring-hub/eseries_exporter:latest

docker run -d \
  -p 9313:9313 \
  -v ./eseries_exporter.yml:/etc/eseries_exporter/eseries_exporter.yml \
  ghcr.io/sckyzo/monitoring-hub/eseries_exporter:latest
```

## ⚙️ Configuration

The exporter requires a configuration file with credentials and target arrays.
Default location: `/etc/eseries_exporter/eseries_exporter.yml`.

See upstream documentation: [sckyzo/eseries_exporter](https://github.com/sckyzo/eseries_exporter)
