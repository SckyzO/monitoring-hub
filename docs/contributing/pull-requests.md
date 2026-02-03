# Pull Requests

Guidelines for submitting pull requests.

## Before You Submit

1. ✅ Tests pass locally (`make test`)
2. ✅ Linting passes (`make lint`)
3. ✅ Documentation updated
4. ✅ Commit messages follow conventions

## PR Process

1. **Create Branch**: `git checkout -b feature/my-feature`
2. **Make Changes**: Follow coding standards
3. **Test Locally**: Run test suite
4. **Commit**: Use conventional commits
5. **Push**: `git push origin feature/my-feature`
6. **Create PR**: On GitHub

## PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] New tests added
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

## CI Checks

All PRs must pass:

- ✅ Linting (ruff)
- ✅ Tests (pytest)
- ✅ Build validation
- ✅ Manifest validation

## Review Process

Maintainers will review and may request changes. Once approved, PRs are merged automatically.
