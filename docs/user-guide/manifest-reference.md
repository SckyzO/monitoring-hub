# Manifest Reference

Complete reference for the exporter manifest YAML format.

## Quick Example

```yaml
name: my_exporter
description: Exports metrics for My Service
category: Database
version: v1.2.3

upstream:
  type: github
  repo: owner/my_exporter
  strategy: latest_release

build:
  method: binary_repack
  binary_name: my_exporter
  archs: [amd64, arm64]

artifacts:
  rpm:
    enabled: true
    systemd:
      enabled: true
  docker:
    enabled: true
    entrypoint: ["/usr/bin/my_exporter"]
    validation:
      port: 9100
```

## Complete Reference

For the full manifest schema with all available options, see the [manifest.reference.yaml](https://github.com/SckyzO/monitoring-hub/blob/main/manifest.reference.yaml) file in the repository.

## Field Descriptions

### Identity

- `name` (required): Technical name (e.g., `node_exporter`)
- `description` (required): Short description
- `category` (required): System, Database, Web, Network, etc.
- `version` (required): Upstream version (e.g., `v1.2.3`)

### Upstream

- `type`: Always `github`
- `repo` (required): GitHub repository (e.g., `prometheus/node_exporter`)
- `strategy`: `latest_release` (default) or `pinned`
- `archive_name`: Custom archive name pattern (optional)

#### Archive Name Patterns

The `archive_name` field supports two formats for handling non-standard upstream naming:

**1. String Pattern (Most Common)**

Use template variables for simple patterns:

```yaml
archive_name: "{name}-{clean_version}.linux-{arch}.tar.gz"
```

Available variables:
- `{name}`: Exporter name
- `{version}`: Raw version (e.g., v1.0.0)
- `{clean_version}`: Version without 'v' prefix (e.g., 1.0.0)
- `{arch}`: Standard arch (amd64, arm64)
- `{rpm_arch}`: RPM convention (x86_64, aarch64)
- `{deb_arch}`: DEB convention (amd64, arm64)
- `{upstream_linux_arch}`: Mixed convention (x86_64, arm64)

**2. Dict Format (Per-Architecture Patterns)**

Use when upstream has completely different naming per architecture:

```yaml
archive_name:
  amd64: "project-v{clean_version}-x86_64-special.tar.gz"
  arm64: "project-v{clean_version}-arm64-custom.tar.gz"
```

This is useful when:
- Upstream uses inconsistent naming across architectures
- Each architecture has a unique file structure
- Standard variables don't provide enough flexibility

### Build

- `method`: `binary_repack` or `source_build`
- `binary_name` (required): Main binary name
- `archs`: List of architectures (`amd64`, `arm64`)
- `extra_binaries`: Additional binaries to extract
- `extra_sources`: External files to download

### Artifacts - RPM

- `enabled`: Enable RPM generation
- `summary`: Package summary
- `targets`: EL versions (`el8`, `el9`, `el10`)
- `systemd.enabled`: Create systemd service
- `systemd.arguments`: Command-line args
- `system_user`: Create system user
- `extra_files`: Config files to include
- `directories`: Data directories to create
- `dependencies`: Package dependencies

### Artifacts - Docker

- `enabled`: Enable Docker image
- `base_image`: Base container image
- `entrypoint`: Container entrypoint
- `cmd`: Container command
- `validation.enabled`: Enable port validation
- `validation.port`: Port to check

See [Adding Exporters](adding-exporters.md) for practical examples.
