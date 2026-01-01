# Monitoring Hub: smartctl_exporter

Enterprise-grade packaging of the Prometheus smartctl_exporter.

## 🚀 Features
- **Base Image:** Red Hat UBI 9 Minimal.
- **Security:** Built from official upstream sources.
- **Multi-Arch:** Support for x86_64 and aarch64.

## 📦 Usage

```bash
docker pull ghcr.io/sckyzo/monitoring-hub/smartctl_exporter:latest
docker run -d -p 9633:9633 --privileged ghcr.io/sckyzo/monitoring-hub/smartctl_exporter:latest
```

## 🌐 Documentation
See official documentation: [prometheus-community/smartctl_exporter](https://github.com/prometheus-community/smartctl_exporter)
