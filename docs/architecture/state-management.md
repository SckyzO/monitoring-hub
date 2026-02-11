# State Management

How Monitoring Hub tracks and manages exporter versions.

## Catalog System

The catalog uses a **fragmented structure** for efficient incremental publishing:

### Structure

```
/catalog
  ├── index.json           # Lightweight index (4KB)
  ├── node_exporter.json   # Per-exporter details
  ├── prometheus.json
  ├── alertmanager.json
  └── ...
/catalog.json              # Legacy full catalog (217KB, deprecated)
```

### File Purposes

1. **`catalog/index.json`** (Recommended)
   - Lightweight version lookup (4KB)
   - Contains: `name`, `version`, `category`, `last_updated`
   - Used by State Manager for change detection
   - 54x smaller than legacy format

2. **`catalog/{exporter}.json`**
   - Complete metadata for each exporter
   - Availability tracking (RPM/DEB/Docker)
   - Build status and dates
   - Enables incremental updates per exporter

3. **`catalog.json`** (Legacy)
   - Full catalog in single file
   - Maintained for backward compatibility
   - Contains deprecation notice
   - Will be removed in future version

### Configuration

State Manager uses the lightweight index by default:

```python
# core/config/settings.py
DEFAULT_CATALOG_URL = "https://sckyzo.github.io/monitoring-hub/catalog/index.json"
```

Override with environment variable:

```bash
CATALOG_URL=https://custom.domain/catalog.json python -m core.engine.state_manager
```

## Change Detection

State Manager compares:

- **Local manifest versions** (from `exporters/*/manifest.yaml`)
- **Deployed catalog versions** (from `catalog/index.json`)
- **Force rebuild flags** (environment variable)

### Detection Logic

```python
def needs_rebuild(exporter_name, local_version, remote_version):
    # 1. Check force rebuild
    if FORCE_REBUILD:
        return True

    # 2. New exporter (not in remote catalog)
    if remote_version is None:
        return True

    # 3. Version changed
    if local_version != remote_version:
        return True

    return False
```

### Rebuild Matrix

The state manager outputs a JSON array of exporters requiring rebuild:

```json
["node_exporter", "prometheus", "alertmanager"]
```

This array feeds into GitHub Actions matrix strategy for parallel builds.

## Version Comparison

Version format handling:

- Strips `v` prefix for normalization (`v1.0.0` → `1.0.0`)
- Supports semantic versioning (MAJOR.MINOR.PATCH)
- Handles custom version schemes (dates, git SHAs)
- Case-insensitive comparison

### Examples

```python
# Normalized comparison
"v1.0.0" == "1.0.0"  # True (v prefix stripped)
"1.0.0" != "1.0.1"   # True (version changed)
"2.0.0" != "1.9.9"   # True (major bump)
```

## Incremental Publishing

The fragmented catalog enables efficient incremental updates:

1. **Build completes** for `node_exporter`
2. **Generate** `catalog/node_exporter.json` with new data
3. **Regenerate** `catalog/index.json` with updated version
4. **Publish** only changed files to gh-pages
5. **Preserve** unchanged exporter files

### Benefits

- **Reduced bandwidth**: Only upload changed exporters
- **Faster CI/CD**: Skip unchanged catalog entries
- **Atomic updates**: Each exporter independently versioned
- **Parallel builds**: Multiple exporters can publish simultaneously
