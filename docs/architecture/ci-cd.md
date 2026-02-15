# CI/CD Workflows

GitHub Actions workflows that power the factory with V3 granular catalog architecture.

## Automated Workflow Chain (V3)

The V3 architecture introduces **atomic writes** and **state-based change detection**:

```
1. scan-updates.yml (CRON daily 6:00 UTC)
   ↓ Detects new versions
   ↓ Creates PRs

2. build-pr.yml (on PR)
   ↓ Validates manifest + canary build
   ↓ Uses detect-changes job

3. (merge to main)
   ↓
   auto-release.yml (on push/manual)
   ↓ Uses state_manager for change detection
   ↓ Triggers release.yml

4. release.yml (matrix build)
   ↓ Builds all changed artifacts
   ↓ Atomic writes: 1 job = 1 file
   ↓ Publishes to gh-pages

5. update-portal.yml
   ↓ Aggregates metadata
   ↓ Regenerates portal
```

## Main Workflows

### release.yml

**Purpose:** Main build pipeline with V3 atomic writes

**Triggers:**
- Manual workflow_call from auto-release.yml
- Manual workflow_dispatch

**Key V3 Changes:**
- **Atomic metadata publishing:** Each job writes exactly 1 JSON file
- **No race conditions:** Parallel jobs safe (rpm_amd64_el9 + rpm_arm64_el9 write different files)
- **Granular artifacts:** `catalog/<exporter>/rpm_<arch>_<dist>.json`
- **Matrix strategy:** Builds all arch/dist combinations in parallel

**Jobs:**
1. **build-rpm:** Build RPM for specific arch/dist combination
   - Downloads binary from upstream
   - Renders spec file from Jinja2 template
   - Builds RPM in Docker (almalinux:9)
   - Signs with GPG
   - Uploads to gh-pages
   - **Publishes atomic metadata:** `generate_artifact_metadata.py` + `publish_artifact_metadata.sh`

2. **build-deb:** Build DEB for specific arch/dist combination
   - Downloads binary from upstream
   - Renders control files from Jinja2 templates
   - Builds DEB in Docker (ubuntu:22.04/debian:12)
   - Signs with GPG
   - Uploads to gh-pages
   - **Publishes atomic metadata:** `generate_artifact_metadata.py` + `publish_artifact_metadata.sh`

3. **build-docker:** Build multi-arch Docker image
   - Uses buildx for multi-platform builds
   - Pushes to ghcr.io
   - **Publishes atomic metadata:** `generate_artifact_metadata.py` + `publish_artifact_metadata.sh`

**Example Atomic Write:**
```yaml
- name: 📦 Publish RPM metadata (amd64/el9)
  run: |
    python3 core/scripts/generate_artifact_metadata.py \
      --type rpm --arch amd64 --dist el9 \
      --exporter node_exporter --version 1.10.2 \
      --filename node_exporter-1.10.2-1.el9.x86_64.rpm \
      --url https://sckyzo.github.io/monitoring-hub/el9/x86_64/... \
      --sha256 abc123 --size 12345678 --status success \
      --output catalog/node_exporter/rpm_amd64_el9.json

    bash core/scripts/publish_artifact_metadata.sh \
      catalog/node_exporter/rpm_amd64_el9.json
```

### scan-updates.yml

**Purpose:** Automated version watcher (CRON daily)

**Triggers:**
- Scheduled: Daily at 6:00 UTC
- Manual workflow_dispatch

**Process:**
1. Runs `watcher.py` to scan all manifests
2. Compares with GitHub API latest releases
3. Creates PRs for outdated exporters
4. PRs trigger build-pr.yml validation

**No V3 changes** (version detection unchanged)

### build-pr.yml

**Purpose:** PR validation with V3 change detection

**Triggers:**
- Pull requests to main branch
- Manual workflow_dispatch

**Key V3 Changes:**
- **detect-changes job:** Identifies modified exporters using git diff
- **Comprehensive summary:** Shows validation results for all exporters
- **Canary build:** Tests reference exporter (node_exporter)

**Jobs:**
1. **detect-changes:** Find modified manifest.yaml files
2. **validate-manifests:** Schema + URL validation for changed exporters
3. **canary-build:** Build node_exporter as smoke test
4. **summary:** Aggregate results and display status

**Example Output:**
```
📋 PR Validation Summary

Modified Exporters:
✅ node_exporter (v1.10.1 → v1.10.2)
✅ postgres_exporter (v0.15.0 → v0.16.0)

Validation Results:
✅ Schema validation: PASSED
✅ URL validation: PASSED
✅ Canary build: SUCCESS
```

### auto-release.yml

