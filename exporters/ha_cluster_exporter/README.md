# HA Cluster Exporter

![Build Status](https://img.shields.io/github/actions/workflow/status/SckyzO/monitoring-hub/release.yml?label=Build)
![Version](https://img.shields.io/github/v/release/ClusterLabs/ha_cluster_exporter?label=Upstream)

> Prometheus exporter for High Availability clusters (Pacemaker, Corosync).

This exporter collects metrics from Pacemaker, Corosync, SBD, and DRBD to monitor the health of High Availability clusters.

## 🚀 Installation

### RPM (Enterprise Linux)
```bash
sudo dnf config-manager --add-repo https://sckyzo.github.io/monitoring-hub/el9/$(arch)/
sudo dnf install ha_cluster_exporter
sudo systemctl enable --now ha_cluster_exporter
```

### Docker
```bash
docker pull ghcr.io/sckyzo/monitoring-hub/ha_cluster_exporter:latest

# Requires privileged access to cluster tools/sockets
docker run -d \
  -p 9664:9664 \
  --privileged \
  -v /var/run/crm:/var/run/crm \
  -v /var/run/corosync:/var/run/corosync \
  ghcr.io/sckyzo/monitoring-hub/ha_cluster_exporter:latest
```

## ⚙️ Configuration

The exporter typically requires no configuration but needs access to the cluster management sockets (`crm`, `corosync`).

See upstream documentation: [ClusterLabs/ha_cluster_exporter](https://github.com/ClusterLabs/ha_cluster_exporter)
