# Release Guide (Maintainers)

This monorepo contains multiple publishable Python packages. Recommended release order:

1. `younger-logics-core`
2. `younger-logics-ir`
3. `younger-apps-dl`
4. `younger-tools-bench` (if needed)
5. `younger` (kernel, with extras)

## Pre-release checklist
- Update version in each package `pyproject.toml`.
- Ensure dependency ranges are compatible (e.g., `younger>=x,<y`).
- Run tests (at least for the kernel + impacted subpackages).
- Update README or changelog if needed.

## Build and publish (recommended)
For each subpackage:

1. Enter the package directory (contains `pyproject.toml`).
2. Clean old build artifacts (`dist/`, `build/`).
3. Build with `python -m build`.
4. Upload with `twine upload dist/*`.

## Versioning strategy
- Use PEP 440 versions (e.g., `0.0.1a1`, `0.1.0`, `1.0.0`).
- If a release contains breaking API changes, bump the major version or tighten dependency ranges.
- Keep subpackage and kernel compatibility ranges predictable.

## Post-release verification
- Install each package from PyPI and validate imports/CLI.
- Validate extras install: `younger[logics]`, `younger[apps]`.

## CI note
If you automate publishing, release in order to avoid dependency availability issues.
