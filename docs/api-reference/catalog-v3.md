# V3 Catalog Architecture

## Overview

The V3 catalog architecture introduces **granular artifact files** with **atomic writes** to eliminate race conditions in parallel GitHub Actions builds. Each build job writes exactly one JSON file, ensuring consistency and reliability.

## Directory Structure

```
catalog/
├── <exporter_name>/
│   ├── rpm_<arch>_<dist>.json       # RPM artifact metadata
│   ├── deb_<arch>_<dist>.json       # DEB artifact metadata
│   ├── docker.json                  # Docker image metadata
│   └── metadata.json                # Aggregated metadata (generated on-demand)
└── catalog.json                     # Global index (backward compatible)
```

### Example: node_exporter

```
catalog/node_exporter/
├── rpm_amd64_el9.json
├── rpm_amd64_el10.json
├── rpm_arm64_el9.json
├── rpm_arm64_el10.json
├── deb_amd64_ubuntu-22.04.json
├── deb_amd64_ubuntu-24.04.json
├── deb_amd64_debian-12.json
├── deb_amd64_debian-13.json
├── deb_arm64_ubuntu-22.04.json
├── deb_arm64_ubuntu-24.04.json
├── deb_arm64_debian-12.json
├── deb_arm64_debian-13.json
├── docker.json
└── metadata.json
```

## Artifact File Formats

### RPM Artifact (`rpm_<arch>_<dist>.json`)

```json
{
  "format_version": "3.0",
  "artifact_type": "rpm",
  "exporter": "node_exporter",
  "version": "1.10.2",
  "arch": "amd64",
  "dist": "el9",
  "build_date": "2024-02-13T10:30:00Z",
  "status": "success",
  "package": {
    "filename": "node_exporter-1.10.2-1.el9.x86_64.rpm",
    "url": "https://sckyzo.github.io/monitoring-hub/el9/x86_64/node_exporter-1.10.2-1.el9.x86_64.rpm",
    "sha256": "abc123def456...",
    "size_bytes": 12345678
  },
  "rpm_metadata": {
    "name": "node_exporter",
    "version": "1.10.2",
    "release": "1.el9",
    "arch": "x86_64",
    "summary": "Prometheus exporter for hardware and OS metrics",
    "license": "Apache-2.0",
    "vendor": "Monitoring Hub"
  }
}
```

**Fields:**
- `format_version`: Always "3.0" for V3 artifacts
- `artifact_type`: "rpm", "deb", or "docker"
- `exporter`: Exporter name from manifest
- `version`: Version without 'v' prefix
- `arch`: Architecture (amd64, arm64)
- `dist`: Distribution (el8, el9, el10)
- `build_date`: ISO 8601 timestamp
- `status`: "success", "failed", "pending", or "na"
- `package`: Package file details
- `rpm_metadata`: Extracted RPM metadata (optional, requires rpm tools)

### DEB Artifact (`deb_<arch>_<dist>.json`)

```json
{
  "format_version": "3.0",
  "artifact_type": "deb",
  "exporter": "node_exporter",
  "version": "1.10.2",
  "arch": "amd64",
  "dist": "ubuntu-22.04",
  "build_date": "2024-02-13T10:30:00Z",
  "status": "success",
  "package": {
    "filename": "node-exporter_1.10.2-1_amd64.deb",
    "url": "https://sckyzo.github.io/monitoring-hub/apt/pool/main/n/node-exporter/node-exporter_1.10.2-1_amd64.deb",
    "sha256": "def789ghi012...",
    "size_bytes": 10234567
  },
  "deb_metadata": {
    "package": "node-exporter",
    "version": "1.10.2-1",
    "architecture": "amd64",
    "section": "net",
    "priority": "optional",
    "description": "Prometheus exporter for hardware and OS metrics"
  }
}
```

**Fields:**
- Same as RPM artifact, but with `deb_metadata` instead
- `dist`: Distribution (ubuntu-22.04, ubuntu-24.04, debian-12, debian-13)
- `deb_metadata`: Extracted DEB control file metadata (optional, requires dpkg tools)

### Docker Artifact (`docker.json`)

```json
{
  "format_version": "3.0",
  "artifact_type": "docker",
  "exporter": "node_exporter",
  "version": "1.10.2",
  "build_date": "2024-02-13T10:30:00Z",
  "status": "success",
  "image": {
    "registry": "ghcr.io",
    "repository": "sckyzo/monitoring-hub/node-exporter",
    "tag": "1.10.2",
    "digest": "sha256:abc123def456...",
    "platforms": ["linux/amd64", "linux/arm64"]
  },
  "manifest": {
    "schemaVersion": 2,
    "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
    "config": {
      "digest": "sha256:config123...",
      "size": 1234
    },
    "layers": [
      {
        "digest": "sha256:layer1...",
        "size": 12345678
      }
    ]
  }
}
```

