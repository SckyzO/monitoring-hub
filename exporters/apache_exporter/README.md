# Apache Exporter

![Build Status](https://img.shields.io/github/actions/workflow/status/SckyzO/monitoring-hub/release.yml?label=Build)
![Version](https://img.shields.io/github/v/release/Lusitaniae/apache_exporter?label=Upstream)

> Prometheus exporter for Apache HTTP Server metrics.

This exporter scrapes Apache `mod_status` statistics and exports them in Prometheus format.

## 🚀 Installation

### RPM (Enterprise Linux)
```bash
sudo dnf config-manager --add-repo https://sckyzo.github.io/monitoring-hub/el9/$(arch)/
sudo dnf install apache_exporter
sudo systemctl enable --now apache_exporter
```

### Docker
```bash
docker pull ghcr.io/sckyzo/monitoring-hub/apache_exporter:latest

docker run -d \
  -p 9117:9117 \
  ghcr.io/sckyzo/monitoring-hub/apache_exporter:latest \
  --scrape_uri="http://YOUR_APACHE_SERVER/server-status?auto"
```

## ⚙️ Configuration

The exporter requires `mod_status` to be enabled in Apache with `ExtendedStatus On`.

### Common Flags
*   `--scrape_uri`: URL to Apache status page (default `http://localhost/server-status?auto`).
*   `--telemetry.address`: Address to listen on (default `:9117`).

See upstream documentation: [Lusitaniae/apache_exporter](https://github.com/Lusitaniae/apache_exporter)
