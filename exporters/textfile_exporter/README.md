# Textfile Exporter

Prometheus exporter for local text files metrics.

## Overview
This exporter reads `.prom` files from a directory and exports them in Prometheus format. It's useful for monitoring cron jobs or batch scripts.

## Configuration
The exporter is configured via command-line flags.

### Common Flags
*   `-directory`: Directory to read `.prom` files from (default `/var/lib/textfile_exporter`).
*   `-addr`: Address to listen on (default `:9106`).

## Usage

### RPM
```bash
sudo dnf install textfile_exporter
sudo systemctl enable --now textfile_exporter
```

### Docker
```bash
docker run -d -p 9106:9106 -v /path/to/metrics:/var/lib/textfile_exporter ghcr.io/sckyzo/monitoring-hub/textfile_exporter:latest
```
