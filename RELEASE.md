# Release Guide

Younger uses independent Git repositories connected by Git submodules. Each
repository builds one Python distribution, owns its version in `pyproject.toml`,
and publishes its own GitHub Release and PyPI project. Conda distribution is
deferred.

## Routine release

Use this procedure for every new version. Trusted Publisher and GitHub environment
setup is normally needed only once per repository. Release only packages that
changed; other packages may keep their existing versions. Skip deferred packages.

Run Git commands in the repository of the package being released:

| Package | Directory from the Younger checkout | Expected official `origin` |
| --- | --- | --- |
| `younger` | `.` | `Yangs-AI/Younger` |
| `younger-logics-ir` | `younger/logics/ir` | `Yangs-AI/Younger-Logics-IR` |
| `younger-apps-dl` | `younger/apps/dl` | `Yangs-AI/Younger-Apps-DL` |

For a standalone component checkout, use its root directory. A tag in the parent
repository does not tag or publish its submodules.

1. On `dev`, update this package's `project.version` in `pyproject.toml`, dependency
   ranges when needed, and release notes. Use a new version for new artifacts.
   For example, a compatible IR fix does not require a new kernel or DL version.
2. Run relevant tests and build checks described below. Commit and push changes
   in each affected repository. Component changes must be pushed before the
   parent can check out their commits in CI.
3. For a new tested combination, update the parent repository's submodule pointers
   and `releases/current.txt` to the actual package versions. Commit these changes
   in the parent repository. Run **Verify package combination** for that checkout;
   matching the combination does not require package version numbers to be equal.
4. Open a PR from `dev` to `main` in the package repository. In its latest commit's
   **Checks**, confirm **Build and release** jobs `build` and `verify` succeeded.
   For a parent PR changing package versions, submodule pointers, or the combination,
   also confirm **Verify package combination** job `integration` succeeded.
   `publish` and `github-release` are skipped on PRs and manual runs. Documentation-only
   parent PRs may not trigger integration because it has path filters.
5. After the PR is merged and required dependency versions are available on PyPI,
   use the commands below in this package's repository to tag its release commit
   on `main`. For the first coordinated release, publish Younger, then IR, then DL;
   for later releases, publish only the changed packages in dependency order.
   A component's standalone check can fail until its required upstream version is
   on PyPI; rerun that check after publishing the upstream dependency.
6. In GitHub **Actions**, open the tag-triggered **Build and release** run and
   confirm `build`, `verify`, `publish`, and `github-release` all succeeded. Confirm
   the version on PyPI and its GitHub Release, then install that exact version in a
   clean environment outside the source checkout and check its import, CLI, and
   relevant functional paths. Finally, record the released component commits in
   the parent and preserve accepted combinations as new named snapshots.

First, synchronize `main` and inspect the release commit. Start with a clean
working tree; confirm `origin` is the intended repository from the table:

```bash
git status --short
git remote -v
git fetch origin --tags
git switch main
git pull --ff-only origin main
git log -1 --oneline
```

Read the version from this repository's `pyproject.toml` using Python 3.12+:

```bash
release_version=$(python -c 'import pathlib, tomllib; print(tomllib.loads(pathlib.Path("pyproject.toml").read_text())["project"]["version"])')
git tag --list "v${release_version}"
```

If the tag is listed, stop and inspect the existing release; do not overwrite it.
Confirm this is the intended new version and release commit, then create and push
only that tag. This push starts the actual PyPI publication:

```bash
git tag -a "v${release_version}" -m "Release ${release_version}"
git push origin "v${release_version}"
```

For an IR release, run this sequence inside `younger/logics/ir`; for a DL release,
run it inside `younger/apps/dl`. Each reads its own version and publishes only its
own package. Do not repeat the parent package's tag operation for unchanged or
deferred components.

If a check fails, open the failing job and step in **Actions** to read the error.
If **Run workflow** is unavailable, the workflow must first exist on the default
branch for manual dispatch; a PR can run its `pull_request` checks before that.
For a coordinated release, prepare and check the combination first, then complete
the package PR, tag, and publication steps in dependency order.

## Current release scope

Publish `younger`, `younger-logics-ir`, and `younger-apps-dl` at `0.1.0`. Defer
`younger-logics-core` and `younger-tools-bench`; their source repositories and
prepared release configuration may remain in place without publishing tags.
They are excluded from `releases/current.txt` and the combination workflow.

