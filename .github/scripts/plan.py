"""Computes the test matrix of the CI workflow.

Selects the packages affected by the changes of the triggering event and writes one matrix entry per package to the
`matrix` output, with the entry file to test and the APT packages and named setup steps of the package and of the
packages it depends on. The CI requirements of a package are read from its optional `ci.toml`:

    apt = ["libgtk-4-dev"]  # APT packages to install
    setup = ["llvm"]        # named setup steps of .github/workflows/ci.yml

Environment: EVENT (github.event_name), BASE (the commit to diff HEAD against, empty or all zeros to test everything).
"""

import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path

PACKAGES_DIR = Path("packages")
# Changes to these paths affect every package
GLOBAL_PATHS = (".github/workflows/ci.yml", ".github/scripts/")
# Named setup steps, that .github/workflows/ci.yml implements
KNOWN_SETUP_STEPS = {"llvm"}
KNOWN_CI_KEYS = {"apt", "setup"}


def fail(message: str):
    print(f"::error::{message}")
    sys.exit(1)


def load_toml(path: Path) -> dict:
    try:
        return tomllib.loads(path.read_text())
    except tomllib.TOMLDecodeError as e:
        fail(f"{path}: {e}")


def load_packages() -> tuple[dict, dict]:
    manifests, ci_configs = {}, {}
    for manifest_file in sorted(PACKAGES_DIR.glob("*/spice.toml")):
        name = manifest_file.parent.name
        manifests[name] = load_toml(manifest_file)
        ci_file = manifest_file.parent / "ci.toml"
        ci = load_toml(ci_file) if ci_file.exists() else {}
        if unknown := set(ci) - KNOWN_CI_KEYS:
            fail(f"{ci_file}: unknown keys {sorted(unknown)}")
        for key, value in ci.items():
            if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
                fail(f"{ci_file}: '{key}' must be a list of strings")
        if unknown := set(ci.get("setup", [])) - KNOWN_SETUP_STEPS:
            fail(f"{ci_file}: unknown setup steps {sorted(unknown)}, known are {sorted(KNOWN_SETUP_STEPS)}")
        ci_configs[name] = ci
    return manifests, ci_configs


def changed_files() -> list[str] | None:
    """Returns the files changed by the triggering event, or None if every package has to be tested."""
    base = os.environ.get("BASE", "")
    if os.environ.get("EVENT") in ("schedule", "workflow_dispatch") or not base.strip("0"):
        return None
    result = subprocess.run(["git", "diff", "--name-only", base, "HEAD"], capture_output=True, text=True, check=True)
    return result.stdout.split()


def main():
    manifests, ci_configs = load_packages()
    names = list(manifests)
    # Dependencies on other packages of this repository
    deps = {n: {d for d in manifests[n].get("dependencies", {}) if d in manifests} for n in names}

    files = changed_files()
    if files is None or any(f.startswith(GLOBAL_PATHS) for f in files):
        selected = set(names)
    else:
        selected = {parts[1] for f in files
                    if len(parts := f.split("/")) > 2 and parts[0] == PACKAGES_DIR.name and parts[1] in manifests
                    and not f.endswith(".md")}
        # Packages, that depend on a selected package, are affected as well
        while dependents := {n for n in names if deps[n] & selected} - selected:
            selected |= dependents

    def closure(name: str, seen: set) -> set:
        if name not in seen:
            seen.add(name)
            for dep in deps[name]:
                closure(dep, seen)
        return seen

    matrix = []
    for name in sorted(selected):
        required = closure(name, set())
        matrix.append({
            "name": name,
            "entry": manifests[name]["package"]["entry"],
            "apt": sorted({a for r in required for a in ci_configs[r].get("apt", [])}),
            "setup": sorted({s for r in required for s in ci_configs[r].get("setup", [])}),
        })

    print(json.dumps(matrix, indent=2))
    if output := os.environ.get("GITHUB_OUTPUT"):
        with open(output, "a") as f:
            f.write(f"matrix={json.dumps(matrix)}\n")
    if summary := os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(summary, "a") as f:
            tested = ", ".join(f"`{e['name']}`" for e in matrix) or "none"
            f.write(f"**Packages to test:** {tested}\n")


if __name__ == "__main__":
    main()
