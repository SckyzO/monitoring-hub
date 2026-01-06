# Blackbox Exporter

![Build Status](https://img.shields.io/github/actions/workflow/status/SckyzO/monitoring-hub/release.yml?label=Build)
![Version](https://img.shields.io/github/v/release/prometheus/blackbox_exporter?label=Upstream)

> Prometheus blackbox exporter for network probing (HTTP, DNS, TCP, ICMP).

The Blackbox Exporter allows probing of endpoints over HTTP, HTTPS, DNS, TCP, ICMP, and gRPC. Unlike most exporters that run on the target machine, it runs centrally and probes targets remotely.

## 🚀 Installation

### RPM (Enterprise Linux)
```bash
sudo dnf config-manager --add-repo https://sckyzo.github.io/monitoring-hub/el9/$(arch)/
sudo dnf install blackbox_exporter
sudo systemctl enable --now blackbox_exporter
```

### Docker
```bash
docker pull ghcr.io/sckyzo/monitoring-hub/blackbox_exporter:latest

docker run -d \
  -p 9115:9115 \
  -v ./blackbox.yml:/etc/blackbox_exporter/blackbox.yml \
  ghcr.io/sckyzo/monitoring-hub/blackbox_exporter:latest
```

## ⚙️ Configuration

The configuration file defines modules (e.g., `http_2xx`, `icmp`).
Default location: `/etc/blackbox_exporter/blackbox.yml`.

### Prometheus Scrape Config
```yaml
scrape_configs:
  - job_name: 'blackbox'
    metrics_path: /probe
    params:
      module: [http_2xx]  # Look for a HTTP 200 response.
    static_configs:
      - targets:
        - http://prometheus.io
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: 127.0.0.1:9115  # Blackbox exporter address
```

See upstream documentation: [prometheus/blackbox_exporter](https://github.com/prometheus/blackbox_exporter)
