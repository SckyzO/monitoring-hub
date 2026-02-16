# V3 Migration Guide

This guide helps you migrate from V2 (legacy) catalog format to V3 (granular) architecture.

## Overview

### What Changed in V3?

**V2 (Legacy):**
- Single `catalog.json` file updated by all jobs
- Race conditions in parallel builds
- Monolithic artifact metadata
- Write-time aggregation

**V3 (Granular):**
- Atomic artifact files: `catalog/<exporter>/rpm_<arch>_<dist>.json`
- No race conditions (1 job = 1 file)
- Granular per-artifact metadata
- Read-time aggregation

### Why Migrate?

✅ **Reliability:** No race conditions in parallel builds
✅ **Scalability:** Hundreds of parallel jobs without conflicts
✅ **Observability:** Individual artifact status tracking
✅ **Performance:** Faster builds (no catalog.json lock)
✅ **Maintainability:** Clear separation of concerns

## Migration Checklist

### For Repository Maintainers

- [x] Phase 1: Implement V3 catalog architecture (DONE)
  - [x] Create generate_artifact_metadata.py
  - [x] Create aggregate_catalog_metadata.py
  - [x] Create publish_artifact_metadata.sh
  - [x] Create site_generator_v2.py

- [x] Phase 2: Workflow simplification (DONE)
  - [x] Update release.yml with atomic writes
  - [x] Update auto-release.yml with state_manager
  - [x] Consolidate update-portal.yml
  - [x] Update build-pr.yml with detect-changes
  - [x] Update full-build.yml with site_generator_v2

- [x] Phase 3: Testing and validation (DONE)
  - [x] Add test_artifact_schemas.py
  - [x] Add test_aggregation.py
  - [x] Add test_site_generator.py
  - [x] Create Docker-based test infrastructure

- [ ] Phase 4: Documentation updates (IN PROGRESS)
  - [x] Update CLAUDE.md with V3 patterns
  - [x] Update README.md with V3 architecture
  - [x] Create catalog-v3.md API reference
  - [x] Update ci-cd.md workflow documentation
  - [ ] Create v3-migration-guide.md (this file)

- [ ] Phase 5: Deployment and monitoring
  - [ ] Deploy to production (merge to main)
  - [ ] Monitor first V3 builds
  - [ ] Verify backward compatibility
  - [ ] Clean up V2 legacy code (optional)

### For Portal Consumers

If you consume the catalog programmatically, follow this guide to migrate your code.

### For Fork Maintainers

If you maintain a fork, see the "Migrating Your Fork" section below.

## Code Migration Examples

### Python: Reading Catalog

#### Before V3 (Legacy Format)

```python
import requests

# Read monolithic catalog.json
catalog_url = "https://sckyzo.github.io/monitoring-hub/catalog.json"
catalog = requests.get(catalog_url).json()

# Iterate exporters
for exporter in catalog["exporters"]:
    name = exporter["name"]
    version = exporter["version"]
    rpm_status = exporter["rpm_status"]

    # Check availability
    if "el9" in exporter.get("availability", {}):
        rpm_url = exporter["availability"]["el9"]["x86_64"]["path"]
        print(f"{name} v{version}: {rpm_url}")
```

#### After V3 (Granular Format)

**Option 1: Use aggregated metadata.json (Recommended)**

```python
import requests

# Read exporter-specific metadata (aggregated)
metadata_url = "https://sckyzo.github.io/monitoring-hub/catalog/node_exporter/metadata.json"
metadata = requests.get(metadata_url).json()

# Check format version
if metadata["format_version"] != "3.0":
    raise ValueError("Unexpected format version")

# Access artifact data
rpm_status = metadata["status"]["rpm"]
rpm_artifacts = metadata["artifacts"]["rpm"]

# Get specific artifact
if "el9" in rpm_artifacts and "amd64" in rpm_artifacts["el9"]:
    artifact = rpm_artifacts["el9"]["amd64"]
    rpm_url = artifact["url"]
    print(f"{metadata['exporter']} v{metadata['version']}: {rpm_url}")
```

