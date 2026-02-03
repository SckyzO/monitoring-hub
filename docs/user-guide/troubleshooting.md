# Troubleshooting

Common issues and solutions when working with Monitoring Hub.

## Installation Issues

### DNF Repository Not Found

**Problem:** `Error: Failed to download metadata for repo`

**Solution:**

```bash
# Clear DNF cache
sudo dnf clean all

# Reconfigure repo
sudo dnf config-manager --add-repo https://sckyzo.github.io/monitoring-hub/el9/$(arch)/
```

### GPG Signature Verification Failed

**Problem:** Packages fail signature verification

**Solution:** Packages are not signed. Disable GPG check:

```bash
sudo dnf install --nogpgcheck node_exporter
```

## Build Issues

### Binary Not Found in Archive

**Problem:** `Warning: Binary 'my_exporter' not found`

**Solution:** Check the archive structure and update `archive_name` pattern:

```bash
# Check actual archive structure
curl -L https://github.com/owner/repo/releases/download/v1.0.0/archive.tar.gz | tar -tzf - | head
```

### Version Mismatch

**Problem:** Wrong version is downloaded

**Solution:** Update manifest version and ensure it matches upstream tag format (with or without `v` prefix).

### Architecture Not Available

**Problem:** Build fails for ARM64

**Solution:** Check if upstream provides ARM64 binaries. Update manifest `archs` if needed.

## Runtime Issues

### Service Won't Start

**Problem:** `systemctl start my_exporter` fails

**Solution:**

```bash
# Check service status
sudo systemctl status my_exporter

# Check logs
sudo journalctl -u my_exporter -n 50

# Test binary manually
sudo -u my_exporter /usr/bin/my_exporter --help
```

### Port Already in Use

**Problem:** Exporter can't bind to port

**Solution:**

```bash
# Find what's using the port
sudo lsof -i :9100

# Change port in config or systemd override
sudo systemctl edit my_exporter
```

### Permission Issues

**Problem:** Exporter can't read/write files

**Solution:**

```bash
# Check file permissions
ls -la /etc/my_exporter/
ls -la /var/lib/my_exporter/

# Fix ownership
sudo chown -R my_exporter:my_exporter /var/lib/my_exporter/
```

## Docker Issues

### Image Pull Failed

**Problem:** Can't pull from GHCR

**Solution:**

```bash
# Ensure you're authenticated
docker login ghcr.io

# Or use public access (no auth needed for public images)
docker pull ghcr.io/sckyzo/monitoring-hub/node_exporter:latest
```

### Container Exits Immediately

**Problem:** Container starts then stops

**Solution:**

```bash
# Check container logs
docker logs my_exporter

# Run interactively for debugging
docker run -it --entrypoint /bin/sh ghcr.io/sckyzo/monitoring-hub/my_exporter:latest
```

## Development Issues

### Tests Failing

**Problem:** `pytest` fails

**Solution:**

```bash
# Ensure PYTHONPATH is set
export PYTHONPATH=$(pwd)

# Run with verbose output
pytest -vv

# Run specific test
pytest core/tests/test_builder.py::test_load_valid_manifest
```

### Pre-commit Hooks Failing

**Problem:** `pre-commit run` fails

**Solution:**

```bash
# Update hooks
pre-commit autoupdate

# Run on all files
pre-commit run --all-files

# Skip hooks if needed (not recommended)
git commit --no-verify
```

## Getting Help

If your issue isn't covered here:

1. Check [GitHub Issues](https://github.com/SckyzO/monitoring-hub/issues)
2. Review [GitHub Actions](https://github.com/SckyzO/monitoring-hub/actions) logs
3. Open a new issue with details
