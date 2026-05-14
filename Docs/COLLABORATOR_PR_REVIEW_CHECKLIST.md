# Collaborator PR Review Checklist

## Purpose

Give collaborators one safe checklist for reviewing PR #2.

This document is for review and onboarding only. It does not implement code,
change tests, change package metadata, run hardware, open MIDI ports, send
MIDI, publish packages, or apply repository admin settings.

## Current Baseline

Current review branch:

- `codex/execute-eddie-plan`

Current HEAD before this slice:

- `9db8407 Add package release no-publish checklist`

Draft PR:

- <https://github.com/buzzijose-hub/RytmRandomizer/pull/2>

Base branch:

- `modularize-v1.34`

Current PR status before this checklist:

- open draft PR
- local closeout passed
- Python cross-platform closeout passed locally
- GitHub Actions passed on Windows, macOS, and Ubuntu for Python 3.11,
  3.12, and 3.13
- V1.34 current worktree diff was empty

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## First-Time Collaborator Setup

Clone the repository:

```powershell
git clone https://github.com/buzzijose-hub/RytmRandomizer.git
cd RytmRandomizer
```

Fetch the review branch:

```powershell
git fetch origin
git checkout codex/execute-eddie-plan
```

Install the development package:

```powershell
python -m pip install -e ".[dev]"
```

Run the passive project status summary:

```powershell
python -m rytm_randomizer project-status-report --summary
```

Run the full local closeout:

```powershell
powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
```

For macOS/Linux or cross-platform verification:

```bash
python Scripts/closeout_check.py
```

## Review Order

Recommended first-pass review order:

1. Read `README.md`.
2. Read `CONTRIBUTING.md`.
3. Read `Docs/PR_2_READINESS_STATUS_CHECKPOINT.md`.
4. Read `Docs/COLLABORATOR_EXECUTION_PLAN_WORKSTREAM_MAP.md`.
5. Read `Docs/BRANCH_PROTECTION_ADMIN_INSTRUCTIONS.md`.
6. Read `Docs/PACKAGE_RELEASE_NO_PUBLISH_CHECKLIST.md`.
7. Review `.github/workflows/test.yml`.
8. Review `.github/workflows/release.yml`.
9. Review `pyproject.toml`.
10. Review `Scripts/closeout_check.py`.
11. Review `Scripts/smoke_test_wheel_install.py`.
12. Review `rytm_hybrid_randomizer_v134.py` diff carefully.

## What To Confirm

Confirm that PR #2:

- keeps passive package commands passive
- keeps package entry points read-only
- keeps wheel smoke from importing real MIDI libraries in passive paths
- keeps real MIDI sending absent
- keeps MIDI port opening absent
- keeps active CLI execution absent
- keeps command dispatch absent
- keeps hardware validation absent
- keeps package publication absent
- keeps branch protection as an owner/admin follow-up
- keeps V1.34 behavior changes deliberate, reviewable, and import-safety
  focused

## What Not To Do During Review

Do not:

- turn on the Rytm
- turn on the Analog Four
- run hardware validation
- create or push `v*` release tags
- publish to PyPI or TestPyPI
- apply branch protection settings
- merge PR #2 before owner/collaborator review is complete
- treat green CI as merge approval by itself
- execute broad external plans without converting them into narrow reviewed
  slices first

## Finding Format

When reporting review findings, use this format:

```text
Severity: Critical | Important | Minor | Question
File:
Line or section:
Finding:
Why it matters:
Suggested next step:
```

Use exact file paths and line numbers when possible.

If a finding came from an AI reviewer, include the relevant text and say which
tool produced it. Screenshot-only findings are not enough for implementation;
paste the finding as text or Markdown so it can be triaged.

## Safe Review Topics

Good topics for review:

- packaging metadata accuracy
- README clarity
- contributor onboarding clarity
- CI matrix coverage
- wheel smoke behavior
- release workflow no-publish boundary
- branch protection instructions
- V1.34 import-safety diff
- passive command safety
- docs that are stale or duplicative

## Topics Requiring Separate Approval

Do not bundle these into review fixes without separate approval:

- more V1.34 edits
- broad docs deletion
- branch protection application
- package publication
- public release policy
- 100% coverage ratchet
- module consolidation
- active CLI commands
- real MIDI send path
- port opening
- hardware validation
- monolith retirement

## Expected Review Outcome

The expected near-term outcome is a written review summary, not immediate
large-scale implementation.

After review, choose one narrow next slice:

- keep PR #2 draft and address review findings
- mark PR #2 ready for review
- create a docs inventory plan
- polish contributor onboarding further
- plan package publication separately
- park PR #2 until hardware-facing work is intentionally scheduled

Hardware remains off.
