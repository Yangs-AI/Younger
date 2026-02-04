# Contributing to Younger

This document explains how to develop and contribute to this repository.

## Repository layout and dependency graph
- `younger`: kernel package
- `younger_logics_core` and `younger_logics_ir`: logic toolchains, depend on `younger`
- `younger_apps_dl`: DL apps, depend on `younger` + `younger_logics_core` + `younger_logics_ir`
- `younger_tools_bench`: tools (planned)

## Development environment
Use Python 3.12+ with a dedicated virtual environment.

```bash
git clone --recursive git@github.com:Yangs-AI/Younger.git
cd Younger
git checkout dev
git submodule update --init --recursive

# core
pip install -e .

# logics
pip install -e younger/logics/core
pip install -e younger/logics/ir

# apps
pip install -e younger/apps/dl

# tools (optional)
pip install -e younger/tools/bench
```

For docs and dev tools, install the optional extras for each package:

```bash
pip install -e .[developer]
pip install -e younger/logics/ir[develop]
pip install -e younger/logics/core[develop]
pip install -e younger/apps/dl[develop]
pip install -e younger/tools/bench[develop]
```

## Dependency boundaries
To keep the dependency graph clean:
- `younger` provides kernel capabilities and does not depend on logics/apps/tools.
- `younger_logics_core` and `younger_logics_ir` depend only on `younger`.
- `younger_apps_dl` depends on `younger` + `younger_logics_core` + `younger_logics_ir`.
- `younger_tools_bench` is not part of the dependency chain for now.

New code must follow these boundaries to avoid cyclic dependencies.

## Development guidelines
- Ensure tests pass before submitting.
- Preserve existing code style; avoid unrelated reformatting.
- Add tests and docs for new features.

## Tests
Run from the repository root:

```bash
pytest tests
```

Submodules have their own tests as needed:

```bash
pytest younger/logics/ir/tests
pytest younger/logics/core/tests
pytest younger/apps/dl/tests
```

## Branching and commits
- Use the `dev` branch for day-to-day work.
- Commit message format: `type: summary` (e.g., `feat: add new parser`).

## Pull Request (PR) workflow
1. Fork this repo and create a feature branch.
2. Complete development and tests.
3. Open a PR with a clear description of changes and impact.

Recommended PR content:
- Summary of changes
- Impacted packages/modules
- Test results

## Versioning and releases (maintainers)
See [RELEASE.md](RELEASE.md) for the publishing order and checklist.

Versioning notes:
- Use PEP 440 versions (e.g., `0.0.1a1`, `0.1.0`, `1.0.0`).
- Prefer compatible dependency ranges (e.g., `younger>=x,<y`) to avoid install-time mismatches.
