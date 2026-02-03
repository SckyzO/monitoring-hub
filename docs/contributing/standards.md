# Coding Standards

Code quality standards for Monitoring Hub.

## Commit Messages

Use Conventional Commits format:

- `feat(exporters): add new exporter`
- `fix(builder): correct archive extraction`
- `docs: update installation guide`
- `test: add builder unit tests`
- `chore(deps): update dependencies`

## Code Style

- **Python**: Follow PEP 8, enforced by ruff
- **Formatting**: Automated with ruff format
- **Type Hints**: Encouraged but not required
- **Docstrings**: Google style

## Testing

- Write tests for new functionality
- Maintain or improve coverage
- Use pytest fixtures for common setup

## Documentation

- Update docs for user-facing changes
- Include code examples
- Keep manifest.reference.yaml in sync
