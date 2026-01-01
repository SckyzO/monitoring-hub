# Monitoring Hub: alertmanager

Enterprise-grade packaging of the official Prometheus Alertmanager.

## 🚀 Features
- **Base Image:** Red Hat UBI 9 Minimal.
- **Components:** Includes `alertmanager` and `amtool`.
- **Pre-configured:** Default configuration path at `/etc/alertmanager/alertmanager.yml`.

## 📦 Usage

```bash
docker pull ghcr.io/sckyzo/monitoring-hub/alertmanager:latest
docker run -d -p 9093:9093 ghcr.io/sckyzo/monitoring-hub/alertmanager:latest
```

## 🌐 Documentation
See official documentation: [prometheus/alertmanager](https://github.com/prometheus/alertmanager)
