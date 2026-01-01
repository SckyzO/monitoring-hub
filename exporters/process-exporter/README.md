# Monitoring Hub: process-exporter

Enterprise-grade packaging of the Prometheus process-exporter.

## 🚀 Features
- **Base Image:** Red Hat UBI 9 Minimal.
- **Security:** Built from official upstream sources.
- **Multi-Arch:** Support for x86_64 and aarch64.

## 📦 Usage

```bash
docker pull ghcr.io/sckyzo/monitoring-hub/process-exporter:latest
docker run -d -p 9256:9256 --privileged ghcr.io/sckyzo/monitoring-hub/process-exporter:latest
```

## 🌐 Documentation
See official documentation: [ncabatoff/process-exporter](https://github.com/ncabatoff/process-exporter)
