# Bind Exporter

Prometheus exporter for Bind (DNS) statistics.

## Overview
This exporter probes a Bind server via its HTTP statistics channel and exports metrics in Prometheus format.

## Configuration
The exporter is configured via command-line flags. By default, it listens on port `9119`.

### Common Flags
*   `-bind.stats-url`: URL of the Bind statistics channel (default `http://localhost:8053/`).
*   `-bind.pid-file`: Path to the Bind PID file.
*   `-web.listen-address`: Address to listen on for web interface and telemetry (default `:9119`).

## Usage

### RPM
```bash
sudo dnf install bind_exporter
sudo systemctl enable --now bind_exporter
```

### Docker
```bash
docker run -d -p 9119:9119 ghcr.io/sckyzo/monitoring-hub/bind_exporter:latest
```
