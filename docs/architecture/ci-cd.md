# CI/CD Workflows

GitHub Actions workflows that power the factory with unified build architecture and V3 granular catalog.

## Unified Workflow Architecture

The V3 architecture uses a **single unified build workflow** with **atomic writes** and **state-based change detection**:

```
1. scan-updates.yml (CRON daily 8:00 UTC)
   ↓ Detects new versions
   ↓ Creates PRs

2. build-pr.yml (on PR)
   ↓ Validates manifest + canary build
   ↓ Uses detect-changes job

3. (merge to main)
   ↓
   auto-release.yml (on push/manual)
   ↓ Uses state_manager for change detection
   ↓ Triggers build.yml

4. build.yml (unified workflow)
   ↓ Builds ALL artifacts (RPM + DEB + Docker)
   ↓ Uploads to GitHub Releases
   ↓ Atomic writes: 1 job = 1 file
   ↓ Publishes metadata to gh-pages
   ↓ Generates portal

OR

security-rebuild.yml (CRON Monday 2:00 UTC)
   ↓ Detects new UBI9 base image
   ↓ Triggers build.yml with force_rebuild=true
   ↓ Rebuilds ALL exporters
```

## Main Workflows

### build.yml (Unified Build Workflow)

**Purpose:** Main build pipeline that handles everything (RPM, DEB, Docker, metadata, portal)

**Triggers:**
- workflow_call from auto-release.yml (changed exporters only)
- workflow_call from security-rebuild.yml (all exporters)
- Manual workflow_dispatch

**Input:**
- `exporters`: JSON array of exporter names (e.g., `["node_exporter", "redis_exporter"]`)
- Empty array `[]` = build ALL exporters
- Empty string `""` (default) = auto-detect changed exporters with state_manager

**Key Features:**
- **Unified workflow:** Single workflow handles all build scenarios (1 exporter, N exporters, ALL exporters)
- **Atomic metadata publishing:** Each job writes exactly 1 JSON file
- **No race conditions:** Parallel jobs safe (rpm_amd64_el9 + rpm_arm64_el9 write different files)
- **Granular artifacts:** `catalog/<exporter>/rpm_<arch>_<dist>.json`
- **Matrix strategy:** Builds all arch/dist combinations in parallel
- **Integrated portal generation:** Portal updated after all builds complete

**Jobs:**

1. **discover:** Generate build matrix from input
   - Parses `exporters` input parameter
   - Auto-detects changed exporters if input is empty (using state_manager)
   - Generates matrix for RPM, DEB, and Docker jobs
   - Outputs: `rpm_matrix`, `deb_matrix`, `docker_matrix`

2. **build-rpm:** Build RPM for specific arch/dist combination (parallel)
   - Downloads binary from upstream
   - Renders spec file from Jinja2 template
   - Builds RPM in Docker (almalinux:9 for el8/el9/el10)
   - Signs with GPG
   - Uploads to GitHub Releases
   - **Publishes atomic metadata:** `generate_artifact_metadata.py` + `publish_artifact_metadata.sh`
   - **Output:** `catalog/<exporter>/rpm_<arch>_<dist>.json`

3. **build-deb:** Build DEB for specific arch/dist combination (parallel)
   - Downloads binary from upstream
   - Renders control files from Jinja2 templates
   - Builds DEB in Docker (debian:12 for universal package)
   - Signs with GPG
   - Uploads to GitHub Releases
   - **Publishes atomic metadata:** `generate_artifact_metadata.py` + `publish_artifact_metadata.sh`
   - **Output:** `catalog/<exporter>/deb_<arch>_<dist>.json`

4. **build-docker:** Build multi-arch Docker image (parallel)
   - Uses buildx for multi-platform builds (linux/amd64, linux/arm64)
   - Pushes to ghcr.io
   - Scans with Trivy (security)
   - **Publishes atomic metadata:** `generate_artifact_metadata.py` + `publish_artifact_metadata.sh`
   - **Output:** `catalog/<exporter>/docker.json`

5. **aggregate-security:** Aggregate Trivy scan results (sequential)
   - Collects all security scan results
   - Generates security-stats.json
   - Uploads to gh-pages

