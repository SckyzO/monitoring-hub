# MySQL Exporter

[![Upstream](https://img.shields.io/badge/Upstream-prometheus/mysqld_exporter-blue)](https://github.com/prometheus/mysqld_exporter)

Prometheus exporter for MySQL server metrics.

## Overview
This exporter collects metrics from a MySQL or MariaDB server. It uses the official Prometheus Go client and supports a wide range of MySQL versions.

## Configuration
The exporter requires database credentials. The recommended way is to use a `.my.cnf` file.

### Default Configuration
A default configuration file is provided at `/var/lib/mysqld_exporter/.my.cnf`:

```ini
[client]
user=exporter
password=exporter_password
host=localhost
```

**Security Note:** This file should be readable ONLY by the `mysqld_exporter` user (`chmod 600`).

### Common Flags
*   `--config.my-cnf`: Path to `.my.cnf` file (default `~/.my.cnf`).
*   `--web.listen-address`: Address to listen on (default `:9104`).

## Usage

### RPM
```bash
# 1. Edit credentials
sudo vi /var/lib/mysqld_exporter/.my.cnf

# 2. Start service
sudo systemctl enable --now mysqld_exporter
```

### Docker
```bash
docker run -d -p 9104:9104 \
  -v /path/to/.my.cnf:/var/lib/mysqld_exporter/.my.cnf \
  ghcr.io/sckyzo/monitoring-hub/mysqld_exporter:latest
```

## Database Permissions
The database user needs `PROCESS`, `REPLICATION CLIENT`, and `SELECT` privileges.

```sql
CREATE USER 'exporter'@'localhost' IDENTIFIED BY 'exporter_password';
GRANT PROCESS, REPLICATION CLIENT, SELECT ON *.* TO 'exporter'@'localhost';
```

