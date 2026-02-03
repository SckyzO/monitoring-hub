# Artifactory Exporter

![Build Status](https://img.shields.io/github/actions/workflow/status/SckyzO/monitoring-hub/release.yml?label=Build)
![Version](https://img.shields.io/github/v/release/peimanja/artifactory_exporter?label=Upstream)

> Prometheus exporter for JFrog Artifactory stats.

Collects metrics about an Artifactory system, including repository sizes, artifact counts, license information, and system health.

## 🚀 Installation

### RPM (Enterprise Linux)
```bash
sudo dnf config-manager --add-repo https://sckyzo.github.io/monitoring-hub/el9/$(arch)/
sudo dnf install artifactory_exporter
sudo systemctl enable --now artifactory_exporter
```

### Docker
```bash
docker pull ghcr.io/sckyzo/monitoring-hub/artifactory_exporter:latest

docker run -d \
  -p 9531:9531 \
  -e ARTI_SCRAPE_URI=http://artifactory.example.com/artifactory \
  -e ARTI_USERNAME=admin \
  -e ARTI_PASSWORD=password \
  ghcr.io/sckyzo/monitoring-hub/artifactory_exporter:latest
```

## ⚙️ Configuration

The exporter runs by default on port **9531**. It is configured primarily via environment variables.

### Environment Variables

| Variable | Description | Default |
| :--- | :--- | :--- |
| `ARTI_SCRAPE_URI` | Full URL to Artifactory | `http://localhost:8081/artifactory` |
| `ARTI_USERNAME` | Username for authentication (Basic Auth) | - |
| `ARTI_PASSWORD` | Password for authentication (Basic Auth) | - |
| `ARTI_ACCESS_TOKEN` | Bearer token (Alternative to User/Pass) | - |
| `ARTI_SSL_VERIFY` | Verify SSL certificate | `true` |
| `ARTI_TIMEOUT` | Scrape timeout | `5s` |
| `WEB_LISTEN_ADDR` | Address to listen on | `:9531` |

### Optional Metrics

You can enable expensive metrics by passing flags in the `docker run` command or `ARTS_ARGS` (if implemented in sysconfig):

* `--optional-metric=artifacts`: Count artifacts created/downloaded (resource intensive).
* `--optional-metric=replication_status`: Replication status per repo.
* `--optional-metric=federation_status`: Federation status (Enterprise+).

See upstream documentation for full details: [peimanja/artifactory_exporter](https://github.com/peimanja/artifactory_exporter)
