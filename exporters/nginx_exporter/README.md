# Nginx Exporter

Prometheus exporter for NGINX metrics.

## Overview
This exporter scrapes metrics from an NGINX `stub_status` page and exports them in Prometheus format.

## Configuration
Requires `stub_status` module enabled in Nginx.

### Common Flags
*   `-nginx.scrape-uri`: Address to scrape NGINX metrics from (default `http://127.0.0.1:8080/stub_status`).
*   `-web.listen-address`: Address to listen on (default `:9113`).

## Usage

### RPM
```bash
sudo dnf install nginx_exporter
sudo systemctl enable --now nginx_exporter
```

### Docker
```bash
docker run -d -p 9113:9113 ghcr.io/sckyzo/monitoring-hub/nginx_exporter:latest -nginx.scrape-uri http://<NGINX_ADDR>:<PORT>/stub_status
```