**Fields:**
- `image`: Container image details
- `manifest`: OCI manifest (optional, extracted from registry)

### Aggregated Metadata (`metadata.json`)

Generated on-demand by `aggregate_catalog_metadata.py` from granular artifacts:

```json
{
  "format_version": "3.0",
  "exporter": "node_exporter",
  "version": "1.10.2",
  "category": "System",
  "description": "Hardware and OS metrics",
  "last_updated": "2024-02-13T10:30:00Z",
  "artifacts": {
    "rpm": {
      "el9": {
        "amd64": {
          "status": "success",
          "url": "https://sckyzo.github.io/monitoring-hub/el9/x86_64/node_exporter-1.10.2-1.el9.x86_64.rpm",
          "size_bytes": 12345678,
          "sha256": "abc123..."
        },
        "arm64": {
          "status": "success",
          "url": "https://sckyzo.github.io/monitoring-hub/el9/aarch64/node_exporter-1.10.2-1.el9.aarch64.rpm",
          "size_bytes": 12123456,
          "sha256": "def456..."
        }
      },
      "el10": { ... }
    },
    "deb": {
      "ubuntu-22.04": {
        "amd64": {
          "status": "success",
          "url": "https://sckyzo.github.io/monitoring-hub/apt/pool/main/n/node-exporter/...",
          "size_bytes": 10234567,
          "sha256": "ghi789..."
        },
        "arm64": { ... }
      },
      "debian-12": { ... }
    },
    "docker": {
      "status": "success",
      "registry": "ghcr.io",
      "repository": "sckyzo/monitoring-hub/node-exporter",
      "tag": "1.10.2",
      "digest": "sha256:abc123...",
      "platforms": ["linux/amd64", "linux/arm64"]
    }
  },
  "status": {
    "rpm": "success",
    "deb": "success",
    "docker": "success"
  }
}
```

**Aggregation Logic:**

1. **Load granular artifacts:** Read all `rpm_*.json`, `deb_*.json`, `docker.json`
2. **Group by type:** Organize RPM by dist/arch, DEB by dist/arch
3. **Compute aggregate status:**
   - `success`: At least one artifact succeeded
   - `failed`: All enabled artifacts failed
   - `pending`: Some artifacts still building
   - `na`: Artifact type disabled in manifest
4. **Extract latest timestamp:** Use most recent `build_date` from all artifacts

## Global Catalog (`catalog.json`)

Backward-compatible index of all exporters:

```json
{
  "format_version": "3.0",
  "generated_at": "2024-02-13T12:00:00Z",
  "exporters": [
    {
      "name": "node_exporter",
      "version": "1.10.2",
      "category": "System",
      "description": "Hardware and OS metrics",
      "last_updated": "2024-02-13T10:30:00Z",
      "rpm_status": "success",
      "deb_status": "success",
      "docker_status": "success",
      "metadata_url": "https://sckyzo.github.io/monitoring-hub/catalog/node_exporter/metadata.json"
    },
    ...
  ]
}
```

## V3 Scripts

### generate_artifact_metadata.py

Generates atomic artifact JSON files from build outputs.

**Usage:**
```bash
python3 core/scripts/generate_artifact_metadata.py \
  --type rpm \
  --exporter node_exporter \
  --version 1.10.2 \
  --arch amd64 \
  --dist el9 \
  --filename node_exporter-1.10.2-1.el9.x86_64.rpm \
  --url https://sckyzo.github.io/monitoring-hub/el9/x86_64/node_exporter-1.10.2-1.el9.x86_64.rpm \
  --sha256 abc123... \
  --size 12345678 \
  --status success \
  --output catalog/node_exporter/rpm_amd64_el9.json
```

**Options:**
- `--type`: Artifact type (rpm, deb, docker)
- `--exporter`: Exporter name
- `--version`: Version (without 'v' prefix)
- `--arch`: Architecture (amd64, arm64)
- `--dist`: Distribution (el9, ubuntu-22.04, etc.)
- `--filename`: Package filename
- `--url`: Download URL
- `--sha256`: SHA256 checksum
- `--size`: File size in bytes
- `--status`: Build status (success, failed, pending, na)
- `--output`: Output JSON file path
- `--extract-metadata`: Extract RPM/DEB metadata (requires rpm/dpkg tools)

### aggregate_catalog_metadata.py

Aggregates granular artifact files into `metadata.json`.

