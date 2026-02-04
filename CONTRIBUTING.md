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

# kernel
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
pip install -e .[develop]
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

## Kernel vs. submodule scope
Principle:
- `younger` should contain general, reusable capabilities.
- Each submodule should contain only functionality that is specific to that submodule.

If you discover a feature in a submodule that can be abstracted and reused:
1. Extract and implement it in `younger` as a decoupled, reusable component.
2. Update the submodule to consume the new kernel feature.
3. Submit changes separately: one PR for `younger`, one PR for the submodule.

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

## Submodules in forks
This repo uses git submodules for component packages. In a fork, you have two options:

1) Keep upstream submodules (recommended):
	- Do nothing. Submodules continue to point to the upstream Yangs-AI repos.

2) Use your own forks (when you need to modify a submodule):
	- Fork the submodule repo you plan to modify.
	- Update the submodule URL in [.gitmodules](.gitmodules) to your fork.
	- Sync and update submodules:

```bash
git submodule sync --recursive
git submodule update --init --recursive
```

Example (switch a submodule to your fork):

```bash
git config -f .gitmodules submodule.younger/logics/ir.url git@github.com:<your-username>/Younger-Logics-IR.git
git submodule sync --recursive
git submodule update --init --recursive
```

Maintainers keep the official [.gitmodules](.gitmodules) pointing to upstream Yangs-AI repos. Contributors only need to adjust submodules they work on.

### Who should update submodule pointers?
- **Contributors (developers):**
	- Do **not** commit submodule pointer updates in the parent repo unless explicitly requested.
	- Submit changes in the submodule repo itself (your fork or a PR to upstream).
- **Maintainers:**
	- Decide when to update submodule pointers in the parent repo.
	- Verify compatibility across packages before bumping submodule hashes.

If your change requires a submodule pointer update, mention it in your PR description instead of updating it yourself.

## Versioning and releases (maintainers)
See [RELEASE.md](RELEASE.md) for the publishing order and checklist.

Versioning notes:
- Use PEP 440 versions (e.g., `0.0.1a1`, `0.1.0`, `1.0.0`).
- Prefer compatible dependency ranges (e.g., `younger>=x,<y`) to avoid install-time mismatches.
