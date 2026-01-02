# Monitoring Hub: eseries_exporter

Enterprise-grade packaging of the NetApp/Lenovo E-Series storage exporter.

## 🚀 Features
- **Base Image:** Red Hat UBI 9 Minimal.
- **Security:** Built from official upstream sources.
- **Multi-Arch:** Support for x86_64 and aarch64.

## 📦 Usage

```bash
docker pull ghcr.io/sckyzo/monitoring-hub/eseries_exporter:latest
docker run -d -p 9128:9128 \
  -v /path/to/config.yml:/etc/eseries_exporter/eseries_exporter.yml \
  ghcr.io/sckyzo/monitoring-hub/eseries_exporter:latest
```

## 🌐 Documentation
See official documentation: [sckyzo/eseries_exporter](https://github.com/sckyzo/eseries_exporter)

```