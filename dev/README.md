# dev/ - Local Development Directory

This directory is used for local development, testing, and custom exporters that are not published on GitHub.

## Purpose

The `dev/` directory is **git-ignored** (except for documentation files like this README) and serves as a staging area for:
- Local binaries for testing
- Custom proprietary exporters
- Development prototypes

## Usage

### Testing Local Binaries

1. Place your binary in this directory:
   ```bash
   cp /path/to/my_exporter dev/
   chmod +x dev/my_exporter
   ```

2. **IMPORTANT:** For production exporters, move the binary to the exporter's assets directory:
   ```bash
   mkdir -p exporters/my_exporter/assets
   mv dev/my_exporter exporters/my_exporter/assets/
   ```

3. Reference it in your manifest with a relative path:
   ```yaml
   upstream:
     type: local
     local_binary: assets/my_exporter
   ```

## What Gets Committed

- ✅ `*.md` - Documentation files (like this README)
- ✅ `*.yml.example` - Example configuration files
- ❌ Binaries, executables, and actual config files

## Best Practices

1. **Never commit binaries** - They should remain local or be moved to `exporters/<name>/assets/`
2. **Provide example configs** - Create `.yml.example` files for reference
3. **Document dependencies** - If your binary has special requirements, document them here

## Examples

### Example 1: Custom Python Exporter

```bash
# Place the script
cp rackpower_exporter dev/
cp rackpower.yml dev/rackpower.yml.example

# Create exporter structure
mkdir -p exporters/rackpower_exporter/assets
cp dev/rackpower_exporter exporters/rackpower_exporter/assets/
cp dev/rackpower.yml exporters/rackpower_exporter/assets/
```

### Example 2: Compiled Binary

```bash
# Build your exporter
go build -o dev/my_exporter main.go

# Test it
./dev/my_exporter --version

# Move to production location
mkdir -p exporters/my_exporter/assets
mv dev/my_exporter exporters/my_exporter/assets/
```

## Troubleshooting

**Q: Why is my binary not found during build?**
- A: Ensure the path in the manifest is relative to the manifest location (usually `assets/binary_name`)

**Q: Can I reference files in dev/ from a manifest?**
- A: Yes, but it's not recommended. Use relative paths like `../../../dev/binary` for quick testing, then move to `assets/` for commits.

**Q: Will the watcher update local sources?**
- A: No, local sources (`type: local`) are skipped by the automatic version watcher.
