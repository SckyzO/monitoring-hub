# Exim Exporter

![Build Status](https://img.shields.io/github/actions/workflow/status/SckyzO/monitoring-hub/release.yml?label=Build)
![Version](https://img.shields.io/github/v/release/gvengel/exim_exporter?label=Upstream)

> Prometheus exporter for Exim mail server metrics.

## 🚀 Installation

### RPM (Enterprise Linux)
```bash
sudo dnf config-manager --add-repo https://sckyzo.github.io/monitoring-hub/el9/$(arch)/ 
sudo dnf install exim_exporter
sudo systemctl enable --now exim_exporter
```

### Docker
```bash
docker pull ghcr.io/sckyzo/monitoring-hub/exim_exporter:latest
```

## ⚙️ Configuration

The exporter needs permissions to run `exim` commands or read spool directories.

### Basic Usage
The RPM installs a systemd service running as `exim_exporter`. You may need to add this user to the `exim` group or configure sudoers if direct queue access is required.

```bash
# /etc/default/exim_exporter
OPTIONS="--exim.input-path=/var/spool/exim/input"
```

### Metrics
By default, it exposes metrics on port `9636`.

See upstream documentation: [gvengel/exim_exporter](https://github.com/gvengel/exim_exporter)
