# Domain Exporter

![Build Status](https://img.shields.io/github/actions/workflow/status/SckyzO/monitoring-hub/release.yml?label=Build)
![Version](https://img.shields.io/github/v/release/caarlos0/domain_exporter?label=Upstream)

> Exports the expiration time of your domains as Prometheus metrics.

Domain Exporter checks WHOIS information to provide expiration dates for your domains. It works similarly to the Blackbox Exporter using a probe pattern.

## 🚀 Installation

### RPM (Enterprise Linux)
```bash
sudo dnf config-manager --add-repo https://sckyzo.github.io/monitoring-hub/el9/$(arch)/
sudo dnf install domain_exporter
sudo systemctl enable --now domain_exporter
```

### Docker
```bash
docker pull ghcr.io/sckyzo/monitoring-hub/domain_exporter:latest

docker run -d \
  -p 9222:9222 \
  ghcr.io/sckyzo/monitoring-hub/domain_exporter:latest
```

## ⚙️ Configuration

The exporter runs on port **9222** by default.

### Prometheus Probe Configuration
To probe domains, use the following configuration in your `prometheus.yml`:

```yaml
- job_name: domain
  metrics_path: /probe
  relabel_configs:
    - source_labels: [__address__]
      target_label: __param_target
    - target_label: __address__
      replacement: domain-exporter-host:9222
  static_configs:
    - targets:
      - example.com
      - my-awesome-project.io
```

### Static Configuration
You can also provide a list of domains via a configuration file:
```bash
domain_exporter --config=domains.yaml
```

| Flag | Description | Default |
| :--- | :--- | :--- |
| `--bind` | Address to listen on | `:9222` |
| `--config` | Path to configuration file | - |

See upstream documentation: [caarlos0/domain_exporter](https://github.com/caarlos0/domain_exporter)
