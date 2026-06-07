# Node Exporter

![Build Status](https://img.shields.io/github/actions/workflow/status/SckyzO/monitoring-hub/release.yml?label=Build)
![Version](https://img.shields.io/github/v/release/prometheus/node_exporter?label=Upstream)

> Prometheus exporter for hardware and OS metrics exposed by *NIX kernels.

Node Exporter is the standard for monitoring Linux systems. It collects metrics on CPU, memory, disk, network, and more.

## 🚀 Installation

### RPM (Enterprise Linux)
```bash
sudo dnf config-manager --add-repo https://sckyzo.github.io/monitoring-hub/el9/$(arch)/
sudo dnf install node_exporter
sudo systemctl enable --now node_exporter
```

### Docker
```bash
docker pull ghcr.io/sckyzo/monitoring-hub/node_exporter:latest

docker run -d \
  -p 9100:9100 \
  --net="host" \
  --pid="host" \
  -v "/:/host:ro,rslave" \
  ghcr.io/sckyzo/monitoring-hub/node_exporter:latest \
  --path.rootfs=/host
```

## ⚙️ Configuration

The exporter typically runs without a configuration file, using command-line flags for customization.

See upstream documentation: [prometheus/node_exporter](https://github.com/prometheus/node_exporter)