**Option 2: Read granular artifacts directly (Advanced)**

```python
import requests

# Read specific artifact file
artifact_url = "https://sckyzo.github.io/monitoring-hub/catalog/node_exporter/rpm_amd64_el9.json"
artifact = requests.get(artifact_url).json()

# Validate format
assert artifact["format_version"] == "3.0"
assert artifact["artifact_type"] == "rpm"

# Access package details
if artifact["status"] == "success":
    package = artifact["package"]
    print(f"Filename: {package['filename']}")
    print(f"URL: {package['url']}")
    print(f"SHA256: {package['sha256']}")
    print(f"Size: {package['size_bytes']} bytes")
```

### JavaScript/TypeScript: Portal Integration

#### Before V3 (Legacy Format)

```javascript
// Fetch catalog
const response = await fetch('https://sckyzo.github.io/monitoring-hub/catalog.json');
const catalog = await response.json();

// Display exporters
catalog.exporters.forEach(exporter => {
  const statusBadge = exporter.rpm_status === 'success' ? '✅' : '❌';
  console.log(`${statusBadge} ${exporter.name} v${exporter.version}`);

  // Show availability
  if (exporter.availability?.el9?.x86_64) {
    console.log(`  RPM: ${exporter.availability.el9.x86_64.path}`);
  }
});
```

#### After V3 (Granular Format)

```typescript
interface V3Metadata {
  format_version: string;
  exporter: string;
  version: string;
  category: string;
  description: string;
  last_updated: string;
  artifacts: {
    rpm: Record<string, Record<string, ArtifactInfo>>;
    deb: Record<string, Record<string, ArtifactInfo>>;
    docker: DockerInfo;
  };
  status: {
    rpm: ArtifactStatus;
    deb: ArtifactStatus;
    docker: ArtifactStatus;
  };
}

interface ArtifactInfo {
  status: ArtifactStatus;
  url: string;
  size_bytes: number;
  sha256: string;
}

type ArtifactStatus = 'success' | 'failed' | 'pending' | 'na';

// Fetch exporter metadata
async function loadExporterMetadata(exporterName: string): Promise<V3Metadata> {
  const url = `https://sckyzo.github.io/monitoring-hub/catalog/${exporterName}/metadata.json`;
  const response = await fetch(url);
  const metadata: V3Metadata = await response.json();

  // Validate format version
  if (metadata.format_version !== '3.0') {
    throw new Error(`Unsupported format version: ${metadata.format_version}`);
  }

  return metadata;
}

// Display exporter
async function displayExporter(exporterName: string) {
  const metadata = await loadExporterMetadata(exporterName);

  const statusBadge = metadata.status.rpm === 'success' ? '✅' : '❌';
  console.log(`${statusBadge} ${metadata.exporter} v${metadata.version}`);

  // Show availability
  const rpmArtifacts = metadata.artifacts.rpm;
  if (rpmArtifacts.el9?.amd64) {
    console.log(`  RPM (el9/amd64): ${rpmArtifacts.el9.amd64.url}`);
  }
}
```

### Bash: Downloading Artifacts

#### Before V3 (Legacy Format)

```bash
#!/bin/bash
set -euo pipefail

CATALOG_URL="https://sckyzo.github.io/monitoring-hub/catalog.json"
EXPORTER_NAME="node_exporter"

# Download and parse catalog
catalog=$(curl -fsSL "$CATALOG_URL")

# Extract RPM URL (requires jq)
rpm_url=$(echo "$catalog" | jq -r \
  ".exporters[] | select(.name == \"$EXPORTER_NAME\") | .availability.el9.x86_64.path")

# Download RPM
curl -fsSL -O "$rpm_url"
```

#### After V3 (Granular Format)

```bash
#!/bin/bash
set -euo pipefail

CATALOG_BASE="https://sckyzo.github.io/monitoring-hub/catalog"
EXPORTER_NAME="node_exporter"
ARCH="amd64"
DIST="el9"

