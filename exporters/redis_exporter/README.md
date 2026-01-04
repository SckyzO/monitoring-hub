# Redis Exporter

Prometheus exporter for Redis metrics.

## Overview
This exporter supports Redis versions 2.x, 3.x, 4.x, 5.x, 6.x, and 7.x.

## Configuration
The exporter is configured via command-line flags or environment variables.

### Common Flags
*   `-redis.addr`: Address of one or more Redis nodes (default `redis://localhost:6379`).
*   `-redis.password`: Password for the Redis instance.
*   `-web.listen-address`: Address to listen on (default `:9121`).

## Usage

### RPM
```bash
sudo dnf install redis_exporter
sudo systemctl enable --now redis_exporter
```

### Docker
```bash
docker run -d -p 9121:9121 ghcr.io/sckyzo/monitoring-hub/redis_exporter:latest -redis.addr redis://<REDIS_ADDR>:6379
```
