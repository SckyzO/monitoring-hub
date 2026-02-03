# Security Guidelines

Security best practices for contributing to Monitoring Hub.

## Code Security Principles

### Input Validation

**Always validate external input:**

```python
# Good: Strict schema validation
from core.engine.schema import ManifestSchema
schema = ManifestSchema()
validated_data = schema.load(user_input)

# Bad: Trusting user input
data = yaml.safe_load(untrusted_file)  # No validation
```

**Manifest validation prevents:**
- Injection attacks through malformed YAML
- Unexpected data types causing runtime errors
- Missing required fields

### Network Operations

**Always use timeouts:**

```python
# Good: Timeout prevents hanging
response = requests.get(url, timeout=30)

# Bad: No timeout
response = requests.get(url)  # Can hang indefinitely
```

**Implement retry logic with exponential backoff:**

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def download_file(url):
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.content
```

### Template Security

**Enable Jinja2 autoescape:**

```python
# Good: Autoescape prevents XSS
from jinja2 import Environment, FileSystemLoader, select_autoescape

env = Environment(
    loader=FileSystemLoader(template_dir),
    autoescape=select_autoescape(['html', 'xml', 'j2'])
)

# Bad: No autoescape
env = Environment(loader=FileSystemLoader(template_dir))
```

### Exception Handling

**Always chain exceptions for better debugging:**

```python
# Good: Exception chaining preserves context
try:
    dangerous_operation()
except SpecificError as err:
    logger.error(f"Operation failed: {err}")
    raise click.Abort() from err

# Bad: Losing exception context
except:
    raise click.Abort()
```

**Avoid bare except clauses:**

```python
# Good: Specific exception handling
try:
    risky_operation()
except (ValueError, KeyError) as err:
    handle_error(err)

# Bad: Catches everything including KeyboardInterrupt
try:
    risky_operation()
except:
    pass
```

## Dependency Security

### Managing Dependencies

- **Pin versions**: Use exact versions in `requirements.txt`
- **Regular updates**: Review Dependabot PRs weekly
- **Vulnerability scanning**: Check `pip-audit` reports
- **Minimal dependencies**: Only add necessary packages

### Before Adding Dependencies

1. Check package reputation (GitHub stars, downloads, maintainers)
2. Review security advisories on [PyPI Advisory Database](https://github.com/pypa/advisory-database)
3. Verify package signatures when available
4. Check for known vulnerabilities with `pip-audit`

## Container Security

### Dockerfile Best Practices

```dockerfile
# Use minimal base images
FROM registry.access.redhat.com/ubi9/ubi-minimal

# Run as non-root user
RUN useradd -r -u 1000 exporter
USER exporter

# Use read-only root filesystem
VOLUME ["/var/lib/exporter"]
```

### Image Scanning

Before pushing images:

```bash
# Scan with Trivy
trivy image monitoring-hub/exporter:latest

# Check for high/critical vulnerabilities
trivy image --severity HIGH,CRITICAL monitoring-hub/exporter:latest
```

## Secret Management

**Never commit secrets:**

- API tokens
- Private keys
- Passwords
- Connection strings

**Use environment variables:**

```python
# Good: From environment
token = os.environ.get('GITHUB_TOKEN')

# Bad: Hardcoded
token = "ghp_xxxxxxxxxxxx"
```

**Add sensitive files to `.gitignore`:**

```
secrets/
.env
*.key
*.pem
credentials.json
```

## Security Testing

### Pre-Commit Checks

Install pre-commit hooks:

```bash
make install
```

This runs:
- `bandit`: Security vulnerability scanner
- `ruff`: Linting with security rules
- `mypy`: Type checking

### Manual Security Checks

```bash
# Run security scanner
make security

# Check for vulnerable dependencies
pip-audit -r core/requirements.txt

# Scan code for secrets
gitleaks detect --no-git
```

## Reporting Security Issues

**Do not open public issues for security vulnerabilities.**

Follow our [Security Policy](../../SECURITY.md) for responsible disclosure.

## Security Checklist for Contributors

Before submitting a PR:

- [ ] All network calls have timeouts
- [ ] Input validation on external data
- [ ] No hardcoded secrets or credentials
- [ ] Jinja2 templates use autoescape
- [ ] Exceptions are properly chained
- [ ] No bare `except:` clauses
- [ ] Dependencies are pinned and reviewed
- [ ] Security tests pass (`make security`)
- [ ] No new Bandit warnings introduced

## Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)
- [Bandit Documentation](https://bandit.readthedocs.io/)
- [pip-audit](https://github.com/pypa/pip-audit)

## Questions?

For security questions or concerns:

- Open a GitHub Discussion
- Contact maintainers privately for sensitive issues
- See [SECURITY.md](../../SECURITY.md) for vulnerability reporting
