---
name: spice-packages-release
description: Release a new version of one package of the spicelang/packages monorepo so the Spice Rack registry and Spice Shaker pick it up — semver bump in the package's `spice.toml`, the `<name>-vX.Y.Z` tag and GitHub release format, release notes, and how the registry syncs. Use when preparing or describing a package release, or when checking why a released version does not show up on the registry.
---

# Release a package

Package versions are **GitHub releases**. The registry maps a release to a package of this monorepo by its tag: the
tag must start with the package directory (last segment or full path) followed by `-`, `/` or `@`. This repository uses
`<name>-v<version>`:

```
github-v0.2.0     gtk4-v0.1.0     libcurl-v0.1.0     sqlite-v0.1.0
```

## Steps

1. **Pick the version** (semver; while `0.x`, a breaking change bumps the minor version). Users depend on
   `^0.y.z`, so a breaking change must not ship as a patch release.
2. **Update `packages/<name>/spice.toml`** in a PR: `version` to the new version, and `spice` if the package now needs a
   newer compiler. Merge it to `main` first; CI must be green.
3. **Create the release** on `main` with tag and title `<name>-v<version>` (e.g. in the GitHub UI, or
   `gh release create github-v0.3.0 --target main --title github-v0.3.0 --notes-file notes.md`). Creating releases is
   done by a maintainer.
4. **Release notes**: a short bullet list of user-visible changes, e.g.

   ```
   - Use base64 encoding/decoding from std
   - Bump minimum required Spice version to 0.29.1
   ```

   For a first release: ``Initial release of the `<name>` package``.

5. **Registry sync**: Spice Rack refreshes stale packages in the background (packages not synced for 6 hours, a few per
   run), or immediately when a maintainer presses sync on the package's dashboard page. It reads `spice.toml` and the
   README of the package directory at the tag.

## Rules

- One release per package; never tag several packages with one tag. Releasing several packages from the same commit is
  fine (`gtk4-v0.1.0`, `libcurl-v0.1.0` and `sqlite-v0.1.0` share one).
- Never move or delete a published tag: lock files of users record the version and a checksum of its contents.
- Spice Shaker depends on the `github` package (`spicelang/spice-shaker`, `src/spice.toml`). After a `github` release
  with changes it needs, bump it there in a separate PR.
