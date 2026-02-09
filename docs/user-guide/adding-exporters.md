# Adding Exporters

Learn how to add a new Prometheus exporter to the Monitoring Hub.

## Overview

Adding a new exporter is a simple process that takes less than 5 minutes. The factory handles all the complexity of building, packaging, and distributing your exporter.

## Step 1: Create Exporter Scaffold

Use the Docker-first creator tool:

```bash
./devctl create-exporter
```

**Or using Make:**
```bash
make create-exporter
```

You'll be prompted for:

- **Exporter Name:** Technical name (e.g., `redis_exporter`)
- **GitHub Repository:** Upstream repo (e.g., `oliver006/redis_exporter`)
- **Category:** Choose from System, Database, Web, Network, etc.
- **Description:** Short one-liner description

The script will automatically:

- Fetch latest version from GitHub
- Detect supported architectures
- Create `exporters/my_exporter/` directory
- Generate `manifest.yaml` with sensible defaults
- Create `README.md` template
- Create `assets/` directory for config files

**Note:** No Python installation required - everything runs in Docker!

## Step 2: Review and Customize Manifest

Open `exporters/my_exporter/manifest.yaml` and review:

### Basic Information

```yaml
name: my_exporter
description: Exports metrics for My Service
category: Database
version: v1.2.3
# Optional: License will be auto-detected from GitHub if not specified
# license: Apache-2.0
```

**License Auto-Detection:**
The builder automatically queries the GitHub API to detect the upstream project's license (SPDX format). If detection fails or the field is omitted, it defaults to `Apache-2.0`. Common values include:
- `MIT`
- `Apache-2.0`
- `GPL-3.0`
- `BSD-3-Clause`
- `MPL-2.0`

### Upstream Configuration

```yaml
upstream:
  type: github
  repo: owner/my_exporter
  strategy: latest_release
  # Optional: custom archive naming pattern
  archive_name: "{name}-{clean_version}-linux-{arch}.tar.gz"
```

### Build Configuration

```yaml
build:
  method: binary_repack
  binary_name: my_exporter
  archs:
    - amd64
    - arm64
  # Optional: additional binaries from the archive
  extra_binaries: []
  # Optional: extra files to download
  extra_sources: []
```

### RPM Artifacts

```yaml
artifacts:
  rpm:
    enabled: true
    summary: My Service Prometheus Exporter
    targets: [el8, el9, el10]
    systemd:
      enabled: true
      # Optional: command-line arguments
      arguments: ["--config.file=/etc/my_exporter/config.yml"]
    # Optional: config files
    extra_files:
      - source: assets/config.yml
        dest: /etc/my_exporter/config.yml
        mode: "0640"
        config: true
    # Optional: data directories
    directories:
      - path: /var/lib/my_exporter
        owner: my_exporter
        group: my_exporter
    # Optional: system user
    system_user: my_exporter
    # Optional: dependencies
    dependencies: []
```

### Docker Artifacts

```yaml
artifacts:
  docker:
    enabled: true
    base_image: registry.access.redhat.com/ubi9/ubi-minimal:latest
    entrypoint: ["/usr/bin/my_exporter"]
    cmd: []
    validation:
      enabled: true
      port: 9121
```

## Step 3: Add Configuration Files (Optional)

If your exporter needs configuration files:

1. Create files in `exporters/my_exporter/assets/`
2. Reference them in the manifest's `extra_files` section

Example:

```bash
# Create config file
cat > exporters/my_exporter/assets/config.yml << 'EOF'
listen_address: ":9121"
log_level: info
EOF
```

## Step 4: Test Locally

Run the comprehensive test using Docker:

```bash
./devctl test-exporter my_exporter
```

**Or using Make:**
```bash
make test-exporter EXPORTER=my_exporter
```

This will:

- Generate build artifacts
- Build RPM for EL9/x86_64
- Build Docker image
- Run validation tests

For specific options:

```bash
# Test ARM64 build
./devctl test-exporter my_exporter --arch arm64

# Test specific EL version
./devctl test-exporter my_exporter --el10

# Enable smoke tests
./devctl test-exporter my_exporter --smoke
```

**Quick artifact generation only:**
```bash
./devctl build-exporter my_exporter
# Output: build/my_exporter/
```

## Step 5: Create Pull Request

Once local testing passes:

```bash
# Create feature branch
git checkout -b feature/add-my-exporter

# Add files
git add exporters/my_exporter/

# Commit using conventional commits
git commit -m "feat(exporters): add my_exporter support

- Add manifest for my_exporter v1.2.3
- Include default configuration
- Support amd64 and arm64 architectures"

# Push branch
git push origin feature/add-my-exporter
```

Create a Pull Request on GitHub. CI will automatically:

✅ Validate manifest schema  
✅ Build RPM packages (all distros + archs)  
✅ Build Docker images (multi-arch)  
✅ Run validation tests  
✅ Update catalog

## Advanced: Custom Templates

For complex packaging needs, you can override the default templates.

### Custom RPM Spec

Create `exporters/my_exporter/templates/my_exporter.spec.j2`:

```jinja
%define debug_package %{nil}

Name: {{ name }}
Version: {{ version }}
# ... custom spec logic ...

%post
# Custom post-install logic
if [ $1 -eq 1 ]; then
    # First install
    /usr/bin/my_exporter --init-db
fi
```

### Custom Dockerfile

Create `exporters/my_exporter/templates/Dockerfile.j2`:

```dockerfile
FROM {{ artifacts.docker.base_image }}

# Install dependencies
RUN microdnf install -y ca-certificates curl && \
    microdnf clean all

# Copy binary
COPY {{ build.binary_name }} /usr/bin/{{ name }}

# Custom setup
RUN /usr/bin/{{ name }} --version

ENTRYPOINT {{ artifacts.docker.entrypoint | tojson }}
```

## Common Patterns

### Simple Exporter (No Config)

Minimal manifest with just the binary:

```yaml
artifacts:
  rpm:
    enabled: true
    systemd:
      enabled: true
  docker:
    enabled: true
    entrypoint: ["/usr/bin/my_exporter"]
```

### Exporter with Config File

Include configuration management:

```yaml
artifacts:
  rpm:
    system_user: my_exporter
    extra_files:
      - source: assets/config.yml
        dest: /etc/my_exporter/config.yml
        mode: "0640"
        config: true
    systemd:
      arguments: ["--config.file=/etc/my_exporter/config.yml"]
```

### Multi-Binary Package

Include helper tools:

```yaml
build:
  binary_name: main_tool
  extra_binaries:
    - helper_tool
    - cli_tool
```

## Troubleshooting

See [Troubleshooting Guide](troubleshooting.md) for common issues.

## Next Steps

- [Manifest Reference](manifest-reference.md) - Complete manifest documentation
- [Local Testing](local-testing.md) - Advanced testing techniques
- [Contributing Guide](../contributing/development.md) - Development best practices
