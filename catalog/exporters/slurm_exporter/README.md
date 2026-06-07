# Slurm Exporter

![Build Status](https://img.shields.io/github/actions/workflow/status/SckyzO/monitoring-hub/release.yml?label=Build)
![Version](https://img.shields.io/github/v/release/sckyzo/slurm_exporter?label=Upstream)

> Prometheus exporter for Slurm workload manager metrics.

This exporter collects metrics from Slurm clusters (nodes, partitions, jobs) and exposes them for Prometheus.

## 🚀 Installation

### RPM (Enterprise Linux)
```bash
sudo dnf config-manager --add-repo https://sckyzo.github.io/monitoring-hub/el9/$(arch)/
sudo dnf install slurm_exporter
sudo systemctl enable --now slurm_exporter
```

### Docker
```bash
docker pull ghcr.io/sckyzo/monitoring-hub/slurm_exporter:latest

# Requires access to Slurm CLI tools and configuration
docker run -d \
  -p 9341:9341 \
  -v /etc/slurm:/etc/slurm:ro \
  ghcr.io/sckyzo/monitoring-hub/slurm_exporter:latest
```

## ⚙️ Configuration

The exporter requires access to Slurm binaries (`sinfo`, `squeue`) and the `slurm.conf` file.

See upstream documentation: [sckyzo/slurm_exporter](https://github.com/sckyzo/slurm_exporter)
