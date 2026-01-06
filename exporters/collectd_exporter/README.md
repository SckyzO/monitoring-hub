# Collectd Exporter

![Build Status](https://img.shields.io/github/actions/workflow/status/SckyzO/monitoring-hub/release.yml?label=Build)
![Version](https://img.shields.io/github/v/release/prometheus/collectd_exporter?label=Upstream)

> Relay metrics from collectd to Prometheus.

Collectd Exporter accepts metrics from collectd's binary network protocol or JSON format via HTTP POST, and transforms them for consumption by Prometheus.

## 🚀 Installation

### RPM (Enterprise Linux)
```bash
sudo dnf config-manager --add-repo https://sckyzo.github.io/monitoring-hub/el9/$(arch)/
sudo dnf install collectd_exporter
sudo systemctl enable --now collectd_exporter
```

### Docker
```bash
docker pull ghcr.io/sckyzo/monitoring-hub/collectd_exporter:latest

docker run -d \
  -p 9103:9103 \
  -p 25826:25826/udp \
  ghcr.io/sckyzo/monitoring-hub/collectd_exporter:latest \
  --collectd.listen-address=":25826"
```

## ⚙️ Configuration

The exporter runs on port **9103** by default.

### Binary Network Protocol
To send metrics from collectd using the network plugin:
```
LoadPlugin network
<Plugin network>
  Server "exporter-host" "25826"
</Plugin>
```

### HTTP POST (JSON)
To send metrics via the `write_http` plugin:
```
LoadPlugin write_http
<Plugin write_http>
  <Node "collectd_exporter">
    URL "http://exporter-host:9103/collectd-post"
    Format "JSON"
    StoreRates false
  </Node>
</Plugin>
```

### Main Flags

| Flag | Description | Default |
| :--- | :--- | :--- |
| `--collectd.listen-address` | Network address to listen on for binary packets | `:25826` |
| `--web.collectd-push-path` | Path to serve HTTP POST requests | `/collectd-post` |
| `--web.listen-address` | Address to listen on for web interface | `:9103` |

See upstream documentation: [prometheus/collectd_exporter](https://github.com/prometheus/collectd_exporter)