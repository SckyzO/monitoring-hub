# Blackbox Exporter

[![Upstream](https://img.shields.io/badge/Upstream-prometheus/blackbox_exporter-blue)](https://github.com/prometheus/blackbox_exporter)

The Blackbox Exporter allows probing of endpoints over HTTP, HTTPS, DNS, TCP, ICMP, and gRPC.

## Overview
Unlike most exporters that run on the target machine, the Blackbox Exporter runs centrally and probes targets remotely. It is essential for "Canary" testing and availability monitoring.

## Configuration
The exporter requires a configuration file (`blackbox.yml`) defining modules (e.g., `http_2xx`, `icmp`). A default configuration file is provided in `/etc/blackbox_exporter/blackbox.yml`.

### Common Flags
*   `--config.file`: Path to configuration file (default `/etc/blackbox_exporter/blackbox.yml`).
*   `--web.listen-address`: Address to listen on (default `:9115`).

## Usage

### RPM
```bash
sudo dnf install blackbox_exporter
sudo systemctl enable --now blackbox_exporter
```

### Docker
```bash
docker run -d -p 9115:9115 -v /path/to/blackbox.yml:/etc/blackbox_exporter/blackbox.yml ghcr.io/sckyzo/monitoring-hub/blackbox_exporter:latest
```

## Example Scrape Config (Prometheus)
```yaml
scrape_configs:
  - job_name: 'blackbox'
    metrics_path: /probe
    params:
      module: [http_2xx]  # Look for a HTTP 200 response.
    static_configs:
      - targets:
        - http://prometheus.io    # Target to probe with http_2xx
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: 127.0.0.1:9115  # The blackbox exporter's real hostname:port.
```