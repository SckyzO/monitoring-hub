# MySQL Exporter

![Build Status](https://img.shields.io/github/actions/workflow/status/SckyzO/monitoring-hub/release.yml?label=Build)
![Version](https://img.shields.io/github/v/release/prometheus/mysqld_exporter?label=Upstream)

> Prometheus exporter for MySQL server metrics.

This exporter collects metrics from a MySQL or MariaDB server. It uses the official Prometheus Go client and supports a wide range of MySQL versions.

## 🚀 Installation

### RPM (Enterprise Linux)
```bash
sudo dnf config-manager --add-repo https://sckyzo.github.io/monitoring-hub/el9/$(arch)/
sudo dnf install mysqld_exporter

# 1. Edit credentials
sudo vi /var/lib/mysqld_exporter/.my.cnf

# 2. Start service
sudo systemctl enable --now mysqld_exporter
```

### Docker
```bash
docker pull ghcr.io/sckyzo/monitoring-hub/mysqld_exporter:latest

docker run -d \
  -p 9104:9104 \
  -v ./.my.cnf:/var/lib/mysqld_exporter/.my.cnf \
  ghcr.io/sckyzo/monitoring-hub/mysqld_exporter:latest
```

## ⚙️ Configuration

The exporter requires database credentials. The recommended way is to use a `.my.cnf` file.

```ini
[client]
user=exporter
password=exporter_password
host=localhost
```

**Security Note:** This file should be readable ONLY by the `mysqld_exporter` user (`chmod 600`).

### Database Permissions
The database user needs `PROCESS`, `REPLICATION CLIENT`, and `SELECT` privileges.

```sql
CREATE USER 'exporter'@'localhost' IDENTIFIED BY 'exporter_password';
GRANT PROCESS, REPLICATION CLIENT, SELECT ON *.* TO 'exporter'@'localhost';
```

See upstream documentation: [prometheus/mysqld_exporter](https://github.com/prometheus/mysqld_exporter)