# Prometheus

![Build Status](https://img.shields.io/github/actions/workflow/status/SckyzO/monitoring-hub/release.yml?label=Build)
![Version](https://img.shields.io/github/v/release/prometheus/prometheus?label=Upstream)

> The Prometheus monitoring system and time series database.

Prometheus is an open-source systems monitoring and alerting toolkit. It collects and stores its metrics as time series data, i.e. metrics information is stored with the timestamp at which it was recorded, alongside optional key-value pairs called labels.

## 🚀 Installation

### RPM (Enterprise Linux)
```bash
sudo dnf config-manager --add-repo https://sckyzo.github.io/monitoring-hub/el9/$(arch)/
sudo dnf install prometheus
sudo systemctl enable --now prometheus
```

### Docker
```bash
docker pull ghcr.io/sckyzo/monitoring-hub/prometheus:latest

docker run -d \
  -p 9090:9090 \
  -v ./prometheus.yml:/etc/prometheus/prometheus.yml \
  -v prometheus_data:/var/lib/prometheus \
  ghcr.io/sckyzo/monitoring-hub/prometheus:latest
```

## ⚙️ Configuration

The default configuration file is located at `/etc/prometheus/prometheus.yml`.
The database is stored in `/var/lib/prometheus`.

See upstream documentation: [prometheus/prometheus](https://github.com/prometheus/prometheus)
