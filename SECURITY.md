# Security Policy

## Supported Versions

We actively support the latest version of Monitoring Hub. Security updates are applied to the `main` branch and included in the next release.

| Version | Supported          |
| ------- | ------------------ |
| main    | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in Monitoring Hub, please report it responsibly:

### Private Reporting (Recommended)

1. **GitHub Security Advisories**: Use the [Security Advisories](https://github.com/SckyzO/monitoring-hub/security/advisories) feature on GitHub
   - Click "Report a vulnerability"
   - Provide detailed information about the vulnerability
   - We will respond within 48 hours

2. **Email**: Contact the maintainer directly
   - Email: [Maintainer GitHub profile](https://github.com/SckyzO)
   - Include "SECURITY" in the subject line
   - Provide steps to reproduce the vulnerability

### What to Include

Please provide:
- Description of the vulnerability
- Steps to reproduce the issue
- Potential impact and severity
- Any proof-of-concept code (if applicable)
- Your contact information for follow-up

### Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Depends on severity
  - Critical: 7-14 days
  - High: 14-30 days
  - Medium/Low: Next regular release

### Public Disclosure

- We will coordinate disclosure with you
- Vulnerabilities will be disclosed after a fix is available
- Credit will be given to reporters (unless anonymity is requested)

## Security Measures

Monitoring Hub implements several security best practices:

### Code Security

- **Static Analysis**: Bandit security scanner runs on all PRs
- **Dependency Scanning**: pip-audit checks for vulnerable dependencies
- **Container Scanning**: Trivy scans container images for vulnerabilities
- **Automated Updates**: Dependabot monitors and updates dependencies

### Network Security

- **Timeouts**: All HTTP requests include timeouts to prevent hanging
- **Retry Logic**: Exponential backoff with retry limits for network operations
- **TLS/HTTPS**: All external communications use HTTPS

### Build Security

- **Input Validation**: Strict manifest schema validation with marshmallow
- **Template Security**: Jinja2 templates use autoescape to prevent injection
- **Signed Releases**: Future releases will include GPG signatures

### Container Security

- **Base Images**: Use official Red Hat UBI minimal images
- **Non-Root**: Containers run as non-privileged users where possible
- **Read-Only**: Filesystem mounted as read-only where applicable

## Best Practices for Users

When deploying Monitoring Hub:

1. **Use Latest Version**: Always use the latest stable release
2. **Scan Images**: Run container security scans before deployment
3. **Network Isolation**: Deploy in isolated network segments
4. **Access Control**: Restrict access to build artifacts and manifests
5. **Monitor Dependencies**: Enable Dependabot alerts in your fork

## Security Contacts

- **Maintainer**: [@SckyzO](https://github.com/SckyzO)
- **Security Issues**: Use GitHub Security Advisories
- **General Questions**: Open a GitHub Discussion

## Acknowledgments

We thank the security research community for responsibly disclosing vulnerabilities and helping improve the security of Monitoring Hub.
