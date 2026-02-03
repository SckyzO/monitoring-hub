# Ebpf Exporter

![Build Status](https://img.shields.io/github/actions/workflow/status/SckyzO/monitoring-hub/release.yml?label=Build)
![Version](https://img.shields.io/github/v/release/cloudflare/ebpf_exporter?label=Upstream)

> Prometheus exporter for custom eBPF metrics.

## 🚀 Installation

### RPM (Enterprise Linux)
```bash
sudo dnf config-manager --add-repo https://sckyzo.github.io/monitoring-hub/el9/$(arch)/
sudo dnf install ebpf_exporter
sudo systemctl enable --now ebpf_exporter
```

### Docker
```bash
docker pull ghcr.io/sckyzo/monitoring-hub/ebpf_exporter:latest
```

## ⚙️ Configuration

**This exporter requires a configuration file to define eBPF programs.**
It also requires **privileged** access to the kernel (CAP_SYS_ADMIN).

### 1. Create a config file
By default, the RPM expects configuration in `/etc/ebpf_exporter/config.yaml`.
See [examples here](https://github.com/cloudflare/ebpf_exporter/tree/master/examples).

```yaml
# /etc/ebpf_exporter/config.yaml
programs:
  - name: timers
    metrics:
      timers:
        - name: timer_start
          type: counter
          help: Timer start counts
    tracepoints:
      - timer:timer_start
```

### 2. Permissions
Ensure the service runs as a user with enough capabilities (usually root or CAP_BPF/CAP_SYS_ADMIN).
The provided systemd unit runs as a dedicated user, so you might need to adjust capabilities via `systemctl edit ebpf_exporter`.

```ini
[Service]
AmbientCapabilities=CAP_SYS_ADMIN CAP_BPF CAP_PERFMON
```

See upstream documentation: [cloudflare/ebpf_exporter](https://github.com/cloudflare/ebpf_exporter)
