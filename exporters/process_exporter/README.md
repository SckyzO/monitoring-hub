# Process Exporter

![Build Status](https://img.shields.io/github/actions/workflow/status/SckyzO/monitoring-hub/release.yml?label=Build)
![Version](https://img.shields.io/github/v/release/ncabatoff/process-exporter?label=Upstream)

> Prometheus exporter for process metrics.

Process Exporter allows you to monitor selected processes by reading `/proc` on Linux. It can group processes by name, user, or other attributes.

## 🚀 Installation

### RPM (Enterprise Linux)
```bash
sudo dnf config-manager --add-repo https://sckyzo.github.io/monitoring-hub/el9/$(arch)/
sudo dnf install process_exporter
sudo systemctl enable --now process_exporter
```

### Docker
```bash
docker pull ghcr.io/sckyzo/monitoring-hub/process_exporter:latest

# Requires access to the host's /proc filesystem
docker run -d \
  -p 9256:9256 \
  --privileged \
  -v /proc:/host/proc:ro \
  ghcr.io/sckyzo/monitoring-hub/process_exporter:latest \
  -procfs /host/proc
```

## ⚙️ Configuration

The exporter is typically configured using a YAML file to define process matching groups.

See upstream documentation: [ncabatoff/process-exporter](https://github.com/ncabatoff/process-exporter)