# manifest

`spice.toml`, the manifest of Spice packages: the data model, validation with helpful messages, and editing of
dependencies that keeps comments and formatting. This package is the specification of the format and the one
implementation of it that [Spice Shaker](https://github.com/spicelang/spice-shaker) (installs packages),
[Spice Rack](https://github.com/spicelang/spice-rack) (the registry) and the [Spice compiler](https://github.com/spicelang/spice)
(finds the manifest for its `[lint]` and `[format]` configuration) share.

It has two modules:

- `manifest`: model, validation and editing. It does no I/O; it only needs `String`, `Vector` and the std TOML library.
- `manifest-file`: loading and saving `spice.toml` and finding the manifest of a source file.

## Installation

```toml
[dependencies]
manifest = "^0.1.0"
```

```spice
import "spice_packages/manifest/manifest";
import "spice_packages/manifest/manifest-file"; // Only if you need file access
```

The package depends on the [semver](../semver) package, which Spice Shaker installs along with it.

## Quick start

```spice
import "std/data/vector";
import "spice_packages/manifest/manifest";
import "spice_packages/manifest/manifest-file";

f<int> main() {
    Manifest manifest;
    Vector<String> errors;
    if !loadManifest(String(MANIFEST_FILE), String(MANIFEST_FILE), manifest, errors) {
        foreach const String& error : errors {
            printf("%s\n", error.getRaw()); // e.g. spice.toml: [package] unknown key 'verison' (did you mean 'version'?)
        }
        return 1;
    }

    // Add a dependency. Comments and formatting of the rest of the file stay as they are
    if !manifest.setDependency(registryDependency(String("semver"), String("^0.1.0")), errors) { return 1; }
    if !saveManifest(manifest) { return 1; }
    printf("%s now depends on %d packages\n", manifest.name.getRaw(), cast<int>(manifest.dependencies.getSize()));
}
```

## API

### `manifest`

| Function / type | Purpose |
|-----------------|---------|
| `parseManifest(text, label, manifest, errors)` | Parse and [validate](#validation) the text of a `spice.toml`. `label` names the file in the messages, which are appended to `errors`. Returns `false` if there were errors |
| `Manifest` | `name`, `version`, `description`, `license`, `authors`, `repository`, `homepage`, `spice`, `entry`, `dependencies` and the original `text` |
| `manifest.getEntry()` | `entry`, or `src/main.spice` if it is not set |
| `manifest.indexOf(name)`, `manifest.hasDependencies()` | Look up dependencies |
| `manifest.setDependency(dep, errors)` | Add or replace a dependency, or move it between `[dependencies]` and `[dev-dependencies]`, by [editing the text](#editing) |
| `manifest.removeDependency(name, errors)` | Remove a dependency by editing the text |
| `renderManifest(manifest)` | Text of a new `spice.toml` with the metadata and dependencies of the manifest |
| `Dependency` | `name`, `source` (`DependencySource::REGISTRY`, `GITHUB` or `PATH`), `version`, `github`, `rev`, `path`, `dev` |
| `registryDependency(name, constraint)`, `githubDependency(name, repo, rev)`, `pathDependency(name, path)` | Create dependencies |
| `dep.sourceId()` | `"registry"`, `"github:owner/repo"` or `"path:<path>"`, as in the lock file |
| `dep.describe()`, `dep.ref()`, `dep.toToml()` | `"^1.2.0"` / `"github:o/r#v1"` / `"path:../x"`, the git ref (`HEAD` by default) and the value as written to the manifest |
| `isValidPackageName(name)`, `isValidRegistryName(name)`, `registryNameRule()` | The [name rules](#names) |
| `sanitizeName(text)` | Turn a dir or repository name into a valid package name |
| `isValidGithubRepo(repo)`, `isValidGitRef(ref)`, `isValidEntry(entry)` | The rules for `github`, `rev` and `entry` |
| `MANIFEST_FILE`, `LOCK_FILE`, `PACKAGES_DIR`, `DEFAULT_ENTRY`, `TABLE_*` | `spice.toml`, `spice.lock`, `spice_packages`, `src/main.spice` and the names of the top-level tables |

`parseManifest` fills the manifest as far as possible even if there are errors: it holds every valid value and every
dependency whose specification is valid on its own. Only text that is no valid TOML leaves it empty. A tool that does not
need a valid manifest, like the registry, can ignore the errors and use what was read.

### `manifest-file`

| Function | Purpose |
|----------|---------|
| `loadManifest(path, label, manifest, errors)` | Read and validate a `spice.toml` |
| `saveManifest(manifest, path = "spice.toml")` | Write the text of the manifest, with `\n` line breaks on every platform |
| `findManifest(path)` | The `spice.toml` in the dir of a source file or dir, or in the nearest parent dir. Empty if there is none |
| `manifestDisplayPath(path, baseDir)` | The path of a manifest for messages: `./spice.toml`, `../../spice.toml`, or absolute |
| `makeAbsolutePath(path)`, `getAbsoluteParentDir(path)` | The lexical path operations that `findManifest` uses |

## The format

Format version: **1**. `spice.toml` is a [TOML v1.0.0](https://toml.io/en/v1.0.0) document. The lock file `spice.lock`,
dependency resolution and the commands of Spice Shaker are specified in its
[spec](https://github.com/spicelang/spice-shaker/blob/main/media/manifest-spec.md).

### Example

```toml
[package]
name = "my-app"
version = "0.1.0"
description = "Does things"
license = "MIT"
authors = ["Jane Doe <jane@example.com>"]
repository = "https://github.com/jane/my-app"
spice = ">=0.29.0"
entry = "src/lib.spice"

[dependencies]
json-parser = "^1.2.0"
http-utils = { github = "owner/Http-Utils", rev = "v1.0.0" }
my-local = { path = "../my-local" }

[dev-dependencies]
test-kit = "~1.2.0"

[lint.rules]
too-many-parameters = { max = 8, severity = "error" }

[format]
indent-width = 2

[tool.some-linter]
max-line = 120
```

### Top-level tables

| Table                | Required | Description                                              | Validated by |
|----------------------|----------|----------------------------------------------------------|--------------|
| `[package]`          | yes      | Metadata of the package                                  | this package |
| `[dependencies]`     | no       | Dependencies needed to build and run the package         | this package |
| `[dev-dependencies]` | no       | Dependencies only needed to develop and test it          | this package |
| `[lint]`             | no       | Configuration of the linter of the compiler (`spice lint`) | the compiler |
| `[format]`           | no       | Configuration of the formatter of the compiler (`spice format`) | the compiler |
| `[tool]`             | no       | Configuration of other tools, each in `[tool.<its own name>]` | each tool |

Any other top-level key is an error. `[lint]`, `[format]` and `[tool]` have to be tables; their contents are left to the
compiler and to the other tools. The keys of `[lint]` and `[format]` are documented with the
[linter](https://github.com/spicelang/spice/blob/main/docs/docs/cli/lint.md) and the [formatter](https://github.com/spicelang/spice/blob/main/docs/docs/cli/format.md).

### `[package]`

| Key           | Type             | Required | Description |
|---------------|------------------|----------|-------------|
| `name`        | string           | yes      | Package name, see [Names](#names) |
| `version`     | string           | yes      | Version of the package, [SemVer 2.0.0](https://semver.org) without a leading `v` |
| `description` | string           | no       | One-line summary, shown by the registry for a package in a subdirectory of its repository |
| `license`     | string           | no       | [SPDX license expression](https://spdx.org/licenses/), e.g. `"MIT OR Apache-2.0"` |
| `authors`     | array of strings | no       | `"Name <email>"` or `"Name"` |
| `repository`  | string           | no       | URL of the source repository |
| `homepage`    | string           | no       | URL of the project website |
| `spice`       | string           | no       | [Version constraint](#version-constraints) on the Spice compiler |
| `entry`       | string           | no       | File consumers import, relative to the package root. Default: `src/main.spice` |

Any other key in `[package]` is an error. `entry` must be a relative path with `/` as separator, must not contain `..`
components and must end in `.spice`. Whether the file exists is not checked.

### Dependencies

`[dependencies]` and `[dev-dependencies]` map a **dependency name** to a **dependency specification**. The dependency name
is the name of the directory below `spice_packages/` and must be a valid [package name](#names). A name must not appear in
both tables.

A specification is either a string (short form) or an inline table (detailed form). The short form `"^1.2.0"` is
equivalent to `{ version = "^1.2.0" }`. Registry dependencies are always written in the short form.

| Key       | Type   | Description |
|-----------|--------|-------------|
| `version` | string | [Version constraint](#version-constraints) for a registry package |
| `github`  | string | `owner/repo` of a GitHub repository |
| `rev`     | string | Tag, branch or commit sha of the GitHub repository. Default: the repository's default branch |
| `path`    | string | Path of a local package, relative to the project root, with `/` as separator |

Exactly one of `version`, `github` and `path` must be present. `rev` is only allowed together with `github`. Any other key
is an error. The name of a registry dependency is the name of the package in the registry, so it must also be a valid
[registry name](#names).

**Format restriction.** Every dependency must be written as a single `name = value` line inside a `[dependencies]` or
`[dev-dependencies]` section. The table headers must be written exactly like that (bare keys, optionally surrounded by
spaces inside the brackets). Sub-tables (`[dependencies.foo]`), dotted keys (`foo.version = "1.0"`), quoted dependency
names and a top-level `dependencies = { ... }` are errors. This keeps [editing](#editing) simple and safe; TOML does not
allow line breaks inside inline tables, so the restriction costs no expressiveness.

### Names

**Package names**, which includes all dependency names, consist of lower-case ASCII letters, digits, `-` and `_`, start
with a letter or digit and are at most 64 characters long. They are safe to use as a directory name and on a command line.

**Registry names** are the names under which packages are published to Spice Rack. They are stricter: lower kebab-case,
2-64 lower-case letters and digits in words separated by single `-`, like `my-package`. Every registry name is a package
name. A package that will never be published, or that is used as a GitHub or path dependency, only needs a package name.

### Version constraints

A constraint is a list of clauses separated by commas and/or spaces. A version satisfies the constraint if it satisfies
every clause. The rules are implemented by the [semver](../semver) package.

| Clause              | Matches                                                 |
|---------------------|---------------------------------------------------------|
| `1.2.3`, `=1.2.3`   | exactly `1.2.3`                                          |
| `^1.2.3`            | `>=1.2.3, <2.0.0`; `^0.2.3` = `>=0.2.3, <0.3.0`; `^0.0.3` = `>=0.0.3, <0.0.4` |
| `~1.2.3`            | `>=1.2.3, <1.3.0`                                        |
| `1.2.x`, `1.x`      | `>=1.2.0, <1.3.0` and `>=1.0.0, <2.0.0`                  |
| `>=`, `>`, `<=`, `<` followed by a version | comparison                        |
| `*`                 | any version                                              |

Versions in constraints may omit minor and patch (`^1` = `^1.0.0`). Versions published to the registry may have a leading
`v` (from git tags), which is ignored. Pre-releases sort before their release.

### Validation

A manifest is rejected if any of the following holds. The error message names the file, the table and the key; for an
unknown key it suggests the known key with the smallest edit distance, if that distance is at most 2.

- It is not valid TOML.
- `[package]`, `package.name` or `package.version` is missing.
- A value has the wrong type, or `[lint]`, `[format]` or `[tool]` is no table.
- There is an unknown key at the top level, in `[package]` or in a dependency specification.
- `name` or a dependency name is not a valid package name, or the name of a registry dependency is not a valid registry name.
- `version` is not valid SemVer, or a constraint (`spice`, a dependency `version`) is not a valid constraint.
- `entry` violates the rules of [`[package]`](#package).
- A dependency specification has no source, more than one source, or `rev` without `github`.
- `github` is not `owner/repo` (letters, digits, `-`, `_` and `.` each), or `rev` contains characters other than letters,
  digits, `-`, `_`, `.` and `/`.
- `path` is empty or contains `\`.
- A name is in both `[dependencies]` and `[dev-dependencies]`.
- The [format restriction](#dependencies) is violated.

### Editing

Editing the dependencies keeps the manifest as the user wrote it: comments, blank lines, key order and formatting of every
line that is not affected.

**Reading.** The file is parsed with `parseToml` from `std/text/toml/toml-parser`, and the resulting tree is
[validated](#validation). Additionally, a line scanner locates each dependency line. The scanner

- skips the contents of multi-line strings (`"""` and `'''`),
- recognizes table headers (`[name]` and `[[name]]`, optionally followed by a comment), and
- inside `[dependencies]` and `[dev-dependencies]` recognizes lines of the form `<bare key> = <value> [# comment]`, using a
  small lexer (basic strings with escapes, literal strings, braces and brackets) to find where the value ends and the
  comment begins.

Every dependency in the parsed tree must be found by the scanner in the matching section; if one is not, the manifest
violates the [format restriction](#dependencies) and is rejected.

**Writing.** The parsed tree is not serialized back. Instead, the original text is edited line by line:

- The value of a dependency is formatted from `TomlValue`s with `TomlSerializer.serializeValue`: a string for the short
  form, or `{ key = value, ... }` with the keys in the order `version`, `github`, `rev`, `path`.
- **Changing** a dependency replaces the value of its line and keeps the comment at the end of the line.
- **Adding** a dependency inserts `name = value` after the last dependency line of the section, or directly after the
  section header if the section is empty. If the section does not exist, a blank line, the header and the dependency line
  are appended to the end of the file.
- **Removing** a dependency deletes its line.
- Moving a dependency between `[dependencies]` and `[dev-dependencies]` is a removal followed by an addition.

**Verification.** The edited text is parsed and validated again, and the edit is only taken over if the result contains
exactly the intended dependencies. This guards against bugs in the line editing.

A new manifest (`renderManifest`) has no user content to preserve; it is written with `TomlSerializer`.

### Finding the manifest

Spice Shaker only uses the `spice.toml` of the directory it is invoked from. The compiler uses the `spice.toml` in the
directory of the main source file or in the nearest of its parent directories (`findManifest`). The parent directories are
determined lexically, like a shell does it for `cd ..`, so that a symlinked directory is searched from where it is linked.

### Out of scope

The format leaves room for these, but this version does not specify them:

- **Workspaces**: multiple packages sharing one `spice.lock` and `spice_packages/` (`[workspace]` table).
- **Target-specific dependencies**, e.g. `[target.windows.dependencies]`.
- **Features and optional dependencies**: `optional = true` in the detailed form, plus a `[features]` table.
- **Renaming**: installing a registry package under another dependency name (a `package` key in the detailed form).
- **Import by package name**: `import "@json-parser";` resolving to the `entry` of the package.
- **Scripts / tasks** (npm `scripts`). These can live under `[tool.<name>]` for now.
