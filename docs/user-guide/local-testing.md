# Local Testing

Learn how to test exporters locally before submitting PRs.

## Quick Test

```bash
./core/scripts/local_test.sh my_exporter
```

## Advanced Options

### Test Specific Architecture

```bash
./core/scripts/local_test.sh my_exporter --arch arm64
```

### Test Specific EL Version

```bash
./core/scripts/local_test.sh my_exporter --el10
```

### Enable Full Validation

```bash
./core/scripts/local_test.sh my_exporter --validate
```

## Manual Build Steps

For debugging, you can run each step individually:

### 1. Generate Artifacts

```bash
export PYTHONPATH=$(pwd)
python3 -m core.engine.builder \
  --manifest exporters/my_exporter/manifest.yaml \
  --arch amd64 \
  --output-dir build/my_exporter
```

### 2. Build RPM

```bash
./core/scripts/build_rpm.sh \
  build/my_exporter/my_exporter.spec \
  build/my_exporter/rpms \
  amd64 \
  almalinux:9
```

### 3. Build Docker

```bash
docker build -t monitoring-hub/my_exporter:local build/my_exporter
```

### 4. Test Docker Container

```bash
docker run -d -p 9100:9100 --name test_exporter monitoring-hub/my_exporter:local
curl http://localhost:9100/metrics
docker stop test_exporter && docker rm test_exporter
```

## Validation

The test script automatically validates:

- ✅ Manifest schema is valid
- ✅ Binaries download successfully
- ✅ RPM builds without errors
- ✅ Docker image builds
- ✅ Container starts and exposes metrics

## Troubleshooting

See [Troubleshooting Guide](troubleshooting.md) for common issues.
