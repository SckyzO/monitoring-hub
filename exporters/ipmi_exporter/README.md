# IPMI Exporter

Prometheus exporter for IPMI devices (Intelligent Platform Management Interface).

## Overview
This exporter collects hardware health metrics (temperatures, fans, voltages, power state) from servers via IPMI. It supports both local (in-band) and remote (out-of-band/LAN) monitoring.

## Configuration
For remote monitoring, a configuration file defining modules (user/password/driver) is recommended.

### Common Flags
*   `--config.file`: Path to configuration file (default `/etc/ipmi_exporter/ipmi_remote.yml`).
*   `--web.listen-address`: Address to listen on (default `:9290`).

### Dependencies (RPM)
The RPM package automatically installs `freeipmi` as a dependency, which provides the necessary underlying tools (`ipmimonitoring`, etc.).

## Usage

### RPM
```bash
sudo dnf install ipmi_exporter
sudo systemctl enable --now ipmi_exporter
```

### Docker
```bash
docker run -d -p 9290:9290 -v /path/to/ipmi_remote.yml:/etc/ipmi_exporter/ipmi_remote.yml ghcr.io/sckyzo/monitoring-hub/ipmi_exporter:latest
```
