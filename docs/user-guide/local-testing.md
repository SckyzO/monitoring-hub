# Local Testing

Learn how to test exporters locally before submitting PRs using our Docker-first workflow.

## Prerequisites

- **Docker** - The only requirement!

## Quick Test (Recommended)

Test an exporter with full RPM + Docker build + validation:

```bash
./devctl test-exporter my_exporter
```

**Or using Make:**
```bash
make test-exporter EXPORTER=my_exporter
```

This automatically:
- ✅ Validates manifest schema
- ✅ Generates build artifacts
- ✅ Builds RPM for EL9/x86_64
- ✅ Builds Docker image
- ✅ Runs smoke tests (if configured)

## Advanced Options

### Test Specific Architecture

```bash
./devctl test-exporter my_exporter --arch arm64
```

Supported architectures: `amd64`, `arm64`

### Test Specific EL Version

```bash
./devctl test-exporter my_exporter --el8   # Enterprise Linux 8
./devctl test-exporter my_exporter --el9   # Enterprise Linux 9 (default)
./devctl test-exporter my_exporter --el10  # Enterprise Linux 10
```

### Test DEB Builds

Test Debian/Ubuntu package build:

```bash
./devctl test-deb my_exporter                    # Ubuntu 22.04 / amd64 (default)
./devctl test-deb my_exporter ubuntu-24.04       # Ubuntu 24.04
./devctl test-deb my_exporter debian-12          # Debian 12
./devctl test-deb my_exporter debian-13 arm64    # Debian 13 / arm64
```

Supported distributions:
- `ubuntu-22.04`, `ubuntu-24.04`
- `debian-12`, `debian-13`

Supported architectures: `amd64`, `arm64`

### Enable Smoke Tests

```bash
./devctl test-exporter my_exporter --smoke
```

Smoke tests verify:
- Container starts successfully
- Metrics endpoint responds with HTTP 200
- Binary version command executes

### Build Docker Image Only

```bash
./devctl test-exporter my_exporter --docker
```

## Build Artifacts Only

If you just need to generate artifacts without building packages:

```bash
./devctl build-exporter my_exporter
```

Output directory: `build/my_exporter/`

Generated files:
- `my_exporter.spec` - RPM spec file
- `Dockerfile` - Container build file
- Binaries and assets

## Manual Build Steps (Advanced)

For debugging, you can run each step inside the development container:

### 1. Open Development Shell

```bash
./devctl shell
```

### 2. Generate Artifacts

```bash
python3 -m core.engine.builder \
  --manifest exporters/my_exporter/manifest.yaml \
  --arch amd64 \
  --output-dir build/my_exporter
```

### 3. Build RPM

```bash
./core/scripts/build_rpm.sh \
  build/my_exporter/my_exporter.spec \
  build/my_exporter/rpms \
  amd64 \
  almalinux:9
```

### 4. Build Docker Image

```bash
docker build -t monitoring-hub/my_exporter:local build/my_exporter
```

### 5. Test Container

```bash
# Start container
docker run -d -p 9100:9100 --name test_exporter \
  monitoring-hub/my_exporter:local

# Check metrics
curl http://localhost:9100/metrics

# Cleanup
docker stop test_exporter && docker rm test_exporter
```

## URL Validation

Validate GitHub release URLs before building:

```bash
# Validate all exporters
make validate-urls

# Validate specific exporter
make validate-url EXPORTER=node_exporter

# With verbose output (show successful URLs)
./devctl validate-urls --verbose

# Test specific architectures only
./devctl validate-urls --arch amd64

# Fail on errors (useful for CI)
./devctl validate-urls --fail-on-error
```

This checks that GitHub release assets are accessible and correctly named:
- ✅ Constructs expected URLs from manifest configuration
- ✅ Tests HTTP accessibility (HEAD requests)
- ✅ Reports success/failed/partial results
- ⚠️ Partial = some architectures missing (often arm64 unavailable upstream)

**When to use:**
- Before building new exporters
- After updating versions in manifests
- When upstream releases change naming patterns
- To debug 404 download errors

## Validation Checklist

The test script automatically validates:

- ✅ Manifest schema is valid (marshmallow validation)
- ✅ Binary downloads successfully from upstream
- ✅ Archive extraction works correctly
- ✅ RPM spec renders without errors
- ✅ RPM builds successfully
- ✅ Docker image builds
- ✅ Container starts (if smoke tests enabled)
- ✅ Metrics endpoint responds (if validation.port configured)
- ✅ Version command succeeds (if validation.command configured)

## Quick Commands Reference

```bash
# List all exporters
./devctl list-exporters

# Build artifacts only
./devctl build-exporter <name>

# Full test with defaults
./devctl test-exporter <name>

# Test with all options
./devctl test-exporter <name> --arch arm64 --el10 --docker --smoke

# Open interactive shell
./devctl shell

# Run Python command
./devctl python -m core.engine.builder --help
```

## Troubleshooting

### Image Not Found

If you see "Development image not found", build it first:

```bash
./devctl build
```

### Permission Denied on RPM Build

Ensure Docker daemon is running and your user has permissions:

```bash
docker ps
```

### Manifest Validation Errors

Check your manifest against the reference:

```bash
# View reference manifest
cat manifest.reference.yaml

# Validate specific manifest
./devctl shell
python3 -m core.engine.schema
```

See [Troubleshooting Guide](troubleshooting.md) for more common issues.

## Next Steps

- [Adding Exporters](adding-exporters.md) - Complete guide
- [Manifest Reference](manifest-reference.md) - Schema documentation
- [Development Guide](../contributing/development.md) - Contributing workflow
