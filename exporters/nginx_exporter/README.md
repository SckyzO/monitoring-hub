# Nginx Exporter

![Build Status](https://img.shields.io/github/actions/workflow/status/SckyzO/monitoring-hub/release.yml?label=Build)
![Version](https://img.shields.io/github/v/release/nginx/nginx-prometheus-exporter?label=Upstream)

> Prometheus exporter for NGINX metrics.

This exporter scrapes metrics from an NGINX `stub_status` page and exports them in Prometheus format.

## 🚀 Installation

### RPM (Enterprise Linux)
```bash
sudo dnf config-manager --add-repo https://sckyzo.github.io/monitoring-hub/el9/$(arch)/
sudo dnf install nginx_exporter
sudo systemctl enable --now nginx_exporter
```

### Docker
```bash
docker pull ghcr.io/sckyzo/monitoring-hub/nginx_exporter:latest

docker run -d \
  -p 9113:9113 \
  ghcr.io/sckyzo/monitoring-hub/nginx_exporter:latest \
  -nginx.scrape-uri http://YOUR_NGINX_SERVER:8080/stub_status
```

## ⚙️ Configuration

Requires `stub_status` module enabled in Nginx.

### Common Flags
*   `-nginx.scrape-uri`: Address to scrape NGINX metrics from (default `http://127.0.0.1:8080/stub_status`).
*   `-web.listen-address`: Address to listen on (default `:9113`).

See upstream documentation: [nginx/nginx-prometheus-exporter](https://github.com/nginx/nginx-prometheus-exporter)
