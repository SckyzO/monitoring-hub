# Iperf3 Exporter

![Build Status](https://img.shields.io/github/actions/workflow/status/SckyzO/monitoring-hub/release.yml?label=Build)
![Version](https://img.shields.io/github/v/release/edgard/iperf3_exporter?label=Upstream)

> Prometheus exporter for iPerf3 metrics.

## 🚀 Installation

### RPM (Enterprise Linux)
```bash
sudo dnf config-manager --add-repo https://sckyzo.github.io/monitoring-hub/el9/$(arch)/
sudo dnf install iperf3_exporter iperf3
sudo systemctl enable --now iperf3_exporter
```

### Docker
```bash
docker pull ghcr.io/sckyzo/monitoring-hub/iperf3_exporter:latest
```

## ⚙️ Configuration

The exporter requires `iperf3` to be installed on the system (included as an RPM dependency).

### Metrics
By default, it exposes metrics on port `9579`.

See upstream documentation: [edgard/iperf3_exporter](https://github.com/edgard/iperf3_exporter)