**Usage:**
```bash
python3 core/scripts/aggregate_catalog_metadata.py \
  --exporter node_exporter \
  --catalog-dir catalog \
  --manifest-path exporters/node_exporter/manifest.yaml \
  --output catalog/node_exporter/metadata.json
```

**Process:**
1. Load all `rpm_*.json`, `deb_*.json`, `docker.json` from exporter directory
2. Validate format_version and artifact_type
3. Group artifacts by type and platform
4. Compute aggregate status for each type
5. Extract exporter metadata from manifest (category, description, readme)
6. Generate metadata.json with V3.0 format

### publish_artifact_metadata.sh

Publishes atomic artifact files to gh-pages with git operations.

**Usage:**
```bash
bash core/scripts/publish_artifact_metadata.sh \
  catalog/node_exporter/rpm_amd64_el9.json
```

**Process:**
1. Clone gh-pages branch (if not already cloned)
2. Copy artifact JSON to catalog directory
3. Git add the single file
4. Git commit with descriptive message
5. Git push (with retry on conflict)

## Key V3 Principles

### 1. Atomic Writes

Each GitHub Actions job writes **exactly 1 file**:

```yaml
- name: 📦 Publish RPM metadata (amd64/el9)
  run: |
    python3 core/scripts/generate_artifact_metadata.py \
      --type rpm --arch amd64 --dist el9 \
      --output catalog/node_exporter/rpm_amd64_el9.json

    bash core/scripts/publish_artifact_metadata.sh \
      catalog/node_exporter/rpm_amd64_el9.json
```

**No race conditions:** Jobs can run in parallel without conflicts.

### 2. Format Versioning

All files include `"format_version": "3.0"` for future compatibility:

```python
if artifact["format_version"] == "3.0":
    # Use V3 schema
elif artifact["format_version"] == "4.0":
    # Use V4 schema (future)
```

### 3. On-Demand Aggregation

Granular files are the source of truth. Aggregation happens:
- **At read-time** by portal (site_generator_v2.py)
- **On-demand** by aggregate_catalog_metadata.py
- **Never during build** (eliminates concurrent writes)

### 4. Backward Compatibility

`catalog.json` maintains legacy format for existing consumers:

```python
# Legacy consumers still work
catalog = requests.get("https://sckyzo.github.io/monitoring-hub/catalog.json").json()
exporters = catalog["exporters"]

# V3-aware consumers can use granular files
rpm_el9 = requests.get(
    "https://sckyzo.github.io/monitoring-hub/catalog/node_exporter/rpm_amd64_el9.json"
).json()
```

## Migration Guide

### For Portal Consumers

**Before V3:**
```python
# Read catalog.json
catalog = load_catalog()
for exporter in catalog["exporters"]:
    rpm_status = exporter["rpm_status"]
```

**After V3:**
```python
# Option 1: Use aggregated metadata.json (recommended)
metadata = load_metadata("catalog/node_exporter/metadata.json")
rpm_status = metadata["status"]["rpm"]

# Option 2: Read granular artifacts directly
rpm_el9 = load_artifact("catalog/node_exporter/rpm_amd64_el9.json")
if rpm_el9["status"] == "success":
    download_url = rpm_el9["package"]["url"]
```

### For CI Workflows

**Before V3:**
```yaml
- name: Upload catalog
  run: |
    # Danger: Multiple jobs write to catalog.json (race condition!)
    jq '.exporters += [{"name": "..."}]' catalog.json > tmp && mv tmp catalog.json
    git add catalog.json
    git commit -m "Update catalog"
```

**After V3:**
```yaml
- name: Publish artifact metadata
  run: |
    # Safe: Each job writes 1 file (no race condition)
    python3 core/scripts/generate_artifact_metadata.py \
      --type rpm --arch amd64 --dist el9 \
      --output catalog/node_exporter/rpm_amd64_el9.json

    bash core/scripts/publish_artifact_metadata.sh \
      catalog/node_exporter/rpm_amd64_el9.json
```

## Testing

V3 artifacts are validated by comprehensive test suite:

- **test_artifact_schemas.py** (330 lines) - Schema validation for all artifact types
- **test_aggregation.py** (420 lines) - Aggregation logic and status computation
- **test_site_generator.py** (180 lines) - Portal generation and V3→legacy conversion

Run tests:
```bash
./devctl test
./devctl test-cov  # With coverage report
```

## See Also

- [Architecture Overview](../architecture/design.md)
- [Refactoring V2 Plan](../architecture/refactoring-v2-plan.md)
- [State Manager](state-manager.md)
- [Builder](builder.md)