# Option 1: Use aggregated metadata
metadata_url="${CATALOG_BASE}/${EXPORTER_NAME}/metadata.json"
metadata=$(curl -fsSL "$metadata_url")

# Extract RPM URL
rpm_url=$(echo "$metadata" | jq -r \
  ".artifacts.rpm.${DIST}.${ARCH}.url")

# Download RPM
curl -fsSL -O "$rpm_url"

# Option 2: Use granular artifact directly
artifact_url="${CATALOG_BASE}/${EXPORTER_NAME}/rpm_${ARCH}_${DIST}.json"
artifact=$(curl -fsSL "$artifact_url")

# Extract package details
rpm_url=$(echo "$artifact" | jq -r '.package.url')
sha256=$(echo "$artifact" | jq -r '.package.sha256')

# Download and verify
curl -fsSL -O "$rpm_url"
filename=$(basename "$rpm_url")
echo "${sha256}  ${filename}" | sha256sum -c
```

## CI/CD Migration

### GitHub Actions: Artifact Publishing

#### Before V3 (Legacy - Race Conditions!)

```yaml
# ⚠️ DANGER: Multiple jobs write to same file
- name: Update catalog (UNSAFE)
  run: |
    # Clone gh-pages
    git clone --depth=1 -b gh-pages https://github.com/user/repo.git gh-pages
    cd gh-pages

    # Update catalog.json (RACE CONDITION!)
    jq '.exporters += [{"name": "node_exporter", ...}]' catalog.json > tmp
    mv tmp catalog.json

    # Commit and push (can fail with conflicts)
    git add catalog.json
    git commit -m "Update catalog"
    git push
```

#### After V3 (Atomic Writes - Safe!)

```yaml
# ✅ SAFE: Each job writes exactly 1 file
- name: Generate artifact metadata
  run: |
    python3 core/scripts/generate_artifact_metadata.py \
      --type rpm \
      --exporter node_exporter \
      --version 1.10.2 \
      --arch amd64 \
      --dist el9 \
      --filename node_exporter-1.10.2-1.el9.x86_64.rpm \
      --url https://example.com/node_exporter.rpm \
      --sha256 abc123... \
      --size 12345678 \
      --status success \
      --output catalog/node_exporter/rpm_amd64_el9.json

- name: Publish artifact metadata
  run: |
    bash core/scripts/publish_artifact_metadata.sh \
      catalog/node_exporter/rpm_amd64_el9.json
```

### GitLab CI: Migration Example

#### Before V3

```yaml
publish-catalog:
  stage: deploy
  script:
    # Download catalog (sequential bottleneck)
    - wget https://example.com/catalog.json

    # Update catalog (not atomic)
    - jq '.exporters += [...]' catalog.json > tmp
    - mv tmp catalog.json

    # Upload (can fail with concurrent builds)
    - rsync -avz catalog.json user@server:/var/www/
```

#### After V3

```yaml
publish-rpm-metadata:
  stage: deploy
  script:
    # Generate granular artifact file
    - python3 generate_artifact_metadata.py \
        --type rpm --arch amd64 --dist el9 \
        --output rpm_amd64_el9.json

    # Upload atomic file (parallel safe)
    - rsync -avz rpm_amd64_el9.json \
        user@server:/var/www/catalog/node_exporter/

# Separate job for aggregation (runs after all artifacts)
aggregate-metadata:
  stage: finalize
  needs: [publish-rpm-metadata, publish-deb-metadata, publish-docker-metadata]
  script:
    - python3 aggregate_catalog_metadata.py \
        --exporter node_exporter \
        --output metadata.json
    - rsync -avz metadata.json \
        user@server:/var/www/catalog/node_exporter/
```

## Migrating Your Fork

If you maintain a fork of Monitoring Hub, follow these steps:

### Step 1: Merge V3 Branch

```bash
# Add upstream remote (if not already added)
git remote add upstream https://github.com/SckyzO/monitoring-hub.git

