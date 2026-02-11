## Description

<!-- Provide a brief description of the changes in this PR -->

## Type of Change

<!-- Mark the relevant option with an "x" -->

- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📝 Documentation update
- [ ] 🔧 Configuration change
- [ ] ♻️ Code refactoring (no functional changes)
- [ ] ✅ Test additions or updates
- [ ] 🚀 CI/CD improvements

## Related Issues

<!-- Link related issues using keywords: Fixes #123, Closes #456, Relates to #789 -->

Fixes #

## Changes Made

<!-- List the specific changes made in this PR -->

-
-
-

## Testing Performed

<!-- Describe the tests you ran to verify your changes -->

### Test Commands
```bash
# Example commands used for testing
./devctl test
./devctl ci
./devctl build-exporter my_exporter
```

### Test Results
<!-- Paste relevant test output or describe results -->

```
# Test output here
```

## Screenshots (if applicable)

<!-- Add screenshots to help explain your changes -->

## Checklist

<!-- Mark completed items with an "x" -->

### Required

- [ ] My code follows the project's code style (`./devctl lint` passes)
- [ ] Code is formatted (`./devctl format-check` passes)
- [ ] Type checking passes (`./devctl type-check` passes)
- [ ] All tests pass (`./devctl test` passes)
- [ ] All CI checks pass (`./devctl ci` passes)
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] I have updated the documentation accordingly
- [ ] My commits follow the [Conventional Commits](https://www.conventionalcommits.org/) format
- [ ] I have rebased my branch on the latest main branch

### Optional

- [ ] I have added/updated relevant configuration files
- [ ] I have tested on multiple distributions (el8/el9/el10, Ubuntu, Debian)
- [ ] I have tested on multiple architectures (amd64, arm64)
- [ ] I have updated the changelog (if applicable)

## Additional Notes

<!-- Any additional information that reviewers should know -->

## Deployment Notes

<!-- Any special deployment considerations or migration steps required -->

---

**Reviewer Guidelines:**

- Verify all CI checks pass
- Test locally if possible
- Check for security implications
- Ensure documentation is updated
- Confirm commit messages follow conventions
