# GPFS Exporter

![Build Status](https://img.shields.io/github/actions/workflow/status/SckyzO/monitoring-hub/release.yml?label=Build)
![Version](https://img.shields.io/github/v/release/treydock/gpfs_exporter?label=Upstream)

> Prometheus exporter for IBM GPFS (Spectrum Scale) metrics.

This exporter collects metrics from IBM Spectrum Scale (formerly GPFS) clusters via `mmapplypolicy` or direct command execution.

> **Note:** This exporter is currently available for **x86_64 (AMD64)** architecture only.

## 🚀 Installation

### RPM (Enterprise Linux)
```bash
sudo dnf config-manager --add-repo https://sckyzo.github.io/monitoring-hub/el9/$(arch)/
sudo dnf install gpfs_exporter
sudo systemctl enable --now gpfs_exporter
```

### Docker
```bash
docker pull ghcr.io/sckyzo/monitoring-hub/gpfs_exporter:latest

# Requires access to GPFS binaries and socket
docker run -d \
  -p 9303:9303 \
  --privileged \
  -v /usr/lpp/mmfs/bin:/usr/lpp/mmfs/bin \
  -v /var/mmfs:/var/mmfs \
  ghcr.io/sckyzo/monitoring-hub/gpfs_exporter:latest
```

## ⚙️ Configuration

No configuration file is required by default, but it relies on access to GPFS CLI tools.

See upstream documentation: [treydock/gpfs_exporter](https://github.com/treydock/gpfs_exporter)