6. **publish-metadata-portal:** Generate portal (sequential, after all builds)
   - Downloads ALL metadata artifacts
   - Organizes into `catalog/<exporter>/*.json` structure
   - Aggregates metadata using `aggregate_catalog_metadata.py`
   - Generates portal with `site_generator_v2.py`
   - Pushes to gh-pages (catalog/ + index.html)

**Example Atomic Write:**
```yaml
- name: 📦 Publish RPM metadata (amd64/el9)
  run: |
    python3 core/scripts/generate_artifact_metadata.py \
      --type rpm --arch amd64 --dist el9 \
      --exporter node_exporter --version 1.10.2 \
      --filename node_exporter-1.10.2-1.el9.x86_64.rpm \
      --sha256 $SHA256 --size $SIZE \
      --output artifacts/rpm-node_exporter-amd64-el9/node_exporter/rpm_amd64_el9.json

    bash core/scripts/publish_artifact_metadata.sh \
      artifacts/rpm-node_exporter-amd64-el9
```

**Matrix Strategy:**
```yaml
strategy:
  matrix:
    exporter: ["node_exporter", "redis_exporter", ...]
    arch: ["amd64", "arm64"]
    dist: ["el8", "el9", "el10"]  # For RPM
    # OR
    dist: ["debian-12"]            # For DEB (universal package)
```

**Why Unified?**
- ✅ Simpler mental model (1 main workflow vs 5 chained workflows)
- ✅ Faster debugging (everything in one workflow run)
- ✅ No concurrency bottlenecks
- ✅ No race conditions
- ✅ Atomic operation (all or nothing)
- ✅ Consistent behavior across all scenarios

---

### auto-release.yml

**Purpose:** Detect changed exporters and trigger build.yml

