# Deployment

## Release prerequisites
1. CI passing on the target commit.
2. Local verification:
   ```bash
   make release-check
   ```
3. PyPI trusted publishing configured for this GitHub repository (OIDC).

## Release flow
1. Create and push a version tag:
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```
2. GitHub Actions runs `Release` workflow:
   - verifies tests on Python 3.12/3.13
   - builds wheel and sdist
   - uploads `release-dist` artifact
   - publishes to PyPI via OIDC trusted publishing

## Manual dry-run build
```bash
make build
```
