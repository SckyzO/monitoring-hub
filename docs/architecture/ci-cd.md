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

### security.yml

Security scanning workflow that runs on pull requests and pushes to main.

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

## Workflow Features

- Parallel matrix builds
- Incremental builds
- Automatic deployment
- Validation tests
- Security scanning with SARIF integration
- Multi-architecture support (amd64, arm64)
