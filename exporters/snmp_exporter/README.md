# SNMP Exporter

![Build Status](https://img.shields.io/github/actions/workflow/status/SckyzO/monitoring-hub/release.yml?label=Build)
![Version](https://img.shields.io/github/v/release/prometheus/snmp_exporter?label=Upstream)

> Prometheus exporter for SNMP-enabled devices.

This exporter exposes metrics from SNMP-enabled devices (switches, routers, UPS, etc.) by mapping SNMP MIBs to Prometheus metrics.

## 🚀 Installation

### RPM (Enterprise Linux)
```bash
sudo dnf config-manager --add-repo https://sckyzo.github.io/monitoring-hub/el9/$(arch)/
sudo dnf install snmp_exporter
sudo systemctl enable --now snmp_exporter
```

### Docker
```bash
docker pull ghcr.io/sckyzo/monitoring-hub/snmp_exporter:latest

docker run -d \
  -p 9116:9116 \
  -v ./snmp.yml:/etc/snmp_exporter/snmp.yml \
  ghcr.io/sckyzo/monitoring-hub/snmp_exporter:latest
```

## ⚙️ Configuration

The exporter requires a `snmp.yml` configuration file generated from MIBs.
A default `snmp.yml` is provided at `/etc/snmp_exporter/snmp.yml`.

See upstream documentation: [prometheus/snmp_exporter](https://github.com/prometheus/snmp_exporter)