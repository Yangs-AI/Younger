"""Validate release metadata and distribution contents without importing the package."""

import argparse
import configparser
import email
import fnmatch
import os
from pathlib import Path
import tarfile
import tomllib
import zipfile

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from packaging.version import Version


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata-only", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    config = tomllib.loads((root / "pyproject.toml").read_text())
    project = config["project"]
    name = canonicalize_name(project["name"])
    version = project["version"]
    Version(version)
    module = name.replace("-", "_")

    if os.environ.get("GITHUB_REF_TYPE") == "tag":
        tag = os.environ["GITHUB_REF_NAME"]
        if tag != f"v{version}":
            raise ValueError(f"Tag {tag!r} does not match version {version!r}")

    dependencies = list(project.get("dependencies", []))
    for extra in project.get("optional-dependencies", {}).values():
        dependencies.extend(extra)
    for dependency in dependencies:
        requirement = Requirement(dependency)
        if canonicalize_name(requirement.name).split("-")[0] == "younger":
            operators = {specifier.operator for specifier in requirement.specifier}
            if not {">=", "<"}.issubset(operators):
                raise ValueError(f"Internal dependency needs lower and upper bounds: {dependency}")

    if args.metadata_only:
        print(f"name={name}\nversion={version}\nmodule={module}")
        print(f"prerelease={str(Version(version).is_prerelease).lower()}")
        return

    discovery = config["tool"]["setuptools"]["packages"]["find"]
    expected = set()
    for path in (root / module).rglob("*.py"):
        package = ".".join(path.parent.relative_to(root).parts)
        if not any(fnmatch.fnmatchcase(package, pattern) for pattern in discovery["include"]):
            continue
        if any(fnmatch.fnmatchcase(package, pattern) for pattern in discovery.get("exclude", [])):
            continue
        if not discovery.get("namespaces", True) and not (path.parent / "__init__.py").is_file():
            continue
        expected.add(path.relative_to(root).as_posix())
    if not expected:
        raise ValueError("No Python source files discovered")

    wheels = list((root / "dist").glob("*.whl"))
    sdists = list((root / "dist").glob("*.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        raise ValueError("Expected exactly one wheel and one sdist in dist/")
    with zipfile.ZipFile(wheels[0]) as archive:
        names = archive.namelist()
        actual = {path for path in names if path.endswith(".py")}
        metadata_files = [path for path in names if path.endswith(".dist-info/METADATA")]
        if len(metadata_files) != 1:
            raise ValueError("Expected one wheel METADATA file")
        metadata = email.message_from_bytes(archive.read(metadata_files[0]))
        if canonicalize_name(metadata["Name"]) != name or metadata["Version"] != version:
            raise ValueError("Wheel metadata does not match pyproject.toml")
        entry_points = configparser.ConfigParser()
        entry_points.read_string(archive.read(metadata_files[0].replace("METADATA", "entry_points.txt")).decode())
        if dict(entry_points["console_scripts"]) != project["scripts"]:
            raise ValueError("Wheel console scripts do not match pyproject.toml")
        if name == "younger" and any(path.startswith(("younger/apps/", "younger/logics/", "younger/tools/")) for path in names):
            raise ValueError("Kernel wheel contains component repository files")
    if actual != expected:
        raise ValueError(f"Wheel source mismatch: missing={sorted(expected - actual)}, extra={sorted(actual - expected)}")

    with tarfile.open(sdists[0]) as archive:
        names = {path.partition("/")[2] for path in archive.getnames()}
        actual = {path for path in names if path.startswith(module + "/") and path.endswith(".py")}
        if actual != expected:
            raise ValueError(f"Sdist source mismatch: missing={sorted(expected - actual)}, extra={sorted(actual - expected)}")
        if "LICENSE" not in names:
            raise ValueError("Sdist is missing LICENSE")
    print(f"Verified {name}=={version}: {len(expected)} Python files, wheel and sdist")


if __name__ == "__main__":
    main()
