# Alertmanager

![Build Status](https://img.shields.io/github/actions/workflow/status/SckyzO/monitoring-hub/release.yml?label=Build)
![Version](https://img.shields.io/github/v/release/prometheus/alertmanager?label=Upstream)

> Handle alerts and notifications for the Prometheus ecosystem.

The Alertmanager handles alerts sent by client applications such as the Prometheus server. It takes care of deduplicating, grouping, and routing them to the correct receiver integration such as email, PagerDuty, or OpsGenie.

## 🚀 Installation

### RPM (Enterprise Linux)
```bash
sudo dnf config-manager --add-repo https://sckyzo.github.io/monitoring-hub/el9/$(arch)/
sudo dnf install alertmanager
```

### Docker
```bash
docker pull ghcr.io/sckyzo/monitoring-hub/alertmanager:latest

# Run with custom configuration
docker run -d \
  -p 9093:9093 \
  -v ./alertmanager.yml:/etc/alertmanager/alertmanager.yml \
  ghcr.io/sckyzo/monitoring-hub/alertmanager:latest
```

## ⚙️ Configuration

The default configuration file is located at `/etc/alertmanager/alertmanager.yml`.

See upstream documentation: [prometheus/alertmanager](https://github.com/prometheus/alertmanager)