**Triggers:**
- push to main (exporters/*)
- Manual workflow_dispatch

**Key Features:**
- **State-based detection:** Uses state_manager to compare manifests with deployed catalog
- **Smart filtering:** Only builds exporters that actually changed
- **Force rebuild:** Manual trigger with empty input builds ALL exporters

**Jobs:**

1. **detect-changes:** Detect changed exporters
   - If manual trigger with specific exporters: Use provided list
   - If manual trigger with empty input: Set FORCE_REBUILD=true
   - If automatic (push): Use state_manager for change detection
   - Output: JSON array of exporter names

2. **trigger-releases:** Trigger build.yml
   - Calls build.yml with `exporters` parameter
   - Passes force_rebuild flag if applicable

**Example:**
```bash
# User edits exporters/node_exporter/manifest.yaml
git commit -m "feat: update node_exporter to v1.11.0"
git push origin main

# auto-release.yml detects 1 changed exporter
# Triggers: build.yml --raw-field exporters='["node_exporter"]'
```

---

### security-rebuild.yml

**Purpose:** Rebuild all exporters when security updates are available

**Triggers:**
- CRON: Monday at 2:00 UTC
- Manual workflow_dispatch

**Key Features:**
- **UBI9 detection:** Checks if new ubi9-minimal base image is available
- **Force rebuild:** Rebuilds ALL exporters regardless of state_manager
- **Security-first:** Ensures all containers use latest secure base image

**Jobs:**

1. **check-ubi9-update:** Check for new UBI9 base image
   - Pulls latest ubi9-minimal digest
   - Compares with previous build
   - Outputs: `rebuild_needed=true/false`

2. **trigger-rebuild:** Trigger build.yml with force_rebuild
   - Calls build.yml with empty exporters array (= ALL)
   - Sets force_rebuild=true to ignore state_manager

---

### build-pr.yml

**Purpose:** Validate PRs before merge

**Triggers:**
- pull_request (exporters/*)

**Key Features:**
- **Fast validation:** Only validates changed exporters
- **Canary build:** Builds node_exporter as smoke test
- **Comprehensive checks:** Linting + schema validation + build test

**Jobs:**

1. **detect-changes:** Detect which exporters changed in PR
   - Uses git diff to identify modified manifests
   - Output: JSON array of changed exporters

2. **validate-manifests:** Validate YAML syntax and schema
   - Runs yamllint on all manifests
   - Validates with marshmallow schema

3. **lint-python:** Run ruff linter on Python code

4. **lint-css:** Run stylelint on portal templates

5. **canary-build:** Build node_exporter as smoke test
   - Tests that build pipeline is functional
   - Catches breaking changes early

---

### scan-updates.yml

**Purpose:** Automated version watcher

**Triggers:**
- CRON: Daily at 8:00 UTC
- Manual workflow_dispatch

**Key Features:**
- **GitHub API integration:** Checks latest releases for all exporters
- **Version comparison:** Uses `packaging.version` for semantic versioning
- **Automated PRs:** Creates PR when new version detected

**Jobs:**

1. **scan-versions:** Scan all exporters for updates
   - Reads all manifests
   - Queries GitHub API for latest releases
   - Compares versions
   - Creates PR if update available

---

## Legacy Workflows (Disabled)

The following workflows have been **disabled** (renamed to `.disabled`) as they are now integrated into `build.yml`:

- `build-legacy.yml.disabled` - Old single-exporter build
- `full-build.yml.disabled` - Batch build (logic merged into build.yml)
- `upload-releases.yml.disabled` - Upload step (now integrated)
- `catalog-update.yml.disabled` - Catalog update (now integrated)
- `update-portal.yml.disabled` - Portal update (now integrated)

**Why they were removed:**
- Fragile workflow chains (build → upload → catalog → portal)
- Concurrency bottlenecks (upload-releases had concurrency:1)
- Race conditions (catalog-update could be triggered 34× in parallel)
- Architecture confusion (build.yml for 1, full-build.yml for N)

**Solution:** One unified build.yml that does everything atomically.

---

## Workflow Comparison

### Before (Fragmented)

```
security-rebuild.yml
  └─> Triggers 34× build.yml in parallel
        └─> Each triggers upload-releases.yml (concurrency:1)
              └─> 33 triggers lost/cancelled ❌
                    └─> Packages built but catalog never updated
```

### After (Unified)

```
security-rebuild.yml
  └─> Triggers 1× build.yml with exporters=[]
        └─> Builds ALL 34 exporters in one workflow run
              └─> Uploads in parallel (no concurrency limit)
                    └─> Catalog + portal updated atomically ✅
```

---

## State Management

All change detection uses `core/engine/state_manager.py`:

**How it works:**
1. Fetches `catalog.json` from gh-pages (production state)
2. Compares with local manifests (git state)
3. Detects version changes
4. Outputs JSON array of changed exporters

**Override:**
- Set `FORCE_REBUILD=true` to rebuild everything
- Set `TARGET_EXPORTER=name` to build specific exporter

---

## Metadata Publishing (V3)

Each build job publishes **exactly 1 JSON file**:

```bash
# RPM job (el9/amd64) publishes:
catalog/node_exporter/rpm_amd64_el9.json

# RPM job (el9/arm64) publishes:
catalog/node_exporter/rpm_arm64_el9.json

# DEB job (debian-12/amd64) publishes:
catalog/node_exporter/deb_amd64_debian-12.json

# Docker job publishes:
catalog/node_exporter/docker.json
```

**No race conditions:** Each job writes to a different file.

**Aggregation:** Portal generation aggregates these files into `metadata.json` on-demand.

---

## Security Scanning

Security scans run in parallel with builds:

**Docker images:**
- Trivy scan with SARIF output
- Results uploaded to GitHub Security tab
- Critical/High vulnerabilities block release

**Python code:**
- Bandit: Security linter for Python
- pip-audit: Check dependencies for CVEs
- Results in security.yml workflow

**Frequency:**
- Daily: security.yml (scheduled)
- On PR: build-pr.yml (gating)
- On release: build.yml (embedded)

---

## See Also

- [Unified Workflow Architecture](./unified-workflow.md) - Complete migration details
- [State Manager Documentation](../api-reference/state-manager.md) - Change detection logic
- [V3 Catalog Architecture](../api-reference/catalog-v3.md) - Granular metadata structure
