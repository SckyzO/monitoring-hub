# Bind Exporter

![Build Status](https://img.shields.io/github/actions/workflow/status/SckyzO/monitoring-hub/release.yml?label=Build)
![Version](https://img.shields.io/github/v/release/prometheus-community/bind_exporter?label=Upstream)

> Prometheus exporter for Bind (DNS) statistics.

This exporter probes a BIND server via its HTTP statistics channel and exports metrics in Prometheus format.

## 🚀 Installation

### RPM (Enterprise Linux)
```bash
sudo dnf config-manager --add-repo https://sckyzo.github.io/monitoring-hub/el9/$(arch)/
sudo dnf install bind_exporter
sudo systemctl enable --now bind_exporter
```

### Docker
```bash
docker pull ghcr.io/sckyzo/monitoring-hub/bind_exporter:latest

docker run -d \
  -p 9119:9119 \
  ghcr.io/sckyzo/monitoring-hub/bind_exporter:latest \
  -bind.stats-url="http://YOUR_BIND_SERVER:8053/"
```

## ⚙️ Configuration

The exporter requires the BIND server to have the statistics channel enabled.

### Common Flags
*   `-bind.stats-url`: URL of the BIND statistics channel (default `http://localhost:8053/`).
*   `-web.listen-address`: Address to listen on for web interface and telemetry (default `:9119`).

See upstream documentation: [prometheus-community/bind_exporter](https://github.com/prometheus-community/bind_exporter)
