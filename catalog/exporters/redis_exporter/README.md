# Redis Exporter

![Build Status](https://img.shields.io/github/actions/workflow/status/SckyzO/monitoring-hub/release.yml?label=Build)
![Version](https://img.shields.io/github/v/release/oliver006/redis_exporter?label=Upstream)

> Prometheus exporter for Redis metrics.

This exporter supports Redis versions 2.x, 3.x, 4.x, 5.x, 6.x, and 7.x.

## 🚀 Installation

### RPM (Enterprise Linux)
```bash
sudo dnf config-manager --add-repo https://sckyzo.github.io/monitoring-hub/el9/$(arch)/
sudo dnf install redis_exporter
sudo systemctl enable --now redis_exporter
```

### Docker
```bash
docker pull ghcr.io/sckyzo/monitoring-hub/redis_exporter:latest

docker run -d \
  -p 9121:9121 \
  ghcr.io/sckyzo/monitoring-hub/redis_exporter:latest \
  -redis.addr redis://YOUR_REDIS_SERVER:6379
```

## ⚙️ Configuration

The exporter is configured via command-line flags.

### Common Flags
*   `-redis.addr`: Address of the Redis node (default `redis://localhost:6379`).
*   `-redis.password`: Password for the Redis instance.
*   `-web.listen-address`: Address to listen on (default `:9121`).

See upstream documentation: [oliver006/redis_exporter](https://github.com/oliver006/redis_exporter)
