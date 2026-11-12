# semver

[Semantic versions](https://semver.org) and version constraints for Spice: parsing, comparison, constraint matching and
picking the best version out of a list. These are the rules [Spice Shaker](https://github.com/spicelang/spice-shaker)
uses to resolve dependencies and [Spice Rack](https://github.com/spicelang/spice-rack) uses to show them, as specified
in the [manifest spec](https://github.com/spicelang/spice-shaker/blob/main/media/manifest-spec.md#version-constraints).
Pure Spice that only uses `String` and `Vector`, so it also builds for WebAssembly.

## Installation

```toml
[dependencies]
semver = "^0.1.0"
```

```spice
import "spice_packages/semver/semver";
```

## Quick start

```spice
import "std/data/vector";
import "spice_packages/semver/semver";

f<int> main() {
    Semver version = parseSemver(String("v1.4.2"));
    const String text = version.toString();
    printf("%s\n", text.getRaw()); // 1.4.2

    if satisfies(version, String("^1.2.0")) {
        printf("1.4.2 satisfies ^1.2.0\n");
    }

    Vector<String> tags;
    tags.pushBack(String("v1.0.0"));
    tags.pushBack(String("v1.3.0"));
    tags.pushBack(String("v2.0.0"));
    const long best = pickBestVersion(tags, String("^1.0.0"));
    if best >= 0l {
        const String& tag = tags.get(cast<unsigned long>(best));
        printf("Best match: %s\n", tag.getRaw()); // v1.3.0
    }
}
```

## Versions

`parseSemver` accepts `1.2.3`, a leading `v` (`v1.2.3`, as in git tags), missing minor and patch numbers (`1.2` =
`1.2.0`), a pre-release (`1.2.3-beta.1`) and build metadata (`1.2.3+build`, dropped). Anything else gives a `Semver` with
`valid == false`.

| Function / field       | Purpose                                                                         |
|------------------------|---------------------------------------------------------------------------------|
| `Semver`               | `major`, `minor`, `patch`, `pre` (pre-release, empty for a release), `valid`    |
| `parseSemver(text)`    | Parse a version                                                                 |
| `isStrictSemver(text)` | Complete version without `v`, as required for `package.version` in `spice.toml` |
| `version.toString()`   | `major.minor.patch`, followed by `-pre` for a pre-release                       |
| `compareSemver(a, b)`  | `-1`, `0` or `1`. A pre-release sorts before its release                        |

## Constraints

A constraint is a list of clauses separated by commas and/or spaces. A version satisfies the constraint if it satisfies
every clause.

| Clause                                   | Matches                   |
|------------------------------------------|---------------------------|
| `*`                                      | Any version               |
| `1.2.3`, `=1.2.3`                        | Exactly 1.2.3             |
| `^1.2.3`                                 | `>=1.2.3, <2.0.0`         |
| `^0.2.3`                                 | `>=0.2.3, <0.3.0`         |
| `^0.0.3`                                 | `>=0.0.3, <0.0.4`         |
| `~1.2.3`                                 | `>=1.2.3, <1.3.0`         |
| `1.2.x`, `1.2.*`                         | `>=1.2.0, <1.3.0`         |
| `1.x`                                    | `>=1.0.0, <2.0.0`         |
| `>=1.2.3`, `>1.2.3`, `<=1.2.3`, `<1.2.3` | Comparison with a version |

Versions in clauses may omit minor and patch (`^1` = `^1.0.0`), and an operator may be separated from its version by a
space (`>= 1.0, < 2.0`).

| Function                                | Purpose                                                                                                                                      |
|-----------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------|
| `isValidConstraint(constraint)`         | Check the syntax of a constraint                                                                                                             |
| `satisfies(version, constraint)`        | Check a version against a constraint. Invalid versions or constraints match nothing                                                          |
| `pickBestVersion(versions, constraint)` | Index of the highest version in a list of strings that satisfies the constraint, or `-1`. Pre-releases are only picked if no release matches |
