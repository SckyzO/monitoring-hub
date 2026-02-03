import json
import os

import click

MOCK_EXPORTERS = [
    {
        "name": "alertmanager",
        "version": "0.30.0",
        "description": "Handle alerts and notifications for the Prometheus ecosystem",
        "category": "Infrastructure",
        "new": False,
        "updated": False,
        "rpm_status": "success",
        "docker_status": "success",
        "upstream": {
            "type": "github",
            "repo": "prometheus/alertmanager",
            "strategy": "latest_release",
        },
        "artifacts": {
            "rpm": {
                "enabled": True,
                "targets": ["el8", "el9", "el10"],
                "summary": "Prometheus Alertmanager",
                "service_file": True,
                "system_user": "alertmanager",
                "extra_files": [
                    {
                        "source": "assets/alertmanager.yml",
                        "dest": "/etc/alertmanager/alertmanager.yml",
                        "config": True,
                    }
                ],
                "directories": [
                    {"path": "/etc/alertmanager", "mode": "0755", "owner": "root", "group": "root"},
                    {
                        "path": "/var/lib/alertmanager",
                        "mode": "0755",
                        "owner": "alertmanager",
                        "group": "alertmanager",
                    },
                ],
            },
            "docker": {
                "enabled": True,
                "entrypoint": ["/usr/bin/alertmanager"],
                "cmd": ["--config.file=/etc/alertmanager/alertmanager.yml"],
                "validation": {"port": 9093},
            },
        },
        "build": {
            "method": "binary_repack",
            "binary_name": "alertmanager",
            "extra_binaries": ["amtool"],
        },
        "readme": "# alertmanager\nRandomized production mock for UI stress-testing.",
        "availability": {
            "el8": {"x86_64": {"status": "success"}, "aarch64": {"status": "na"}},
            "el9": {"x86_64": {"status": "failed"}, "aarch64": {"status": "success"}},
            "el10": {"x86_64": {"status": "na"}, "aarch64": {"status": "na"}},
        },
    },
    {
        "name": "apache_exporter",
        "version": "1.0.10",
        "description": "Prometheus exporter for Apache HTTP Server",
        "category": "Web",
        "new": False,
        "updated": True,
        "rpm_status": "failed",
        "docker_status": "success",
        "upstream": {"type": "github", "repo": "Lusitaniae/apache_exporter"},
        "artifacts": {
            "rpm": {
                "enabled": True,
                "summary": "Prometheus Apache Exporter",
                "targets": ["el8", "el9", "el10"],
                "system_user": "apache_exporter",
                "service_file": True,
                "extra_files": [],
                "directories": [
                    {
                        "path": "/var/lib/apache_exporter",
                        "owner": "apache_exporter",
                        "group": "apache_exporter",
                        "mode": "0755",
                    }
                ],
            },
            "docker": {
                "enabled": True,
                "entrypoint": ["/usr/bin/apache_exporter"],
                "validation": {"port": 9117},
            },
        },
        "build": {"method": "binary_repack", "binary_name": "apache_exporter"},
        "readme": "# apache_exporter\nRandomized production mock for UI stress-testing.",
        "availability": {
            "el8": {"x86_64": {"status": "success"}, "aarch64": {"status": "failed"}},
            "el9": {"x86_64": {"status": "success"}, "aarch64": {"status": "success"}},
            "el10": {"x86_64": {"status": "na"}, "aarch64": {"status": "failed"}},
        },
    },
    {
        "name": "bind_exporter",
        "version": "0.8.0",
        "description": "Prometheus exporter for Bind (DNS) statistics",
        "category": "Network",
        "new": True,
        "updated": True,
        "rpm_status": "failed",
        "docker_status": "success",
        "upstream": {"type": "github", "repo": "prometheus-community/bind_exporter"},
        "artifacts": {
            "rpm": {
                "enabled": True,
                "summary": "Prometheus Bind Exporter",
                "targets": ["el8", "el9", "el10"],
                "system_user": "bind_exporter",
                "service_file": True,
                "extra_files": [],
                "directories": [
                    {
                        "path": "/var/lib/bind_exporter",
                        "owner": "bind_exporter",
                        "group": "bind_exporter",
                        "mode": "0755",
                    }
                ],
            },
            "docker": {
                "enabled": True,
                "entrypoint": ["/usr/bin/bind_exporter"],
                "validation": {"port": 9119},
            },
        },
        "build": {"method": "binary_repack", "binary_name": "bind_exporter"},
        "readme": "# bind_exporter\nRandomized production mock for UI stress-testing.",
        "availability": {
            "el8": {"x86_64": {"status": "na"}, "aarch64": {"status": "na"}},
            "el9": {"x86_64": {"status": "failed"}, "aarch64": {"status": "na"}},
            "el10": {"x86_64": {"status": "na"}, "aarch64": {"status": "success"}},
        },
    },
    {
        "name": "blackbox_exporter",
        "version": "0.28.0",
        "description": "Prometheus blackbox exporter for network probing (HTTP, DNS, TCP, ICMP)",
        "category": "Network",
        "new": False,
        "updated": True,
        "rpm_status": "na",
        "docker_status": "failed",
        "upstream": {"type": "github", "repo": "prometheus/blackbox_exporter"},
        "artifacts": {
            "rpm": {
                "enabled": True,
                "summary": "Prometheus blackbox exporter",
                "targets": ["el8", "el9", "el10"],
                "system_user": "blackbox_exporter",
                "service_file": True,
                "extra_files": [
                    {
                        "source": "assets/blackbox.yml",
                        "dest": "/etc/blackbox_exporter/blackbox.yml",
                        "config": True,
                    }
                ],
                "directories": [
                    {
                        "path": "/etc/blackbox_exporter",
                        "owner": "root",
                        "group": "root",
                        "mode": "0755",
                    },
                    {
                        "path": "/var/lib/blackbox_exporter",
                        "owner": "blackbox_exporter",
                        "group": "blackbox_exporter",
                        "mode": "0755",
                    },
                ],
            },
            "docker": {
                "enabled": True,
                "entrypoint": ["/usr/bin/blackbox_exporter"],
                "cmd": ["--config.file=/etc/blackbox_exporter/blackbox.yml"],
                "validation": {"port": 9115},
            },
        },
        "build": {"method": "binary_repack", "binary_name": "blackbox_exporter"},
        "readme": "# blackbox_exporter\nRandomized production mock for UI stress-testing.",
        "availability": {
            "el8": {"x86_64": {"status": "na"}, "aarch64": {"status": "na"}},
            "el9": {"x86_64": {"status": "success"}, "aarch64": {"status": "failed"}},
            "el10": {"x86_64": {"status": "success"}, "aarch64": {"status": "na"}},
        },
    },
    {
        "name": "eseries_exporter",
        "version": "2.0.0",
        "description": "Prometheus exporter for NetApp/Lenovo E-Series storage systems",
        "category": "Storage",
        "new": False,
        "updated": True,
        "rpm_status": "na",
        "docker_status": "success",
        "upstream": {
            "type": "github",
            "repo": "sckyzo/eseries_exporter",
            "strategy": "latest_release",
            "archive_name": "{name}_linux_{arch}.tar.gz",
        },
        "artifacts": {
            "rpm": {
                "enabled": True,
                "targets": ["el8", "el9", "el10"],
                "summary": "Prometheus exporter for E-Series",
                "service_file": True,
                "system_user": "prometheus",
                "extra_files": [
                    {
                        "source": "assets/eseries_exporter.yml",
                        "dest": "/etc/eseries_exporter/eseries_exporter.yml",
                        "config": True,
                    }
                ],
                "directories": [
                    {
                        "path": "/etc/eseries_exporter",
                        "mode": "0755",
                        "owner": "root",
                        "group": "root",
                    }
                ],
            },
            "docker": {
                "enabled": True,
                "base_image": "registry.access.redhat.com/ubi9/ubi-minimal",
                "entrypoint": ["/usr/bin/eseries_exporter"],
                "cmd": ["--config.file=/etc/eseries_exporter/eseries_exporter.yml"],
                "validation": {"port": 9313},
            },
        },
        "build": {"method": "binary_repack", "binary_name": "eseries_exporter"},
        "readme": "# eseries_exporter\nRandomized production mock for UI stress-testing.",
        "availability": {
            "el8": {"x86_64": {"status": "na"}, "aarch64": {"status": "na"}},
            "el9": {"x86_64": {"status": "na"}, "aarch64": {"status": "success"}},
            "el10": {"x86_64": {"status": "failed"}, "aarch64": {"status": "success"}},
        },
    },
    {
        "name": "gpfs_exporter",
        "version": "3.2.0",
        "description": "Prometheus exporter for IBM GPFS (Spectrum Scale) metrics",
        "category": "Storage",
        "new": False,
        "updated": True,
        "rpm_status": "success",
        "docker_status": "failed",
        "upstream": {
            "type": "github",
            "repo": "treydock/gpfs_exporter",
            "strategy": "latest_release",
        },
        "artifacts": {
            "rpm": {
                "enabled": True,
                "targets": ["el8", "el9", "el10"],
                "summary": "Prometheus exporter for IBM GPFS",
                "service_file": True,
                "system_user": "prometheus",
            },
            "docker": {
                "enabled": True,
                "base_image": "registry.access.redhat.com/ubi9/ubi-minimal",
                "entrypoint": ["/usr/bin/gpfs_exporter"],
                "validation": {"enabled": False},
            },
        },
        "build": {"method": "binary_repack", "binary_name": "gpfs_exporter", "archs": ["amd64"]},
        "readme": "# gpfs_exporter\nRandomized production mock for UI stress-testing.",
        "availability": {
            "el8": {"x86_64": {"status": "na"}, "aarch64": {"status": "success"}},
            "el9": {"x86_64": {"status": "na"}, "aarch64": {"status": "success"}},
            "el10": {"x86_64": {"status": "na"}, "aarch64": {"status": "success"}},
        },
    },
    {
        "name": "ha_cluster_exporter",
        "version": "1.4.0",
        "description": "Prometheus exporter for High Availability clusters (Pacemaker, Corosync)",
        "category": "Infrastructure",
        "new": True,
        "updated": False,
        "rpm_status": "success",
        "docker_status": "failed",
        "upstream": {
            "type": "github",
            "repo": "ClusterLabs/ha_cluster_exporter",
            "strategy": "latest_release",
            "archive_name": "{name}-{arch}.gz",
        },
        "artifacts": {
            "rpm": {
                "enabled": True,
                "targets": ["el8", "el9", "el10"],
                "summary": "Prometheus HA Cluster Exporter",
                "service_file": True,
                "system_user": "prometheus",
            },
            "docker": {
                "enabled": True,
                "base_image": "registry.access.redhat.com/ubi9/ubi-minimal",
                "entrypoint": ["/usr/bin/ha_cluster_exporter"],
                "validation": {"command": "--version"},
            },
        },
        "build": {"method": "binary_repack", "binary_name": "ha_cluster_exporter"},
        "readme": "# ha_cluster_exporter\nRandomized production mock for UI stress-testing.",
        "availability": {
            "el8": {"x86_64": {"status": "success"}, "aarch64": {"status": "failed"}},
            "el9": {"x86_64": {"status": "na"}, "aarch64": {"status": "success"}},
            "el10": {"x86_64": {"status": "failed"}, "aarch64": {"status": "na"}},
        },
    },
    {
        "name": "ipmi_exporter",
        "version": "1.10.1",
        "description": "Prometheus exporter for IPMI devices",
        "category": "Infrastructure",
        "new": False,
        "updated": False,
        "rpm_status": "success",
        "docker_status": "na",
        "upstream": {"type": "github", "repo": "prometheus-community/ipmi_exporter"},
        "artifacts": {
            "rpm": {
                "enabled": True,
                "summary": "Prometheus exporter for IPMI devices",
                "targets": ["el8", "el9", "el10"],
                "dependencies": ["freeipmi"],
                "system_user": "ipmi_exporter",
                "service_file": True,
                "extra_files": [
                    {
                        "source": "assets/ipmi_remote.yml",
                        "dest": "/etc/ipmi_exporter/ipmi_remote.yml",
                        "config": True,
                    }
                ],
                "directories": [
                    {
                        "path": "/var/lib/ipmi_exporter",
                        "owner": "ipmi_exporter",
                        "group": "ipmi_exporter",
                        "mode": "0755",
                    },
                    {
                        "path": "/etc/ipmi_exporter",
                        "owner": "root",
                        "group": "root",
                        "mode": "0755",
                    },
                ],
            },
            "docker": {
                "enabled": True,
                "entrypoint": ["/usr/bin/ipmi_exporter"],
                "cmd": ["--config.file=/etc/ipmi_exporter/ipmi_remote.yml"],
                "validation": {"port": 9290},
            },
        },
        "build": {"method": "binary_repack", "binary_name": "ipmi_exporter"},
        "readme": "# ipmi_exporter\nRandomized production mock for UI stress-testing.",
        "availability": {
            "el8": {"x86_64": {"status": "success"}, "aarch64": {"status": "failed"}},
            "el9": {"x86_64": {"status": "failed"}, "aarch64": {"status": "success"}},
            "el10": {"x86_64": {"status": "failed"}, "aarch64": {"status": "na"}},
        },
    },
    {
        "name": "mysqld_exporter",
        "version": "0.18.0",
        "description": "Prometheus exporter for MySQL server metrics",
        "category": "Database",
        "new": False,
        "updated": False,
        "rpm_status": "success",
        "docker_status": "na",
        "upstream": {"type": "github", "repo": "prometheus/mysqld_exporter"},
        "artifacts": {
            "rpm": {
                "enabled": True,
                "summary": "Prometheus MySQL Exporter",
                "targets": ["el8", "el9", "el10"],
                "system_user": "mysqld_exporter",
                "service_file": True,
                "extra_files": [
                    {
                        "source": "assets/my.cnf",
                        "dest": "/var/lib/mysqld_exporter/.my.cnf",
                        "config": True,
                        "mode": "0600",
                    }
                ],
                "directories": [
                    {
                        "path": "/var/lib/mysqld_exporter",
                        "owner": "mysqld_exporter",
                        "group": "mysqld_exporter",
                        "mode": "0700",
                    }
                ],
            },
            "docker": {
                "enabled": True,
                "entrypoint": ["/usr/bin/mysqld_exporter"],
                "cmd": ["--config.my-cnf=/var/lib/mysqld_exporter/.my.cnf"],
                "validation": {"port": 9104},
            },
        },
        "build": {"method": "binary_repack", "binary_name": "mysqld_exporter"},
        "readme": "# mysqld_exporter\nRandomized production mock for UI stress-testing.",
        "availability": {
            "el8": {"x86_64": {"status": "na"}, "aarch64": {"status": "success"}},
            "el9": {"x86_64": {"status": "success"}, "aarch64": {"status": "failed"}},
            "el10": {"x86_64": {"status": "failed"}, "aarch64": {"status": "failed"}},
        },
    },
    {
        "name": "nginx_exporter",
        "version": "1.5.1",
        "description": "Prometheus exporter for NGINX metrics",
        "category": "Web",
        "new": False,
        "updated": False,
        "rpm_status": "na",
        "docker_status": "na",
        "upstream": {
            "type": "github",
            "repo": "nginx/nginx-prometheus-exporter",
            "archive_name": "nginx-prometheus-exporter_{clean_version}_linux_{arch}.tar.gz",
        },
        "artifacts": {
            "rpm": {
                "enabled": True,
                "summary": "Prometheus Nginx Exporter",
                "targets": ["el8", "el9", "el10"],
                "system_user": "nginx_exporter",
                "service_file": True,
                "extra_files": [],
                "directories": [
                    {
                        "path": "/var/lib/nginx_exporter",
                        "owner": "nginx_exporter",
                        "group": "nginx_exporter",
                        "mode": "0755",
                    }
                ],
            },
            "docker": {
                "enabled": True,
                "entrypoint": ["/usr/bin/nginx_exporter"],
                "validation": {"port": 9113},
            },
        },
        "build": {"method": "binary_repack", "binary_name": "nginx-prometheus-exporter"},
        "readme": "# nginx_exporter\nRandomized production mock for UI stress-testing.",
        "availability": {
            "el8": {"x86_64": {"status": "failed"}, "aarch64": {"status": "success"}},
            "el9": {"x86_64": {"status": "success"}, "aarch64": {"status": "na"}},
            "el10": {"x86_64": {"status": "success"}, "aarch64": {"status": "success"}},
        },
    },
    {
        "name": "node_exporter",
        "version": "1.10.2",
        "description": "Hardware and OS metrics exporter for Prometheus",
        "category": "System",
        "new": False,
        "updated": False,
        "rpm_status": "success",
        "docker_status": "failed",
        "upstream": {
            "type": "github",
            "repo": "prometheus/node_exporter",
            "strategy": "latest_release",
        },
        "artifacts": {
            "rpm": {
                "enabled": True,
                "targets": ["el8", "el9", "el10"],
                "summary": "Prometheus exporter for hardware and OS metrics",
                "service_file": True,
            },
            "docker": {
                "enabled": True,
                "entrypoint": ["/usr/bin/node_exporter"],
                "cmd": [],
                "validation": {"port": 9100},
            },
        },
        "build": {"method": "binary_repack", "binary_name": "node_exporter"},
        "readme": "# node_exporter\nRandomized production mock for UI stress-testing.",
        "availability": {
            "el8": {"x86_64": {"status": "na"}, "aarch64": {"status": "na"}},
            "el9": {"x86_64": {"status": "na"}, "aarch64": {"status": "na"}},
            "el10": {"x86_64": {"status": "failed"}, "aarch64": {"status": "success"}},
        },
    },
    {
        "name": "ping_exporter",
        "version": "1.1.4",
        "description": "Prometheus exporter for ICMP ping metrics",
        "category": "Network",
        "new": False,
        "updated": True,
        "rpm_status": "success",
        "docker_status": "failed",
        "upstream": {
            "type": "github",
            "repo": "czerwonk/ping_exporter",
            "strategy": "latest_release",
            "archive_name": "{name}_{version}_linux_{arch}.tar.gz",
        },
        "artifacts": {
            "rpm": {
                "enabled": True,
                "targets": ["el8", "el9", "el10"],
                "summary": "Prometheus exporter for ICMP ping metrics",
                "service_file": True,
                "system_user": "prometheus",
                "extra_files": [
                    {
                        "source": "assets/ping.yml",
                        "dest": "/etc/ping_exporter/ping.yml",
                        "config": True,
                    }
                ],
                "directories": [
                    {"path": "/etc/ping_exporter", "mode": "0755", "owner": "root", "group": "root"}
                ],
            },
            "docker": {
                "enabled": True,
                "base_image": "registry.access.redhat.com/ubi9/ubi-minimal",
                "entrypoint": ["/usr/bin/ping_exporter"],
                "cmd": ["--config.path=/etc/ping_exporter/ping.yml"],
                "validation": {"port": 9427},
            },
        },
        "build": {"method": "binary_repack", "binary_name": "ping_exporter"},
        "readme": "# ping_exporter\nRandomized production mock for UI stress-testing.",
        "availability": {
            "el8": {"x86_64": {"status": "success"}, "aarch64": {"status": "failed"}},
            "el9": {"x86_64": {"status": "success"}, "aarch64": {"status": "na"}},
            "el10": {"x86_64": {"status": "failed"}, "aarch64": {"status": "failed"}},
        },
    },
    {
        "name": "podman_exporter",
        "version": "1.20.0",
        "description": "Prometheus exporter for Podman containers",
        "category": "System",
        "new": False,
        "updated": False,
        "rpm_status": "failed",
        "docker_status": "failed",
        "upstream": {
            "type": "github",
            "repo": "SckyzO/prometheus-podman-exporter",
            "archive_name": "prometheus-podman-exporter-{version}.linux-{arch}.tar.gz",
        },
        "artifacts": {
            "rpm": {
                "enabled": True,
                "summary": "Prometheus exporter for Podman containers",
                "targets": ["el8", "el9", "el10"],
                "system_user": "prometheus",
                "extra_files": [],
                "directories": [
                    {
                        "path": "/var/lib/prometheus",
                        "owner": "prometheus",
                        "group": "prometheus",
                        "mode": "0755",
                    }
                ],
            },
            "docker": {
                "enabled": True,
                "entrypoint": ["/usr/bin/podman_exporter"],
                "cmd": ["--collector.enable-all"],
                "validation": {"command": "--help"},
            },
        },
        "build": {"method": "binary_repack", "binary_name": "podman_exporter"},
        "readme": "# podman_exporter\nRandomized production mock for UI stress-testing.",
        "availability": {
            "el8": {"x86_64": {"status": "na"}, "aarch64": {"status": "failed"}},
            "el9": {"x86_64": {"status": "na"}, "aarch64": {"status": "failed"}},
            "el10": {"x86_64": {"status": "success"}, "aarch64": {"status": "success"}},
        },
    },
    {
        "name": "process_exporter",
        "version": "0.8.7",
        "description": "Prometheus exporter for process metrics",
        "category": "System",
        "new": False,
        "updated": True,
        "rpm_status": "failed",
        "docker_status": "failed",
        "upstream": {
            "type": "github",
            "repo": "ncabatoff/process-exporter",
            "archive_name": "process-exporter-{clean_version}.linux-{arch}.tar.gz",
        },
        "artifacts": {
            "rpm": {
                "enabled": True,
                "targets": ["el8", "el9", "el10"],
                "summary": "Prometheus exporter for process metrics",
                "service_file": True,
                "system_user": "prometheus",
            },
            "docker": {
                "enabled": True,
                "entrypoint": ["/usr/bin/process_exporter"],
                "validation": {"port": 9256},
            },
        },
        "build": {"method": "binary_repack", "binary_name": "process-exporter"},
        "readme": "# process_exporter\nRandomized production mock for UI stress-testing.",
        "availability": {
            "el8": {"x86_64": {"status": "failed"}, "aarch64": {"status": "na"}},
            "el9": {"x86_64": {"status": "success"}, "aarch64": {"status": "success"}},
            "el10": {"x86_64": {"status": "na"}, "aarch64": {"status": "success"}},
        },
    },
    {
        "name": "prometheus",
        "version": "3.8.1",
        "description": "The Prometheus monitoring system and time series database.",
        "category": "Infrastructure",
        "new": True,
        "updated": False,
        "rpm_status": "na",
        "docker_status": "failed",
        "upstream": {
            "type": "github",
            "repo": "prometheus/prometheus",
            "strategy": "latest_release",
        },
        "artifacts": {
            "rpm": {
                "enabled": True,
                "targets": ["el8", "el9", "el10"],
                "summary": "The Prometheus monitoring system and time series database.",
                "service_file": True,
                "system_user": "prometheus",
                "extra_files": [
                    {
                        "source": "assets/prometheus.yml",
                        "dest": "/etc/prometheus/prometheus.yml",
                        "config": True,
                    }
                ],
                "directories": [
                    {"path": "/etc/prometheus", "mode": "0755", "owner": "root", "group": "root"},
                    {
                        "path": "/var/lib/prometheus",
                        "mode": "0755",
                        "owner": "prometheus",
                        "group": "prometheus",
                    },
                ],
            },
            "docker": {
                "enabled": True,
                "entrypoint": ["/usr/bin/prometheus"],
                "cmd": ["--config.file=/etc/prometheus/prometheus.yml"],
                "validation": {"port": 9090},
            },
        },
        "build": {
            "method": "binary_repack",
            "binary_name": "prometheus",
            "extra_binaries": ["promtool"],
        },
        "readme": "# prometheus\nRandomized production mock for UI stress-testing.",
        "availability": {
            "el8": {"x86_64": {"status": "na"}, "aarch64": {"status": "failed"}},
            "el9": {"x86_64": {"status": "success"}, "aarch64": {"status": "failed"}},
            "el10": {"x86_64": {"status": "success"}, "aarch64": {"status": "failed"}},
        },
    },
    {
        "name": "redis_exporter",
        "version": "1.80.1",
        "description": "Prometheus exporter for Redis metrics",
        "category": "Database",
        "new": False,
        "updated": False,
        "rpm_status": "failed",
        "docker_status": "failed",
        "upstream": {
            "type": "github",
            "repo": "oliver006/redis_exporter",
            "archive_name": "redis_exporter-v{clean_version}.linux-{arch}.tar.gz",
        },
        "artifacts": {
            "rpm": {
                "enabled": True,
                "summary": "Prometheus Redis Exporter",
                "targets": ["el8", "el9", "el10"],
                "system_user": "redis_exporter",
                "service_file": True,
                "extra_files": [],
                "directories": [
                    {
                        "path": "/var/lib/redis_exporter",
                        "owner": "redis_exporter",
                        "group": "redis_exporter",
                        "mode": "0755",
                    }
                ],
            },
            "docker": {
                "enabled": True,
                "entrypoint": ["/usr/bin/redis_exporter"],
                "validation": {"port": 9121},
            },
        },
        "build": {"method": "binary_repack", "binary_name": "redis_exporter"},
        "readme": "# redis_exporter\nRandomized production mock for UI stress-testing.",
        "availability": {
            "el8": {"x86_64": {"status": "success"}, "aarch64": {"status": "na"}},
            "el9": {"x86_64": {"status": "failed"}, "aarch64": {"status": "failed"}},
            "el10": {"x86_64": {"status": "failed"}, "aarch64": {"status": "failed"}},
        },
    },
    {
        "name": "slurm_exporter",
        "version": "1.2.0",
        "description": "Prometheus exporter for Slurm workload manager metrics",
        "category": "Infrastructure",
        "new": True,
        "updated": False,
        "rpm_status": "failed",
        "docker_status": "failed",
        "upstream": {
            "type": "github",
            "repo": "sckyzo/slurm_exporter",
            "strategy": "latest_release",
            "archive_name": "{name}-{clean_version}-linux-{arch}.tar.gz",
        },
        "artifacts": {
            "rpm": {
                "enabled": True,
                "targets": ["el8", "el9", "el10"],
                "summary": "Prometheus exporter for Slurm metrics",
                "service_file": True,
                "system_user": "prometheus",
            },
            "docker": {
                "enabled": True,
                "base_image": "registry.access.redhat.com/ubi9/ubi-minimal",
                "entrypoint": ["/usr/bin/slurm_exporter"],
                "validation": {"port": 9341},
            },
        },
        "build": {"method": "binary_repack", "binary_name": "slurm_exporter"},
        "readme": "# slurm_exporter\nRandomized production mock for UI stress-testing.",
        "availability": {
            "el8": {"x86_64": {"status": "success"}, "aarch64": {"status": "na"}},
            "el9": {"x86_64": {"status": "na"}, "aarch64": {"status": "na"}},
            "el10": {"x86_64": {"status": "na"}, "aarch64": {"status": "failed"}},
        },
    },
    {
        "name": "smartctl_exporter",
        "version": "0.14.0",
        "description": "Prometheus exporter for S.M.A.R.T. storage devices metrics",
        "category": "Storage",
        "new": False,
        "updated": True,
        "rpm_status": "success",
        "docker_status": "success",
        "upstream": {
            "type": "github",
            "repo": "prometheus-community/smartctl_exporter",
            "strategy": "latest_release",
        },
        "artifacts": {
            "rpm": {
                "enabled": True,
                "targets": ["el8", "el9", "el10"],
                "summary": "Prometheus exporter for S.M.A.R.T. metrics",
                "service_file": True,
                "system_user": "root",
            },
            "docker": {
                "enabled": True,
                "base_image": "registry.access.redhat.com/ubi9/ubi-minimal",
                "entrypoint": ["/usr/bin/smartctl_exporter"],
                "validation": {"port": 9633},
            },
        },
        "build": {"method": "binary_repack", "binary_name": "smartctl_exporter"},
        "readme": "# smartctl_exporter\nRandomized production mock for UI stress-testing.",
        "availability": {
            "el8": {"x86_64": {"status": "na"}, "aarch64": {"status": "failed"}},
            "el9": {"x86_64": {"status": "failed"}, "aarch64": {"status": "na"}},
            "el10": {"x86_64": {"status": "success"}, "aarch64": {"status": "success"}},
        },
    },
    {
        "name": "snmp_exporter",
        "version": "0.29.0",
        "description": "Prometheus exporter for SNMP-enabled devices",
        "category": "Network",
        "new": False,
        "updated": True,
        "rpm_status": "na",
        "docker_status": "success",
        "upstream": {
            "type": "github",
            "repo": "prometheus/snmp_exporter",
            "strategy": "latest_release",
        },
        "artifacts": {
            "rpm": {
                "enabled": True,
                "targets": ["el8", "el9", "el10"],
                "summary": "Prometheus exporter for SNMP metrics",
                "service_file": True,
                "system_user": "prometheus",
                "extra_files": [
                    {"source": "snmp.yml", "dest": "/etc/snmp_exporter/snmp.yml", "config": True}
                ],
                "directories": [
                    {"path": "/etc/snmp_exporter", "mode": "0755", "owner": "root", "group": "root"}
                ],
            },
            "docker": {
                "enabled": True,
                "base_image": "registry.access.redhat.com/ubi9/ubi-minimal",
                "entrypoint": ["/usr/bin/snmp_exporter"],
                "cmd": ["--config.file=/etc/snmp_exporter/snmp.yml"],
                "validation": {"port": 9116},
            },
        },
        "build": {
            "method": "binary_repack",
            "binary_name": "snmp_exporter",
            "extra_sources": [
                {
                    "url": "https://raw.githubusercontent.com/prometheus/snmp_exporter/refs/heads/main/snmp.yml",
                    "filename": "snmp.yml",
                }
            ],
        },
        "readme": "# snmp_exporter\nRandomized production mock for UI stress-testing.",
        "availability": {
            "el8": {"x86_64": {"status": "failed"}, "aarch64": {"status": "na"}},
            "el9": {"x86_64": {"status": "success"}, "aarch64": {"status": "success"}},
            "el10": {"x86_64": {"status": "na"}, "aarch64": {"status": "success"}},
        },
    },
    {
        "name": "textfile_exporter",
        "version": "0.1.4",
        "description": "Prometheus exporter for local text files metrics",
        "category": "System",
        "new": False,
        "updated": False,
        "rpm_status": "success",
        "docker_status": "failed",
        "upstream": {
            "type": "github",
            "repo": "SckyzO/textfile_exporter",
            "archive_name": "textfile_exporter-{clean_version}-linux-{arch}.tar.gz",
        },
        "artifacts": {
            "rpm": {
                "enabled": True,
                "summary": "Prometheus Textfile Exporter",
                "targets": ["el8", "el9", "el10"],
                "system_user": "textfile_exporter",
                "service_file": True,
                "extra_files": [],
                "directories": [
                    {
                        "path": "/var/lib/textfile_exporter",
                        "owner": "textfile_exporter",
                        "group": "textfile_exporter",
                        "mode": "0755",
                    }
                ],
            },
            "docker": {
                "enabled": True,
                "entrypoint": ["/usr/bin/textfile_exporter"],
                "cmd": ["--textfile.directory=/var/lib/textfile_exporter"],
                "validation": {"port": 9014},
            },
        },
        "build": {"method": "binary_repack", "binary_name": "textfile_exporter"},
        "readme": "# textfile_exporter\nRandomized production mock for UI stress-testing.",
        "availability": {
            "el8": {"x86_64": {"status": "failed"}, "aarch64": {"status": "failed"}},
            "el9": {"x86_64": {"status": "na"}, "aarch64": {"status": "na"}},
            "el10": {"x86_64": {"status": "success"}, "aarch64": {"status": "na"}},
        },
    },
]
MOCK_CATEGORIES = ["Database", "Infrastructure", "Network", "Storage", "System", "Web"]


@click.command()
@click.option(
    "--start-webserver", is_flag=True, help="Start a local webserver to preview the site."
)
def render(start_webserver):
    from jinja2 import Environment, FileSystemLoader

    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("index.html.j2")

    output = template.render(
        exporters=MOCK_EXPORTERS,
        exporters_json=json.dumps(MOCK_EXPORTERS),
        categories_json=json.dumps(MOCK_CATEGORIES),
        core_version="v0.16.0",
        portal_version="v2.8.0",
    )

    with open("index.html", "w") as f:
        f.write(output)
    print("✅ index.html generated with full randomized production mocks.")

    if start_webserver:
        print("🚀 Starting webserver on port 8080...")
        os.system("python3 -m http.server 8080")


if __name__ == "__main__":
    render()
