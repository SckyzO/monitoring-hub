# Monitoring Hub: snmp_exporter

Enterprise-grade packaging of the official Prometheus SNMP Exporter.

## 🚀 Features
- **Base Image:** Red Hat UBI 9 Minimal.
- **Components:** Includes `snmp_exporter` and `snmp_generator`.
- **Multi-Arch:** Support for x86_64 and aarch64.

## 📦 Usage

```bash
docker pull ghcr.io/sckyzo/monitoring-hub/snmp_exporter:latest
docker run -d -p 9116:9116 ghcr.io/sckyzo/monitoring-hub/snmp_exporter:latest
```

## 🌐 Documentation
See official documentation: [prometheus/snmp_exporter](https://github.com/prometheus/snmp_exporter)
