"""Creates the GitHub release of one package, for the release workflow.

Reads the version from `packages/<name>/spice.toml` at HEAD and creates the release `<name>-v<version>` on that commit,
after checking that the tag does not exist yet, that the version is newer than the latest release of the package and
that the CI result of the commit is green. Without notes, the release notes list the commits that touched the package
since its previous release.

Environment: PACKAGE (package directory), NOTES (optional release notes), PRERELEASE and DRY_RUN ("true"/"false"),
GITHUB_REPOSITORY and GH_TOKEN (for the gh CLI).
"""

import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

PACKAGES_DIR = Path("packages")
CI_CHECK_NAME = "CI result"
VERSION_PATTERN = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:-[0-9A-Za-z.-]+)?$")


def fail(message: str):
    print(f"::error::{message}")
    sys.exit(1)


def run(*args: str) -> str:
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout.strip()


def parse_version(version: str) -> tuple[int, int, int] | None:
    match = VERSION_PATTERN.match(version)
    return tuple(int(part) for part in match.groups()) if match else None


def load_manifest(package: str) -> tuple[str, str]:
    path = PACKAGES_DIR / package / "spice.toml"
    if not path.is_file():
        fail(f"{path} does not exist")
    try:
        manifest = tomllib.loads(path.read_text()).get("package", {})
    except tomllib.TOMLDecodeError as e:
        fail(f"{path}: {e}")
    name, version = manifest.get("name"), manifest.get("version")
    if name != package:
        fail(f"{path}: name {name!r} does not match the package directory {package!r}")
    if not isinstance(version, str) or parse_version(version) is None:
        fail(f"{path}: version {version!r} is not a semantic version")
    return name, version


def previous_release(package: str) -> tuple[str, tuple[int, int, int]] | None:
    """Returns the tag and version of the newest existing release of the package."""
    releases = []
    for tag in run("git", "tag", "--list", f"{package}-v*").splitlines():
        version = parse_version(tag.removeprefix(f"{package}-v"))
        if version is not None:
            releases.append((version, tag))
    if not releases:
        return None
    version, tag = max(releases)
    return tag, version


def check_ci(sha: str):
    repo = os.environ["GITHUB_REPOSITORY"]
    conclusions = run(
        "gh", "api", f"repos/{repo}/commits/{sha}/check-runs?check_name={CI_CHECK_NAME.replace(' ', '%20')}",
        "--jq", ".check_runs[].conclusion",
    ).splitlines()
    if "success" not in conclusions:
        state = ", ".join(c or "pending" for c in conclusions) or "missing"
        fail(f"The '{CI_CHECK_NAME}' check of {sha} is not green ({state}). Wait for CI on main to pass")


def generate_notes(package: str, previous_tag: str | None) -> str:
    if previous_tag is None:
        return f"Initial release of the `{package}` package"
    subjects = run("git", "log", "--format=%s", f"{previous_tag}..HEAD", "--", str(PACKAGES_DIR / package))
    if not subjects:
        fail(f"No commits touched {PACKAGES_DIR / package} since {previous_tag}")
    return "\n".join(f"- {subject}" for subject in subjects.splitlines())


def main():
    package = os.environ["PACKAGE"]
    prerelease = os.environ.get("PRERELEASE") == "true"
    dry_run = os.environ.get("DRY_RUN") == "true"

    name, version = load_manifest(package)
    tag = f"{name}-v{version}"
    if run("git", "tag", "--list", tag):
        fail(f"The release {tag} exists already. Bump the version in {PACKAGES_DIR / package / 'spice.toml'} first")

    previous = previous_release(package)
    if previous is not None and parse_version(version) <= previous[1]:
        fail(f"Version {version} is not newer than the latest release {previous[0]}")

    sha = run("git", "rev-parse", "HEAD")
    check_ci(sha)

    notes = os.environ.get("NOTES", "").strip() or generate_notes(package, previous and previous[0])
    print(f"Release {tag} on {sha}{' (pre-release)' if prerelease else ''}, previous: {previous and previous[0]}")
    print(notes)

    with open(os.environ.get("GITHUB_STEP_SUMMARY", os.devnull), "a") as summary:
        summary.write(f"## {'Dry run: ' if dry_run else ''}{tag}\n\n{notes}\n")

    if dry_run:
        return
    subprocess.run(
        ["gh", "release", "create", tag, "--target", sha, "--title", tag, "--notes", notes]
        + (["--prerelease"] if prerelease else []),
        check=True,
    )


if __name__ == "__main__":
    main()
