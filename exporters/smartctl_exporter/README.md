# Smartctl Exporter

![Build Status](https://img.shields.io/github/actions/workflow/status/SckyzO/monitoring-hub/release.yml?label=Build)
![Version](https://img.shields.io/github/v/release/prometheus-community/smartctl_exporter?label=Upstream)

> Prometheus exporter for S.M.A.R.T. storage devices metrics.

This exporter exposes S.M.A.R.T. (Self-Monitoring, Analysis and Reporting Technology) metrics from storage devices by executing the `smartctl` command.

## 🚀 Installation

### RPM (Enterprise Linux)
```bash
sudo dnf config-manager --add-repo https://sckyzo.github.io/monitoring-hub/el9/$(arch)/
sudo dnf install smartctl_exporter
sudo systemctl enable --now smartctl_exporter
```

### Docker
```bash
docker pull ghcr.io/sckyzo/monitoring-hub/smartctl_exporter:latest

# Requires privileged access to read hardware devices
docker run -d \
  -p 9633:9633 \
  --privileged \
  ghcr.io/sckyzo/monitoring-hub/smartctl_exporter:latest
```

## ⚙️ Configuration

The exporter requires access to the host's block devices. In some cases, you may need to specify device paths via flags.

See upstream documentation: [prometheus-community/smartctl_exporter](https://github.com/prometheus-community/smartctl_exporter)