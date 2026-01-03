# Monitoring Hub: ha_cluster_exporter

Enterprise-grade packaging of the ClusterLabs HA Cluster Exporter (Pacemaker/Corosync).

## 🚀 Features
- **Base Image:** Red Hat UBI 9 Minimal.
- **Support:** Pacemaker, Corosync, and SBD metrics.
- **Multi-Arch:** Support for x86_64 and aarch64.

## 📦 Usage

```bash
docker pull ghcr.io/sckyzo/monitoring-hub/ha_cluster_exporter:latest
docker run -d -p 9664:9664 ghcr.io/sckyzo/monitoring-hub/ha_cluster_exporter:latest
```

## 🌐 Documentation
See official documentation: [ClusterLabs/ha_cluster_exporter](https://github.com/ClusterLabs/ha_cluster_exporter)