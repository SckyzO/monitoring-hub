# Frr Exporter

![Build Status](https://img.shields.io/github/actions/workflow/status/SckyzO/monitoring-hub/release.yml?label=Build)
![Version](https://img.shields.io/github/v/release/tynany/frr_exporter?label=Upstream)

> Prometheus exporter for FRR metrics.

## 🚀 Installation

### RPM (Enterprise Linux)
```bash
sudo dnf config-manager --add-repo https://sckyzo.github.io/monitoring-hub/el9/$(arch)/
sudo dnf install frr_exporter
sudo systemctl enable --now frr_exporter
```

### Docker
This exporter uses a custom Docker image based on `quay.io/frrouting/frr:10.1.3` to ensure compatibility with FRR tools.

To allow the exporter to access FRR sockets, you must mount the socket directory:

```bash
docker run -d \
  -p 9342:9342 \
  -v /var/run/frr:/var/run/frr:ro \
  ghcr.io/sckyzo/monitoring-hub/frr_exporter:latest
```

## ⚙️ Configuration

The exporter connects to FRR daemon sockets (default `/var/run/frr`).

### Permissions
The user running the exporter (`frr_exporter`) must have access to the FRR socket directory.
Ensure the user is part of the `frr` or `frrvty` group:

```bash
sudo usermod -a -G frr,frrvty frr_exporter
```

### Collectors
Many BGP-specific collectors are disabled by default to improve performance. You can enable them via flags:

```bash
# /etc/default/frr_exporter
OPTIONS="--collector.bgp.peer-types --collector.bgp.peer-descriptions"
```

See upstream documentation: [tynany/frr_exporter](https://github.com/tynany/frr_exporter)
