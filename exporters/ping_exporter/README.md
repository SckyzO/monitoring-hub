# Monitoring Hub: ping_exporter

Enterprise-grade packaging of the Prometheus ping_exporter.

## 🚀 Features
- **Base Image:** Red Hat UBI 9 Minimal.
- **Security:** Built from official upstream sources.
- **Multi-Arch:** Support for x86_64 and aarch64.

## 📦 Usage

```bash
docker pull ghcr.io/sckyzo/monitoring-hub/ping_exporter:latest
docker run -d -p 9427:9427 --privileged ghcr.io/sckyzo/monitoring-hub/ping_exporter:latest
```

## 🌐 Documentation
See official documentation: [jaxxstorm/ping_exporter](https://github.com/jaxxstorm/ping_exporter)