The kernel currently exposes `apps`, `apps-dl`, `logics`, and `logics-ir` extras.
`logics` installs IR only. Add Core/Bench extras when those packages are published.
DL is planned to depend on Core as well as IR. Its current code does not import
Core; declare the dependency when the integration is implemented, after a
compatible Core version is available. If Core becomes required before DL's first
release, publish Core first or defer DL as well.

## Deferring a package

If a package such as DL is postponed, update the release scope consistently:

1. Remove it from `releases/current.txt`. A still-unreleased candidate snapshot
   such as the initial `0.1.0.txt` may also be updated; preserve snapshots of
   already-published combinations.
2. Remove kernel extras that require the unavailable release. For DL, these are
   `apps` and `apps-dl`. Changing published dependency metadata requires a new
   kernel version; before the first publication, adjust the candidate directly.
3. Remove the package from the parent integration workflow's build directories,
   install extras, imports, and CLI checks. Removing a requirements-file line
   alone does not remove wheels passed directly to pip or an extras dependency.
4. Update the release scope and installation examples in the documentation.

The deferred repository and its Trusted Publisher configuration may remain in
place. Publish that package later using its own version and tag when ready.

## Branches and tags

The recommended flow for each repository is feature branches into `dev`, then a
reviewed release PR from `dev` into `main`, followed by a `v<version>` tag on the
release commit in `main`. `main` contains accepted release changes; `dev` can
continue with work for the next version. The exact released snapshot is the tag.
The workflow publishes on a matching tag push; it does not perform these merges.

A branch per version such as `v0.1.0` is unnecessary. Use `v0.1.0`, `v0.1.1`, and
`v0.2.0` as tags. If `dev` needs to move on to `0.2` while `0.1` is stabilizing,
an optional `release/0.1` branch can receive only release fixes before merging
into `main`. Keep a branch for `0.1.x` maintenance only if that older series still
needs support after development moves on. Propagate applicable fixes back to
`main` and `dev`; do not merge unrelated newer features into the older series.
Branches and tags belong to their own package repositories and need not advance
in lockstep.

## Versions and compatibility

- The initial release prepared here is `0.1.0` for each package in scope. Future package
  versions advance independently; a component update does not require a kernel
  update when it remains inside the kernel's extras dependency range.
- Use PEP 440 distribution versions, such as `0.1.0rc1` and `0.1.0`. During the
  `0.x` series, minor updates may break compatibility; patch updates must remain
  compatible. From `1.0`, use SemVer rules for public API compatibility.
- Declare internal dependencies with a minimum supported version and an exclusive
  upper bound. Initially these are `>=0.1.0,<0.2.0`; verify this policy with tests
  and raise the lower bound when a new dependency feature is required.
- Kernel extras provide convenient installation within compatibility ranges.
  Changing those ranges requires a new kernel distribution, even without code
  changes. Keep components out of the kernel's required dependencies.
- Dataset and IR metadata versions are separate from distribution versions and
  retain their existing `semantic_release.Version` implementation. The package
  declares `python-semantic-release` as a runtime dependency because importing
  `younger.commons.version` requires it.
- Update versions manually for now. CI verifies that `v<version>` exactly matches
  `project.version`; commit messages do not automatically choose versions.

## One-time setup for each repository

| Repository | PyPI project | Import package | Current scope |
| --- | --- | --- | --- |
| `Yangs-AI/Younger` | `younger` | `younger` | Publish |
| `Yangs-AI/Younger-Logics-Core` | `younger-logics-core` | `younger_logics_core` | Deferred |
| `Yangs-AI/Younger-Logics-IR` | `younger-logics-ir` | `younger_logics_ir` | Publish |
| `Yangs-AI/Younger-Apps-DL` | `younger-apps-dl` | `younger_apps_dl` | Publish |
| `Yangs-AI/Younger-Tools-Bench` | `younger-tools-bench` | `younger_tools_bench` | Deferred |

1. Commit the repository's `pyproject.toml`, `scripts/check_release.py`, and
   `.github/workflows/release.yml`. Component files must be committed and pushed
   in their own repositories before the parent repository records their commits.
2. Create a GitHub Actions environment named `pypi` in each repository.
3. On the corresponding PyPI project's Publishing page, add a GitHub Trusted
   Publisher: owner `Yangs-AI`, the matching repository from the table, workflow
   filename `release.yml`, environment `pypi`. For a project that does not exist
   yet, configure a pending publisher on PyPI instead.
4. Ensure GitHub Actions can create repository Releases. Publishing uses OIDC,
   so a stored PyPI API token is unnecessary.

