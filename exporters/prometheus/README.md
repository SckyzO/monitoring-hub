# Monitoring Hub: prometheus

Enterprise-grade packaging of the official Prometheus server.

## 🚀 Features
- **Base Image:** Red Hat UBI 9 Minimal.
- **Components:** Includes `prometheus` and `promtool`.
- **Pre-configured:** Default configuration path at `/etc/prometheus/prometheus.yml`.

## 📦 Usage

```bash
docker pull ghcr.io/sckyzo/monitoring-hub/prometheus:latest
docker run -d -p 9090:9090 ghcr.io/sckyzo/monitoring-hub/prometheus:latest
```

## 🌐 Documentation
See official documentation: [prometheus/prometheus](https://github.com/prometheus/prometheus)