# Fetch V3 branch
git fetch upstream refactor/v2-architecture

# Merge into your main branch
git checkout main
git merge upstream/refactor/v2-architecture

# Resolve conflicts (if any)
# Common conflicts: .github/workflows/, core/scripts/, docs/

# Test locally
./devctl test
./devctl ci

# Push to your fork
git push origin main
```

### Step 2: Update Secrets

V3 uses the same secrets as V2, no changes required:

- `GPG_PRIVATE_KEY` - GPG signing key
- `GPG_PASSPHRASE` - GPG key passphrase
- `GPG_KEY_ID` - GPG key ID
- `GITHUB_TOKEN` - GitHub API token (automatic)

### Step 3: Update Workflow Permissions

Ensure `gh-pages` branch has write permissions:

```yaml
# .github/workflows/release.yml
permissions:
  contents: write
  packages: write
```

### Step 4: Test First Build

Trigger a manual build to verify V3 works:

1. Go to Actions → auto-release.yml → Run workflow
2. Specify a single exporter (e.g., `node_exporter`)
3. Monitor build logs for atomic metadata publishing
4. Verify catalog structure on gh-pages:
   ```
   catalog/node_exporter/
   ├── rpm_amd64_el9.json
   ├── deb_amd64_ubuntu-22.04.json
   ├── docker.json
   └── metadata.json
   ```

### Step 5: Enable V3 for All Exporters

Once verified, enable V3 for all exporters:

1. Merge V3 branch to main
2. Push to your fork
3. V3 workflows will automatically handle all builds

## Backward Compatibility

### Portal Compatibility

V3 maintains backward compatibility with V2 consumers:

```python
# Legacy code still works!
catalog_url = "https://sckyzo.github.io/monitoring-hub/catalog.json"
catalog = requests.get(catalog_url).json()

# V3 automatically converts granular artifacts to legacy format
for exporter in catalog["exporters"]:
    print(exporter["name"], exporter["version"])
```

**How?** The `site_generator_v2.py` script:
1. Reads V3 granular artifacts
2. Aggregates metadata
3. Converts to V2 legacy format
4. Generates backward-compatible `catalog.json`

### API Compatibility Matrix

| Consumer | V2 Catalog | V3 Catalog | Status |
|----------|-----------|-----------|--------|
| Legacy portal (reads catalog.json) | ✅ | ✅ | Fully compatible |
| V3-aware portal (reads metadata.json) | ❌ | ✅ | V3 only |
| Direct artifact consumers | ❌ | ✅ | V3 only |
| Package managers (YUM/APT) | ✅ | ✅ | No changes |
| Container registries (ghcr.io) | ✅ | ✅ | No changes |

### Deprecation Timeline

V2 legacy format support:

- **Q1 2026:** V3 release (backward compatible)
- **Q2-Q3 2026:** V3 stable period, V2 format maintained
- **Q4 2026:** V2 format deprecation warning
- **Q1 2027:** V2 format removal (V3 only)

Consumers have **1 year** to migrate to V3 format.

## Troubleshooting

### Issue: Race condition errors in logs

**Symptoms:**
```
Error: failed to push some refs to 'https://github.com/user/repo.git'
hint: Updates were rejected because the tip of your current branch is behind
```

**Cause:** Multiple jobs writing to same file (V2 behavior)

**Solution:** Ensure all jobs use V3 atomic writes (generate_artifact_metadata.py)

### Issue: Missing metadata.json files

**Symptoms:**
```
FileNotFoundError: catalog/node_exporter/metadata.json not found
```

**Cause:** Aggregation step not run

**Solution:**
```bash
# Run aggregation manually
python3 core/scripts/aggregate_catalog_metadata.py \
  --exporter node_exporter \
  --catalog-dir catalog \
  --manifest-path exporters/node_exporter/manifest.yaml \
  --output catalog/node_exporter/metadata.json
