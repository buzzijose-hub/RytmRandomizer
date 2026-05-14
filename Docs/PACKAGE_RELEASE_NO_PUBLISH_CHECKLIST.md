# Package Release No-Publish Checklist

## Purpose

Document package release readiness without publishing anything.

This checklist exists because PR #2 adds package metadata, package build
verification, wheel install smoke testing, and a tag-triggered release
workflow scaffold. It clarifies what can be safely checked before any public
package release or package registry publication is considered.

This is documentation-only. It does not tag a release, upload artifacts,
publish to PyPI, change package metadata, add runtime behavior, open ports,
send MIDI, or touch hardware.

## Current Baseline

Current review branch:

- `codex/execute-eddie-plan`

Current HEAD before this slice:

- `e5910f4 Add branch protection admin instructions`

Draft PR:

- <https://github.com/buzzijose-hub/RytmRandomizer/pull/2>

Package name:

- `rytm-randomizer`

Current package version:

- `1.34.0`

Current release workflow:

- `.github/workflows/release.yml`

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## Current Release Workflow Behavior

The current release workflow runs only on pushed tags matching:

- `v*`

Current workflow behavior:

- checks out the repository
- sets up Python 3.13
- installs `build`
- runs `python -m build`
- uploads `dist/*` as GitHub Actions artifacts

Current workflow does not:

- publish to PyPI
- publish to TestPyPI
- create a GitHub Release
- attach artifacts to a GitHub Release
- sign artifacts
- run hardware validation
- open MIDI ports
- send MIDI

## No-Publish Release Readiness Checklist

Before creating any release tag, confirm:

- PR #2 has been reviewed.
- GitHub Actions are green on the final PR head.
- `pyproject.toml` metadata has been reviewed.
- package name is intentional.
- package version is intentional.
- license decision is intentional.
- dependency declarations are intentional.
- README install and run instructions are accurate.
- `CHANGELOG.md` has a useful entry for the release.
- `SECURITY.md` is acceptable for the current repo state.
- `CONTRIBUTING.md` is acceptable for collaborators.
- V1.34 import-safety diff has been reviewed.
- passive CLI behavior remains passive.
- wheel install smoke passes.
- package import does not import real MIDI libraries in passive paths.
- no active CLI command has been added.
- no real MIDI send path has been added.
- no hardware validation is implied.

## Local Dry-Run Commands

Recommended local dry-run:

```powershell
python -m pip install -e ".[dev]"
python -m pytest
python -m pytest --cov=rytm_randomizer --cov-branch --cov-fail-under=84
python -m build
python .\Scripts\smoke_test_wheel_install.py
powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
python .\Scripts\closeout_check.py
git diff -- rytm_hybrid_randomizer_v134.py
git status --short
```

Expected dry-run result:

- all tests pass
- coverage gate passes
- package build passes
- wheel install smoke passes
- closeout passes
- cross-platform closeout passes
- V1.34 current worktree diff is empty
- git status is clean

## Tag Dry-Run Rules

Do not create a real `v*` tag until the owner chooses to exercise the release
workflow.

If testing tag behavior later, use a separate approved release-test slice.

Do not push tags casually. A pushed `v*` tag will trigger the release
workflow.

## Publishing Boundary

Publishing to a package registry is not part of the current PR.

Before any PyPI or TestPyPI publication is added:

- write a separate package publication plan
- decide public/private distribution policy
- decide versioning policy
- decide release ownership
- decide package signing/artifact retention expectations
- add a reviewed publish workflow
- verify publish credentials are scoped safely
- keep hardware unrelated to package publication

## Safety Boundaries

This checklist does not authorize:

- public release
- package registry publication
- PyPI upload
- TestPyPI upload
- creating or pushing a release tag
- changing version numbers
- changing license policy
- making the repository public
- real MIDI behavior
- MIDI port opening
- MIDI sending
- active CLI execution
- command dispatch
- hardware validation
- hardware use

## Recommended Next Task

Review PR #2 with Eddie.

After PR review, choose one:

- keep PR #2 draft and update findings
- mark PR #2 ready for review
- merge PR #2 after approval and green checks
- create a docs inventory plan
- polish contributor onboarding
- create a separate package publication plan later

Hardware remains off.