See the official [Trusted Publisher setup](https://docs.pypi.org/trusted-publishers/adding-a-publisher/)
and [GitHub Actions publishing guide](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/).

## Prepare and validate

Use Python 3.12 or newer. For each affected repository:

1. Update `project.version`, internal dependency bounds, and release notes.
2. Use a clean checkout so `dist/` contains only this version's artifacts.
3. Build and inspect the distributions:

   ```bash
   python -m pip install build twine
   python scripts/check_release.py --metadata-only
   python -m build
   python -m twine check --strict dist/*
   python scripts/check_release.py
   ```

   The default build creates an sdist and builds its wheel from that sdist.
   The checker validates package contents, metadata, console scripts, internal
   dependency bounds, and the tag when run from a tag workflow. Kernel wheels
   must not contain component repositories; component wheels must include all
   their discovered Python subpackages.
4. Run relevant unit and functional tests. The release workflow installs the
   wheel in a clean Python 3.12 environment, checks import and CLI loading, and
   runs `pip check`. The kernel also runs `tests/` against its installed wheel.
   These checks do not replace model conversion, training, or other component
   functional tests; some existing IR test files are network integration scripts.

For a coordinated release, first commit the component changes and update the
parent's submodule pointers to those commits. Then run **Verify package
combination** in the parent repository. It builds the three repositories in scope,
installs their wheels together with extras, and verifies imports and CLI entry
points. `releases/current.txt` records the current candidate direct package pins. This is
not a transitive dependency lock or a claim that every optional feature works.
Archive an environment lock separately when exact research reproduction is needed.

When a package version or a submodule pointer changes, update `releases/current.txt`
to match the versions built from that checkout. Package versions may differ; only
the packages being released need new versions. Run the combination workflow before
accepting the new combination. Save accepted combinations as new named snapshots
under `releases/`, and preserve existing snapshots such as `releases/0.1.0.txt`.
Updating only the combination record or submodule pointers does not require a new
kernel package version.

The kernel workflow runs its tests against the installed wheel; confirm its
current result in CI for every release. The earlier directory-lock and retry test
calling errors have been corrected. Core and Bench are deferred and outside the
current combination check; verify their CLI and functionality before enabling
their releases. Build and CLI checks do not cover model conversion or training.

During the first release, a component's independent installation job may fail
until its required kernel/IR version exists on PyPI. Use the combination workflow
to verify unpublished local wheels first, then publish in dependency order.

## Publish in dependency order

For the current release:

1. Publish `younger` and wait for its version to be installable from PyPI.
2. Publish `younger-logics-ir` after its required kernel version is installable.
3. Publish `younger-apps-dl` after its required IR version is installable.

Publish Core and Bench separately when ready. When DL starts using Core, publish
the required Core version before that DL release.

Skip packages that have not changed and whose required versions already exist.
If a component starts requiring a newer kernel, publish that kernel first.
Kernel extras may be temporarily unavailable while a coordinated release is
being uploaded; announce the combination only after every required package is
available and installation has passed. PyPI does not provide atomic multi-project
uploads.

In each in-scope package's own repository, follow [Routine release](#routine-release)
to synchronize `main`, read that package's version, and tag its release commit.

The **Build and release** workflow runs on pull requests, manual dispatch, and
`v*` tag pushes. Only tag pushes publish to PyPI. Successful publication creates
a GitHub Release with the same wheel and sdist; prerelease versions are marked
as GitHub prereleases. Manual dispatch validates a checkout without publishing.

Published files cannot be replaced with different content under the same PyPI
filename. Fix faulty releases with a new version, and yank a broken release when
appropriate. If only GitHub Release creation fails after PyPI succeeds, create
the GitHub Release from the workflow's existing distribution artifacts; do not
rebuild and upload the same PyPI version again.

## Verify and announce

In a fresh environment, outside any source checkout:

```bash
python -m pip install -r /path/to/Younger/releases/current.txt 'younger[apps,logics]'
python -m pip check
younger --help
younger logics ir --help
younger apps dl --help
```

To reproduce a specific recorded combination, use its named snapshot file instead
of `releases/current.txt`.

Confirm the advertised functional paths as well as CLI loading. Existing runtime
and test failures must be resolved separately before publishing the affected
package. The publishing workflow fails if its installation, import, CLI, or test
checks fail; release preparation does not implement missing commands or change
existing API contracts to make those checks pass.

The parent may additionally create an `ecosystem-YYYY.MM` tag and GitHub Release
recording tested package versions and submodule commits. Such tags do not match
`v*` and do not publish the kernel. Updating only submodule pointers or a version
combination record does not require a new kernel package version.
