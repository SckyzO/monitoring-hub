# Monitoring Hub: node_exporter

Enterprise-grade packaging of the official Prometheus node_exporter.

## 🚀 Features
- **Base Image:** Red Hat UBI 9 Minimal.
- **Security:** Scanned and built from official upstream sources.
- **Multi-Arch:** Native support for x86_64 and aarch64.

## 📦 Usage

```bash
docker pull ghcr.io/sckyzo/monitoring-hub/node_exporter:latest
docker run -d -p 9100:9100 ghcr.io/sckyzo/monitoring-hub/node_exporter:latest
```

## 🌐 Documentation
See official documentation: [prometheus/node_exporter](https://github.com/prometheus/node_exporter)
