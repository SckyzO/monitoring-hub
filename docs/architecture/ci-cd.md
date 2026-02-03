# CI/CD Workflows

GitHub Actions workflows that power the factory.

## Main Workflows

### release.yml

Main build pipeline triggered on push to main or manual dispatch.

### scan-updates.yml

Automated watcher that checks upstream for new versions.

### build-pr.yml

PR validation that builds only changed exporters.

### update-site.yml

Portal regeneration when catalog changes.

## Workflow Features

- Parallel matrix builds
- Incremental builds
- Automatic deployment
- Validation tests
