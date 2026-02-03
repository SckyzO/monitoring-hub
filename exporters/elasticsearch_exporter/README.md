# Elasticsearch Exporter

![Build Status](https://img.shields.io/github/actions/workflow/status/SckyzO/monitoring-hub/release.yml?label=Build)
![Version](https://img.shields.io/github/v/release/prometheus-community/elasticsearch_exporter?label=Upstream)

> Prometheus exporter for various metrics about Elasticsearch.

## 🚀 Installation

### RPM (Enterprise Linux)
```bash
sudo dnf config-manager --add-repo https://sckyzo.github.io/monitoring-hub/el9/$(arch)/
sudo dnf install elasticsearch_exporter
```

### Docker
```bash
docker pull ghcr.io/sckyzo/monitoring-hub/elasticsearch_exporter:latest
```

## ⚙️ Configuration

By default, the exporter connects to `http://localhost:9200`.

### Basic Usage
To configure the Elasticsearch URI, use the `--es.uri` flag:

```bash
# /etc/default/elasticsearch_exporter or systemd service override
OPTIONS="--es.uri=http://elasticsearch.example.com:9200"
```

### Authentication
If your cluster requires authentication, include it in the URI:
```bash
OPTIONS="--es.uri=https://user:password@elasticsearch.example.com:9200"
```

### Metrics
Some metrics are disabled by default to reduce load. Enable them as needed:
```bash
OPTIONS="--es.uri=http://localhost:9200 --es.all --es.indices"
```

See upstream documentation: [prometheus-community/elasticsearch_exporter](https://github.com/prometheus-community/elasticsearch_exporter)
