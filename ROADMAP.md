# 🗺️ Roadmap - Monitoring Hub

This document outlines planned features and improvements for the Monitoring Hub project.

## 🔥 High Priority

### 📊 Exporter Status Dashboard

**Goal**: Provide real-time visibility into build status for all exporters

**Components**:
- [ ] Generate status badges JSON for shields.io endpoints
  - Total exporters badge
  - Success rate badge
  - RPM/DEB/Docker status badges
  - Last build timestamp badge
- [ ] Create `STATUS.md` with per-exporter build status
  - Individual badges per exporter
  - Distribution and architecture coverage
  - Build timestamps and versions
- [ ] Add status tab to web portal
  - Interactive status dashboard
  - Real-time metrics (success/failed/pending)
  - Filterable status table
  - Build history visualization
- [ ] Implement aggregate-status workflow
  - Triggered after Release and Auto Release
  - Reads all `catalog/*.json` from gh-pages
  - Generates global metrics and badges
  - Publishes to `badges/*.json` and `STATUS.md`

**Benefits**:
- Quick overview of build health
- Easy identification of failing builds
- Better visibility for users and contributors

**Implementation Notes**:
- Use shields.io endpoint format for badges
- Merge remote catalog data to avoid false status on partial builds
- Auto-update after each release workflow

---

### 🐳 Docker Multi-Architecture Support (ARM64)

**Goal**: Build and publish ARM64 Docker images alongside AMD64

**Current State**:
- ✅ RPM: x86_64 + aarch64 (with QEMU)
- ✅ DEB: amd64 + arm64 (with QEMU)
- ❌ Docker: amd64 only

**Proposed Approach**: Docker Buildx Multi-Platform (Option 1)

**Implementation**:
- [ ] Add `docker/setup-buildx-action@v3` to workflow
- [ ] Use `docker buildx build --platform linux/amd64,linux/arm64`
- [ ] Generate multi-arch manifest automatically
- [ ] Update documentation for ARM64 usage

**Benefits**:
- Native ARM64 support (Raspberry Pi, AWS Graviton, Apple Silicon)
- Single `docker pull` command auto-selects correct architecture
- Standard industry approach (matches official Docker images)

**Trade-offs**:
- Build time: ~2x slower per exporter (QEMU emulation)
- Storage: ~2x GHCR space (acceptable: 10GB vs 50GB free tier)
- No additional GitHub Actions cost (uses QEMU, not ARM runners)

**Estimated Impact**:
- Build time: +2-3 hours total (parallelized across 35 exporters)
- GHCR storage: ~10GB total (well within free tier)

---

## 🚀 Medium Priority

### 📦 Repository Mirrors

**Goal**: Provide faster package downloads via CDN/mirrors

**Options**:
- [ ] CloudFlare R2 mirror for RPM/DEB packages
- [ ] DigitalOcean Spaces mirror
- [ ] Add mirror selection to repository configuration

**Benefits**:
- Faster downloads for international users
- Reduced load on GitHub Releases
- Better availability

---

### 🔍 Enhanced Search and Filtering

**Goal**: Improve exporter discovery in web portal

**Features**:
- [ ] Advanced search filters (category, status, architecture)
- [ ] Tag-based filtering (monitoring, database, web, etc.)
- [ ] Version comparison view
- [ ] Dependency tree visualization

---

### 📈 Metrics and Analytics

**Goal**: Track usage and adoption metrics

**Components**:
- [ ] Download statistics per exporter
- [ ] Popular exporters dashboard
- [ ] Build time trends
- [ ] Failure rate tracking

**Privacy**: All metrics would be aggregated and anonymous.

---

## 🔮 Future Ideas

### 🎨 Custom Exporter Templates

Allow users to create custom exporter templates for specific use cases:
- Systemd service templates with custom options
- Docker compose examples
- Kubernetes manifests
- Prometheus scrape configs

### 🔐 Enhanced Security

- [ ] Automated CVE scanning results in portal
- [ ] Security advisories for affected exporters
- [ ] SBOM (Software Bill of Materials) generation
- [ ] Signature verification documentation

### 🤖 Auto-Healing Builds

- [ ] Automatic retry of failed builds
- [ ] Smart failure detection and categorization
- [ ] Notification system for persistent failures

### 📝 Interactive Documentation

- [ ] Live YAML validator for manifests
- [ ] Interactive manifest builder
- [ ] Architecture decision records (ADRs)

### 🌐 Community Features

- [ ] User-contributed exporter suggestions
- [ ] Voting system for new exporters
- [ ] Community showcase (how are you using these exporters?)

---

## 📋 Completed Features

### ✅ v0.18.0 - Catalog Fragmentation (2024-02-10)

- Fragmented catalog structure (`catalog/index.json` + per-exporter files)
- 54x smaller state manager downloads (4KB vs 217KB)
- Incremental publishing support
- Backward compatible legacy `catalog.json`

### ✅ v0.17.0 - DEB Package Support

- Full Debian/Ubuntu package support
- GPG signing for DEB packages
- Multi-distribution support (Ubuntu 22.04/24.04, Debian 12/13)

### ✅ v0.16.0 - Intelligent Build Routing

- Automatic version detection and incremental builds
- Parallel build matrix for RPM/DEB/Docker
- Optimized CI/CD workflows

---

## 🤝 Contributing

Have ideas for new features? We'd love to hear them!

1. Check if the feature is already listed here
2. Open a [Feature Request](https://github.com/SckyzO/monitoring-hub/issues/new/choose)
3. Join the [Discussion](https://github.com/SckyzO/monitoring-hub/discussions)

---

**Last Updated**: 2024-02-10
