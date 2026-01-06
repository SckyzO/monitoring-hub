# Dell Hardware Exporter

![Build Status](https://img.shields.io/github/actions/workflow/status/SckyzO/monitoring-hub/release.yml?label=Build)
![Version](https://img.shields.io/github/v/release/galexrt/dellhw_exporter?label=Upstream)

> Prometheus exporter for Dell Hardware components using OMSA.

This exporter wraps the `omreport` command from Dell OpenManage Server Administrator (OMSA). It collects metrics on fans, power supplies, temperatures, storage, and more.

## 🚀 Installation

### Prerequisites
**DELL OMSA services must be installed and running on the host!**

### RPM (Enterprise Linux)
```bash
sudo dnf config-manager --add-repo https://sckyzo.github.io/monitoring-hub/el9/$(arch)/ 
sudo dnf install dellhw_exporter
sudo systemctl enable --now dellhw_exporter
```

### Docker
> **NOTE:** The `--privileged` flag is required as OMSA needs to access the host's devices.

```bash
docker pull ghcr.io/sckyzo/monitoring-hub/dellhw_exporter:latest

docker run -d \
  --name dellhw_exporter \
  --privileged \
  -p 9137:9137 \
  -v /etc/hostname:/etc/hostname:ro \
  ghcr.io/sckyzo/monitoring-hub/dellhw_exporter:latest
```

## ⚙️ Configuration

The exporter runs on port **9137** by default.

### Main Flags

| Flag | Description | Default |
| :--- | :--- | :--- |
| `--web.listen-address` | Address to listen on | `:9137` |
| `--web.telemetry-path` | Path to expose metrics | `/metrics` |
| `--omreport.path` | Path to omreport binary | `/opt/dell/srvadmin/bin/omreport` |

See upstream documentation: [galexrt/dellhw_exporter](https://github.com/galexrt/dellhw_exporter)