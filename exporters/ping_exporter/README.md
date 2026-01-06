# Ping Exporter

![Build Status](https://img.shields.io/github/actions/workflow/status/SckyzO/monitoring-hub/release.yml?label=Build)
![Version](https://img.shields.io/github/v/release/czerwonk/ping_exporter?label=Upstream)

> Prometheus exporter for ICMP ping metrics.

This exporter sends ICMP pings to specified targets and exposes the results (latency, packet loss) as Prometheus metrics.

## 🚀 Installation

### RPM (Enterprise Linux)
```bash
sudo dnf config-manager --add-repo https://sckyzo.github.io/monitoring-hub/el9/$(arch)/
sudo dnf install ping_exporter
sudo systemctl enable --now ping_exporter
```

### Docker
```bash
docker pull ghcr.io/sckyzo/monitoring-hub/ping_exporter:latest

# Requires privileged access or CAP_NET_RAW for ICMP
docker run -d \
  -p 9427:9427 \
  --privileged \
  -v ./ping.yml:/etc/ping_exporter/ping.yml \
  ghcr.io/sckyzo/monitoring-hub/ping_exporter:latest
```

## ⚙️ Configuration

The exporter requires a target list in a YAML configuration file.
Default location: `/etc/ping_exporter/ping.yml`.

See upstream documentation: [czerwonk/ping_exporter](https://github.com/czerwonk/ping_exporter)