```

Or trigger update-portal.yml workflow to aggregate all exporters.

### Issue: Format version mismatch

**Symptoms:**
```
ValueError: Expected format_version 3.0, got 2.0
```

**Cause:** Old artifact file from V2 build

**Solution:**
1. Force rebuild exporter: `./devctl test-exporter node_exporter`
2. Trigger full-build.yml workflow
3. Clean gh-pages branch and rebuild all

### Issue: Catalog.json still shows old versions

**Symptoms:** Portal displays outdated versions

**Cause:** Portal cache or aggregation not run

**Solution:**
1. Trigger update-portal.yml workflow
2. Clear browser cache
3. Verify metadata.json files are up to date

## Testing V3 Locally

### Option 1: Docker-based testing

```bash
# Run full test suite
./devctl test

# Run with coverage
./devctl test-cov

# Test specific file
./devctl test tests/test_artifact_schemas.py
```

### Option 2: Manual artifact generation

```bash
# Generate test artifact
python3 core/scripts/generate_artifact_metadata.py \
  --type rpm \
  --exporter test_exporter \
  --version 1.0.0 \
  --arch amd64 \
  --dist el9 \
  --filename test.rpm \
  --url https://example.com/test.rpm \
  --sha256 abc123 \
  --size 1234 \
  --status success \
  --output /tmp/test_rpm.json

# Validate format
cat /tmp/test_rpm.json | jq .

# Aggregate test catalog
mkdir -p /tmp/test_catalog/test_exporter
cp /tmp/test_rpm.json /tmp/test_catalog/test_exporter/

python3 core/scripts/aggregate_catalog_metadata.py \
  --exporter test_exporter \
  --catalog-dir /tmp/test_catalog \
  --manifest-path exporters/node_exporter/manifest.yaml \
  --output /tmp/test_catalog/test_exporter/metadata.json

# Verify aggregation
cat /tmp/test_catalog/test_exporter/metadata.json | jq .
```

### Option 3: End-to-end workflow test

```bash
# Test single exporter build
./devctl test-exporter node_exporter

# Verify V3 artifacts generated
ls -la build/node_exporter/

# Generate portal locally
python3 core/engine/site_generator_v2.py \
  --catalog-dir build/catalog \
  --output-dir build/portal

# Serve portal locally
cd build/portal && python3 -m http.server 8000
# Open http://localhost:8000 in browser
```

## FAQ

### Q: Do I need to update my manifest.yaml files?

**A:** No, manifests are unchanged. V3 only changes internal catalog structure.

### Q: Will my existing packages still work?

**A:** Yes, package URLs and repositories are unchanged. Only catalog format changed.

### Q: Can I roll back to V2 if V3 has issues?

**A:** Yes, V2 code is preserved in git history. Rollback steps:
```bash
git revert <v3-merge-commit>
git push origin main
```

### Q: How do I migrate my custom portal?

**A:** Update your portal code to read V3 metadata.json instead of catalog.json. See "Code Migration Examples" above.

### Q: Are there performance improvements in V3?

**A:** Yes:
- **Faster builds:** No catalog.json lock contention
- **Better parallelism:** Hundreds of jobs without conflicts
- **Incremental updates:** Only changed artifacts regenerated
- **Efficient caching:** Granular artifacts can be cached independently

### Q: What if I only want to use V3 for some exporters?

**A:** V3 is all-or-nothing. Once migrated, all exporters use V3 format. However, you can rebuild individual exporters independently.

## Resources

- [V3 Catalog API Reference](../api-reference/catalog-v3.md)
- [CI/CD Workflow Documentation](ci-cd.md)
- [Refactoring V2 Plan](refactoring-v2-plan.md)
- [State Management](state-management.md)

## Support

If you encounter issues during migration:

1. Check [Troubleshooting](#troubleshooting) section above
2. Review [refactoring-v2-plan.md](refactoring-v2-plan.md) for implementation details
3. Open an issue on GitHub: https://github.com/SckyzO/monitoring-hub/issues
4. Include:
   - Error messages
   - Workflow logs
   - Exporter name
   - Build environment (fork/main repo)
