---
name: spice-packages-contribute
description: Guidelines for contributing changes to the Official Spice Packages GitHub repository (spicelang/packages) — branch naming conventions (enforced by a hook), commit message format, PR workflow, no-push-to-main rule, and quality gates. Use when preparing a branch for review, writing a commit, opening a PR, or checking that a contribution is ready to merge.
---

# Contribute to Official Spice Packages

This skill covers the full contribution workflow: naming branches, writing commits, opening a PR, and satisfying the
quality gates before merge. It follows the conventions of the main [Spice repository](https://github.com/spicelang/spice).

## Branch naming

All work happens on a dedicated branch, never directly on `main`. Never use auto-generated or `claude/...` branch names.

| Prefix | Use for |
|--------|---------|
| `feature/<slug>` | New packages or new API in a package (start the slug with the package name: `feature/github-gists`) |
| `fix/<slug>` (or `bug/<slug>`) | Bug fixes in a package (`fix/sqlite-null-columns`) |
| `chore/<slug>` | Version bumps, dependency updates, repo maintenance |
| `ci/<slug>` | GitHub Actions workflows |
| `test/<slug>` | New or updated package tests |
| `docs/<slug>` | README-only changes |
| `security/<slug>` | Security-sensitive fixes (prefer non-public disclosure first — see `SECURITY.md`) |

Rules:
- Use lowercase `kebab-case` slugs (`feature/github-gists`, not `Feature/GithubGists`).
- Keep slugs short but descriptive; the squash-commit headline is taken from the PR title.
- Tie the slug to the issue number when one exists: `fix/42-sqlite-null-columns`.
- If the session starts on a pre-created branch, rename it with `git branch -m <type>/<slug>` before the first push.
- This is enforced by the `.claude/hooks/check-branch-name.py` hook, which blocks git commands that create, rename or
  push a branch with a non-conforming name.

```sh
git checkout main
git pull origin main
git checkout -b feature/github-gists
```

## Commit message format

Use a short, descriptive headline — no type prefix or scope annotation:

```
<Short descriptive headline>

[optional body — explain WHY, not what]

[optional footer — Fixes #<issue>, Refs #<issue>, Co-authored-by: …]
```

Examples from this repository's history:

```
Add gtk4, libcurl and sqlite packages, moved from the std

Use the std base64 encoder/decoder in the github package

Add CI workflow, that tests all packages with the latest Spice release
```

Rules:
- Headline ≤ 72 characters, imperative mood ("Add", "Fix", not "Added", "Fixes").
- No trailing period on the headline.
- Blank line between headline and body.
- Reference issues in the footer with `Fixes #N` (auto-closes) or `Refs #N`.

## No-push-to-main rule

`main` only receives changes through pull requests. Never `git push origin main`; push the branch
(`git push -u origin <type>/<slug>`) and open a PR. If you accidentally committed to `main` locally, move the work to a
branch before pushing:

```sh
git checkout -b <type>/<slug>          # create branch at current HEAD
git checkout main
git reset --hard origin/main           # restore main to remote state
git checkout <type>/<slug>             # continue on the branch
```

## Repository rules

- Name the package in the headline when a change touches one package ("... in the github package").
- Follow the [Spice Coding Style Guide](https://github.com/spicelang/spice/blob/main/STYLE_GUIDE.md) for all Spice code.
- Packages must build with the **latest Spice release** (that is what CI uses), not with an unreleased compiler.
- Version bumps and releases follow the `spice-packages-release` skill; a PR that changes a package's public API says
  whether it is breaking.

## Pre-PR quality gate

Run the CI test loop for the packages you touched (details in the `spice-packages-develop` skill):

```sh
export SPICE_STD_DIR=/path/to/spice/std
(cd packages/<name> && spice test -O0 <name>.spice)
```

For a new package also check the root README table, `.github/labeler.yml` and, for bindings, the CI `apt-get` line.

If the environment cannot run a check, say so explicitly in the PR description. Do not silently skip checks.

## Opening the pull request

Target branch: **`main`**. The PR title uses the same style as commit headlines: short, descriptive, imperative mood,
no type prefix.

PR description template:

```markdown
## What changed
<!-- 1-3 bullets describing the change -->

## Why
<!-- Motivation, linked issue, or design rationale -->

## How it was validated
<!-- Exact commands run + outcome, e.g.: -->
- `cd packages/github && spice test -O0 github.spice` — all pass (Spice 0.29.1)
- Ran the quick start example from the README — works

## Follow-up / known limitations
<!-- Anything deferred, or limitations the reviewer should know -->

Fixes #<issue>
```

Additional rules:
- Keep PRs focused — one logical change per PR.
- One package per PR, unless a change has to land in several packages together.
- Update the package README when its API, installation steps or requirements change.
- Do not force-push a branch that already has a PR open (use a new commit instead) unless a reviewer explicitly asks
  for a rebase.

## Merge strategy

PRs are merged by a maintainer using **squash and merge** — every PR lands as a single commit on `main` with the PR
title as headline. Write clean incremental commits on your branch so the reviewer can follow the progression.

## Checklist

- [ ] Branch named `<type>/<slug>` with an allowed type and a descriptive slug
- [ ] All commits have a short descriptive headline (no type prefix)
- [ ] Tests of the changed packages pass with the latest Spice release
- [ ] Package README updated if the API or requirements changed
- [ ] New package: root README table, labeler entry, CI system libraries
- [ ] Breaking changes called out for the next version bump
- [ ] Issue linked in footer (`Fixes #N` or `Refs #N`)
- [ ] PR targets `main`
