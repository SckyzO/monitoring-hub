# Apache Exporter

[![Upstream](https://img.shields.io/badge/Upstream-Lusitaniae/apache_exporter-blue)](https://github.com/Lusitaniae/apache_exporter)

Prometheus exporter for Apache HTTP Server metrics.

## Overview
This exporter scrapes Apache `mod_status` statistics and exports them in Prometheus format.

## Configuration
The exporter requires `mod_status` to be enabled in Apache with `ExtendedStatus On`.

### Common Flags
*   `--scrape_uri`: URL to Apache status page (default `http://localhost/server-status?auto`).
*   `--telemetry.address`: Address to listen on (default `:9117`).

## Usage

### RPM
```bash
sudo dnf install apache_exporter
sudo systemctl enable --now apache_exporter
```

### Docker
```bash
docker run -d -p 9117:9117 ghcr.io/sckyzo/monitoring-hub/apache_exporter:latest --scrape_uri="http://YOUR_APACHE_SERVER/server-status?auto"
```