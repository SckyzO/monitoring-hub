# Unified Workflow Architecture

**Date:** 2026-02-16
**Status:** Active (migrated from fragmented architecture)

## Overview

Monitoring Hub uses a **unified build workflow** architecture with a single main workflow (`build.yml`) that handles all build scenarios.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                 TRIGGERS (Automatic & Manual)                │
└─────────────────────────────────────────────────────────────┘

scan-updates.yml (CRON 8h UTC)
  ↓ Creates PR with version update
User merges PR
  ↓ Triggers auto-release.yml

auto-release.yml
  ├─ Detects changed manifests (state_manager)
  └─> build.yml (changed exporters only)

security-rebuild.yml (CRON Monday 2h UTC)
  ├─ Detects new UBI9 base image
  └─> build.yml (ALL exporters)

Manual: workflow_dispatch
  └─> build.yml (custom list or ALL)

┌─────────────────────────────────────────────────────────────┐
│               UNIFIED BUILD WORKFLOW (build.yml)             │
└─────────────────────────────────────────────────────────────┘

INPUT: JSON array of exporters
  - ["node_exporter"]           → Build 1 exporter
  - ["node_exporter", "redis"]  → Build 2 exporters
  - []                          → Build ALL exporters (empty=all)
  - "" (default)                → Auto-detect (state_manager)