**Purpose:** Detects changes and triggers release (V3 state-based)

**Triggers:**
- Push to main branch
- Manual workflow_dispatch (with optional exporter filter)

**Key V3 Changes:**
- **Uses state_manager:** Compares manifest versions vs deployed catalog.json
- **Replaces git diff:** More reliable change detection
- **Smart filtering:** Only builds changed exporters

**Process:**
```bash
# V2 (old): git diff + file parsing
git diff --name-only HEAD~1 exporters/

# V3 (new): state_manager comparison
python3 core/engine/state_manager.py
# Compares:
#   - exporters/node_exporter/manifest.yaml (version: v1.10.2)
#   - https://sckyzo.github.io/monitoring-hub/catalog.json (version: v1.10.1)
# Output: EXPORTERS=node_exporter
```

**Environment Variables:**
- `INPUT_EXPORTERS`: Comma-separated list (manual override)
- `CATALOG_URL`: Override catalog URL (for forks/testing)

### update-portal.yml

**Purpose:** V3 catalog aggregation + portal regeneration

**Triggers:**
- Workflow completion of release.yml
- Manual workflow_dispatch (with --skip-catalog flag)

**Key V3 Changes:**
- **Consolidated workflow:** Replaces update-site.yml + regenerate-portal.yml
- **Uses site_generator_v2.py:** Reads V3 granular catalog structure
- **On-demand aggregation:** Generates metadata.json from granular artifacts

**Jobs:**
1. **aggregate-catalog (optional):**
   - Runs `aggregate_catalog_metadata.py` for each exporter
   - Generates `metadata.json` from granular artifacts
   - Skipped if --skip-catalog flag set

2. **generate-portal:**
   - Runs `site_generator_v2.py` with --catalog-dir parameter
   - Reads V3 catalog structure
   - Converts to legacy format for backward compatibility
   - Generates index.html + catalog.json

**Example:**
```bash
# Full regeneration (with aggregation)
python3 core/scripts/aggregate_catalog_metadata.py \
  --exporter node_exporter \
  --catalog-dir catalog \
  --manifest-path exporters/node_exporter/manifest.yaml \
  --output catalog/node_exporter/metadata.json

# Portal generation
python3 core/engine/site_generator_v2.py \
  --catalog-dir catalog \
  --output-dir portal
```

### full-build.yml

**Purpose:** Force rebuild all exporters (ignores state_manager)

**Triggers:**
- Manual workflow_dispatch only

**Key V3 Changes:**
- **Uses site_generator_v2.py:** V3 catalog support
- **Force rebuild flag:** Sets FORCE_REBUILD=true
- **Ignores state_manager:** Builds everything regardless of changes

**Use Cases:**
- Emergency rebuilds (security patches)
- Catalog corruption recovery
- Testing full pipeline

### security.yml

**Purpose:** Security scanning (no V3 changes)

**Triggers:**
- Pull requests
- Push to main
- Scheduled: Daily

**Scanners:**
- **Bandit**: Python code security issues (SQL injection, hardcoded secrets, insecure functions)
- **pip-audit**: Dependency vulnerability scanning (CVE database)
- **Trivy**: Container image vulnerability scanning with SARIF upload

**Integration:**
- Uploads SARIF reports to GitHub Security tab
- Requires `security-events: write` permission
- Integrates with GitHub Advanced Security
- Fails CI on critical vulnerabilities

**View Results:**
Navigate to **Security** → **Code scanning alerts** in GitHub to view Trivy vulnerability reports.

### security-rebuild.yml

**Purpose:** Emergency rebuild on critical CVE (manual)

**Triggers:**
- Manual workflow_dispatch only

**Process:**
1. Triggers full-build.yml (force rebuild all)
2. Runs security.yml to verify fixes
3. Notifies via GitHub Issues/Discussions

## V3 Workflow Features

- ✅ **Atomic writes:** 1 job = 1 file (no race conditions)
- ✅ **State-based detection:** state_manager replaces git diff
- ✅ **Granular artifacts:** catalog/<exporter>/rpm_<arch>_<dist>.json
- ✅ **On-demand aggregation:** metadata.json generated at read-time
- ✅ **Consolidated workflows:** update-portal.yml replaces 2 workflows
- ✅ **Parallel matrix builds:** Safe concurrent writes
- ✅ **Incremental builds:** Only changed exporters
- ✅ **Automatic deployment:** gh-pages updates
- ✅ **Validation tests:** Schema + URL + canary
- ✅ **Security scanning:** Trivy + Bandit + pip-audit with SARIF
- ✅ **Multi-architecture:** amd64 + arm64 for all artifacts
