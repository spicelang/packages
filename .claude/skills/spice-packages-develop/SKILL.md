---
name: spice-packages-develop
description: Add a new official Spice package to spicelang/packages or change an existing one (github, gtk4, libcurl, sqlite) — the per-package directory layout, `spice.toml` fields, entry file, README, binding packages that link system libraries via `core.*.linker.flag`, the repo files to update (root README table, labeler, CI apt packages), unit tests and how to run them locally exactly like CI. Use when creating, extending or testing a package in this monorepo.
---

# Develop a package in spicelang/packages

This repository is a monorepo: every package lives in its own directory `packages/<name>/` with its own `spice.toml`
and README. The [Spice Rack](https://github.com/spicelang/spice-rack) registry lists each one separately (it is created
there with the directory as `repo_path`), and [Spice Shaker](https://github.com/spicelang/spice-shaker) installs only
that directory to `spice_packages/<name>/` of the user's project. The manifest format is specified in Spice Shaker's
`media/manifest-spec.md`.

## Package layout

```
packages/<name>/
  spice.toml        manifest (below)
  <name>.spice      entry file: the public API users import
  src/*.spice       optional internal modules, imported from the entry file as "src/<module>"
  README.md         shown on the registry page
  .gitignore        /spice_packages/
```

```toml
[package]
name = "<name>"                 # lower kebab-case, same as the directory
version = "0.1.0"
description = "One line, shown on the registry instead of the repository description"
license = "MIT"
authors = ["Marc Auberer <marc.auberer@chillibits.com>"]
repository = "https://github.com/spicelang/packages"
spice = ">=0.29.0"              # minimum compiler; raise it when you use newer std or language features
entry = "<name>.spice"          # CI tests this file

[dependencies]
```

Users import the entry file without the extension: `import "spice_packages/<name>/<name>";`.

## Binding packages (gtk4, libcurl, sqlite)

Bindings declare the C functions with `ext f<…> name(…);` and wrap them in Spice types. They link the system library
through module attributes at the top of the entry file:

```spice
#![core.compiler.warnings.ignore]
#![
    core.linux.linker.flag = "`pkg-config --cflags --libs sqlite3`",
    core.darwin.linker.flag = "`pkg-config --cflags --libs sqlite3`",
    core.windows.linker.flag = "-lsqlite3"
]
```

A new system library needs its development package in the `apt-get install` line of `.github/workflows/ci.yml` and a
per-platform table (Debian/Ubuntu, Fedora, macOS, Windows) in the package README, like the existing bindings.

## Adding a package — checklist

1. `packages/<name>/` with the files above (copy the `.gitignore` of an existing package).
2. README: one-line intro, `## Installation` (the `[dependencies]` snippet and the import line), `## Quick start` with a
   complete `main`, then the API. Use `spice` fenced code blocks; the registry highlights them.
3. Row in the package table of the root `README.md` (keep it alphabetical and the columns aligned).
4. Label entry in `.github/labeler.yml` (`'<name>': packages/<name>/**/*`). The label itself must exist in the GitHub
   repository; ask a maintainer to create it.
5. Unit tests (below). Release it afterwards with the `spice-packages-release` skill.

## Tests

Tests are `#[test]` functions in the package sources, usually in a "Tests" section at the end of the file:

```spice
#[test]
f<bool> testPaths() {
    assert repoPath("spicelang", "spice") == "/repos/spicelang/spice";
    return true;
}
```

Tests must not need the network or a display (CI has neither GitHub credentials nor a GUI); test the pure parts such
as parsing, encoding and path building.

CI (`.github/workflows/ci.yml`) installs the **latest Spice release** and runs, for every `packages/*/spice.toml`:

```sh
cd packages/<name> && spice test -O0 <entry>
```

Run the same locally, with the std of the compiler you use:

```sh
export SPICE_STD_DIR=/path/to/spice/std        # for a release archive: <archive dir>/std
(cd packages/github && spice test -O0 github.spice)
for m in packages/*/spice.toml; do d=$(dirname "$m"); e=$(sed -n 's/^entry *= *"\(.*\)"/\1/p' "$m"); (cd "$d" && spice test -O0 "$e") || echo "FAILED: $d"; done
```

Binding packages need the system libraries installed to link (`libgtk-4-dev libcurl4-openssl-dev libsqlite3-dev` on
Debian/Ubuntu). Since CI uses the latest release, a package may only use std APIs and language features that are
released; if a change needs an unreleased compiler, it has to wait for the next Spice release.

CI does not install package dependencies. A package with a non-empty `[dependencies]` table needs that step added to
the workflow (e.g. `spice-shaker sync` in its directory) first.
