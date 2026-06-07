# IPMI Exporter

![Build Status](https://img.shields.io/github/actions/workflow/status/SckyzO/monitoring-hub/release.yml?label=Build)
![Version](https://img.shields.io/github/v/release/prometheus-community/ipmi_exporter?label=Upstream)

> Prometheus exporter for IPMI devices (Intelligent Platform Management Interface).

This exporter collects hardware health metrics (temperatures, fans, voltages, power state) from servers via IPMI. It supports both local (in-band) and remote (out-of-band/LAN) monitoring.

## 🚀 Installation

### RPM (Enterprise Linux)
```bash
sudo dnf config-manager --add-repo https://sckyzo.github.io/monitoring-hub/el9/$(arch)/
sudo dnf install ipmi_exporter
sudo systemctl enable --now ipmi_exporter
```

> **Note:** The RPM package automatically installs `freeipmi` as a dependency.

### Docker
```bash
docker pull ghcr.io/sckyzo/monitoring-hub/ipmi_exporter:latest

docker run -d \
  -p 9290:9290 \
  -v ./ipmi_remote.yml:/etc/ipmi_exporter/ipmi_remote.yml \
  --device /dev/ipmi0 \
  ghcr.io/sckyzo/monitoring-hub/ipmi_exporter:latest
```

## ⚙️ Configuration

A default configuration file is provided for remote targets.
Location: `/etc/ipmi_exporter/ipmi_remote.yml`.

See upstream documentation: [prometheus-community/ipmi_exporter](https://github.com/prometheus-community/ipmi_exporter)
