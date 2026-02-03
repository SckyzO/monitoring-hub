# Build Pipeline

Detailed documentation of the build pipeline.

## Pipeline Stages

### 1. State Management

Compares local manifests against deployed catalog.json to determine what needs rebuilding.

### 2. Artifact Generation

Builder downloads upstream binaries, extracts them, and renders Jinja2 templates.

### 3. Parallel Builds

- **RPM**: Built for el8, el9, el10 × amd64, arm64
- **Docker**: Built as multi-arch images

### 4. Validation

- Port checks for Docker containers
- Command validation for binaries
- Schema validation for manifests

### 5. Publication

- RPMs pushed to GitHub Pages YUM repository
- Docker images pushed to GHCR
- Catalog updated

## Incremental Builds

Only changed exporters are rebuilt, saving time and resources.
