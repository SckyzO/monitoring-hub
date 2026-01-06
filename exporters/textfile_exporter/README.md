# Textfile Exporter

![Build Status](https://img.shields.io/github/actions/workflow/status/SckyzO/monitoring-hub/release.yml?label=Build)
![Version](https://img.shields.io/github/v/release/SckyzO/textfile_exporter?label=Upstream)

> Prometheus exporter for local text files metrics.

This exporter reads `.prom` files from a directory and exposes them as Prometheus metrics. It is specifically designed for monitoring short-lived jobs, batch scripts, or custom system metrics.

## 🚀 Installation

### RPM (Enterprise Linux)
```bash
sudo dnf config-manager --add-repo https://sckyzo.github.io/monitoring-hub/el9/$(arch)/
sudo dnf install textfile_exporter
sudo systemctl enable --now textfile_exporter
```

### Docker
```bash
docker pull ghcr.io/sckyzo/monitoring-hub/textfile_exporter:latest

docker run -d \
  -p 9014:9014 \
  -v ./metrics:/var/lib/textfile_exporter:ro \
  ghcr.io/sckyzo/monitoring-hub/textfile_exporter:latest
```

## ⚙️ Configuration

The exporter watches the directory defined by the `--textfile.directory` flag.
Default location: `/var/lib/textfile_exporter`.

See upstream documentation: [SckyzO/textfile_exporter](https://github.com/SckyzO/textfile_exporter)