JOBS (Parallel):
  ├─ discover: Generate build matrix
  │
  ├─ build-docker (34× exporters × 2 arches)
  │  ├─ Build multi-arch image
  │  ├─ Push to GHCR
  │  ├─ Upload to GitHub Releases
  │  └─ Generate docker.json (V3 metadata)
  │
  ├─ build-rpm (~200 jobs: 34 × 2 arches × 3 dists)
  │  ├─ Build RPM in AlmaLinux container
  │  ├─ Sign with GPG
  │  ├─ Upload to GitHub Releases
  │  └─ Generate rpm_<arch>_<dist>.json (V3 metadata)
  │
  ├─ build-deb (~68 jobs: 34 × 2 arches × 1 dist)
  │  ├─ Build DEB in Debian 12 container
  │  ├─ Sign with GPG
  │  ├─ Upload to GitHub Releases
  │  └─ Generate deb_<arch>_<dist>.json (V3 metadata)
  │
  ├─ aggregate-security
  │  └─ Aggregate Trivy scan results
  │
  └─ publish-metadata-portal (Sequential, after all builds)
     ├─ Download ALL metadata artifacts
     ├─ Organize into catalog/<exporter>/*.json
     ├─ Generate portal with site_generator_v2.py
     └─ Push to gh-pages (catalog/ + index.html)

OUTPUT:
  ✅ Packages on GitHub Releases
  ✅ Docker images on GHCR
  ✅ Catalog V3 on gh-pages
  ✅ Portal updated on gh-pages
```

## Workflow List

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| **build.yml** ⭐ | workflow_dispatch, auto-release, security-rebuild | Main unified build workflow |
| **auto-release.yml** | push to exporters/ | Detects manifest changes, triggers build.yml |
| **scan-updates.yml** | CRON daily 8h UTC | Scans for new versions, creates PRs |
| **security-rebuild.yml** | CRON Monday 2h UTC | Rebuilds all for security updates |
| **build-pr.yml** | pull_request | Validates PRs (lint + schema + canary) |
| **deploy-docs.yml** | push to docs/ | Deploys MkDocs documentation |

## Key Principles

### 1. Single Responsibility
- **One workflow does it all**: build.yml handles building, uploading, catalog, and portal
- No fragile workflow chains (no build → upload → catalog → portal)
- No concurrency bottlenecks

### 2. Scalability
- Handles 1 exporter as efficiently as 34 exporters
- Parallel builds (100+ jobs running concurrently)
- Single aggregation job at the end (no race conditions)

### 3. Maintainability
- Only 6 workflows instead of 12
- Clear responsibility for each workflow
- Easy to understand and debug

### 4. Consistency
- Same workflow for all scenarios (auto, security, manual)
- Consistent inputs (JSON array of exporters)
- Consistent outputs (Releases + Catalog + Portal)

## Migration from Legacy Architecture

### What Was Removed

The following workflows were **disabled** (renamed to `.disabled`) as they are now integrated into `build.yml`:

- `build-legacy.yml.disabled` - Old single-exporter build
- `full-build.yml.disabled` - Batch build (logic merged into build.yml)
- `upload-releases.yml.disabled` - Upload step (now integrated)
- `catalog-update.yml.disabled` - Catalog update (now integrated)
- `update-portal.yml.disabled` - Portal update (now integrated)

### Why They Were Removed

**Problem 1: Fragile Workflow Chain**
```
build.yml → upload-releases.yml → catalog-update.yml → update-portal.yml
   ↓              ↓                      ↓                    ↓
 If any fails, entire chain breaks
```

**Problem 2: Concurrency Chaos**
```
security-rebuild triggers 34× build.yml in parallel
  → Each triggers upload-releases.yml
    → But upload-releases has concurrency: 1
      → 33 triggers lost/cancelled
        → Packages built but catalog never updated ❌
```

**Problem 3: Architecture Confusion**
- build.yml for 1 exporter
- full-build.yml for N exporters
- Why two workflows for the same task?

### Solution: Unified Architecture

**One workflow to rule them all:**
```
build.yml handles:
  ✅ 1 exporter
  ✅ N exporters
  ✅ ALL exporters
  ✅ Auto-detected exporters
```

**No chains, no concurrency issues:**
```
build.yml does everything in one workflow run:
  ├─ Build (parallel)
  ├─ Upload (parallel)
  └─ Catalog + Portal (sequential after all)
```

## Usage Examples

### Scenario 1: User Updates 1 Manifest

```bash
# User edits exporters/node_exporter/manifest.yaml
git commit -m "feat: update node_exporter to v1.11.0"
git push origin main
```

**Flow:**
```
push → auto-release.yml
    ├─ state_manager detects 1 changed exporter
    └─> build.yml --raw-field exporters='["node_exporter"]'
        └─> Builds only node_exporter
            └─> Updates catalog + portal ✅
```

### Scenario 2: Security Rebuild (All Exporters)

```bash
# Monday 2h UTC (automatic CRON)
security-rebuild.yml
  ├─ Detects new UBI9 base image
  └─> build.yml --raw-field exporters='[]'  # Empty = ALL
      └─> Builds ALL 34 exporters
          └─> Updates catalog + portal ✅
```

### Scenario 3: Manual Rebuild After Refactoring

```bash
# User manually triggers build.yml in GitHub Actions UI
# Input: exporters = [] (empty)
```

**Flow:**
```
Manual trigger → build.yml (empty input = ALL)
    └─> Builds ALL 34 exporters from scratch
        └─> Publishes everything ✅
```

### Scenario 4: Test Specific Exporters

```bash
# User manually triggers build.yml in GitHub Actions UI
# Input: exporters = ["node_exporter", "redis_exporter", "prometheus"]
```

**Flow:**
```
Manual trigger → build.yml
    └─> Builds only these 3 exporters
        └─> Updates catalog + portal ✅
```

## Rollback Plan

If critical issues arise with the unified architecture:

```bash
# Restore legacy workflows
cd .github/workflows/
mv build-legacy.yml.disabled build-single.yml
mv full-build.yml.disabled full-build.yml
mv upload-releases.yml.disabled upload-releases.yml
mv catalog-update.yml.disabled catalog-update.yml
mv update-portal.yml.disabled update-portal.yml

# Revert auto-release and security-rebuild
git restore auto-release.yml security-rebuild.yml

# Disable unified build.yml
mv build.yml build-unified.yml.disabled
```

## Testing Checklist

Before declaring the migration complete, verify:

- [ ] build.yml triggered by auto-release works
- [ ] build.yml triggered by security-rebuild works
- [ ] build.yml manual trigger with 1 exporter works
- [ ] build.yml manual trigger with 3 exporters works
- [ ] build.yml manual trigger with empty (ALL) works
- [ ] Catalog.json published correctly on gh-pages
- [ ] Portal (index.html) updated correctly
- [ ] No concurrency issues
- [ ] No race conditions in metadata aggregation

## Benefits

### Operational
✅ Simpler mental model (1 main workflow vs 5 chained workflows)
✅ Faster debugging (everything in one workflow run)
✅ No concurrency bottlenecks
✅ No race conditions

### Development
✅ Easier to maintain (less code duplication)
✅ Easier to test (single workflow to validate)
✅ Easier to extend (add features in one place)

### Reliability
✅ No fragile chains (1 workflow = atomic operation)
✅ Consistent behavior across all scenarios
✅ Better error handling (fail early in single workflow)

## See Also

- [V3 Granular Catalog Architecture](../api-reference/catalog-v3.md)
- [CI/CD Workflows](./ci-cd.md)
- [State Manager Documentation](../api-reference/state-manager.md)
