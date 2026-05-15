# Collaborator Quickstart

## Purpose

Give collaborators a short, safe way to pull the repository, understand the
current branch, run the passive status checks, and send useful review findings.

This document is for collaborator orientation only. It does not implement
code, tests, package metadata, MIDI, active behavior, runtime execution, or
hardware behavior.

## Current Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this slice:

- `05085e1 Add collaborator triage template visibility checkpoint`

Current phase:

- Passive/Mock Runtime Visibility Phase

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## Pull The Current Branch

From an existing clone:

```powershell
git fetch origin
git switch modularize-v1.34
git pull --ff-only origin modularize-v1.34
```

If the branch does not exist locally yet:

```powershell
git fetch origin
git switch -c modularize-v1.34 origin/modularize-v1.34
```

## First Status Check

Run the quick passive status helper:

```powershell
powershell -ExecutionPolicy Bypass -File .\Scripts\quick_status.ps1
```

Expected safe status:

- project status check `ok: True`
- real MIDI: `absent`
- port opening: `absent`
- active execution: `absent`
- hardware required: `False`
- V1.34 reference: `untouched`
- git status clean, unless the collaborator intentionally has local notes

## Full Closeout

Before reporting a ready-to-review local change, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
```

The closeout suite is the project safety gate. It checks passive behavior,
mock-only behavior, behavior-parity coverage, real MIDI import safety, runtime
planning boundaries, active boundary reports, and protected-file state.

## Useful Passive CLI Commands

These commands are read-only:

```powershell
python -m rytm_randomizer.cli project-status-report --summary
python -m rytm_randomizer.cli project-status-report --check
python -m rytm_randomizer.cli behavior-parity-report
python -m rytm_randomizer.cli active-boundary-report
python -m rytm_randomizer.cli runtime-plan-report
python -m rytm_randomizer.cli mock-runtime-active-bridge-report
```

Do not add or run active execution commands. None are authorized in the current
phase.

## How To Send Review Findings

Send findings as text or Markdown.

Use this shape when possible:

```text
ID:
Severity:
Finding:
Affected files:
Affected lines:
Why it matters:
Suggested change:
Evidence:
```

Screenshots are useful for context, but screenshot-only findings are not
enough for implementation. Findings should be pasted as text so they can be
searched, quoted, verified, and triaged.

The accepted triage template is:

- `Docs/COLLABORATOR_REVIEW_TRIAGE_TEMPLATE.md`

The accepted triage template review is:

- `Docs/COLLABORATOR_REVIEW_TRIAGE_TEMPLATE_REVIEW.md`

## Safety Boundaries

Do not introduce these without separate explicit approval:

- real MIDI
- `mido`
- `rtmidi`
- MIDI port opening
- MIDI sending
- active CLI commands
- dispatch
- command execution
- runtime execution
- hardware behavior
- SysEx
- GUI/capture
- Analog Four support
- Pads 5-12 support
- package metadata changes
- changes to `rytm_hybrid_randomizer_v134.py`

## Protected Reference

`rytm_hybrid_randomizer_v134.py` is the protected V1.34 behavior reference.

Collaborator review may inspect it, but should not edit it unless Jose gives
separate explicit approval.

## Package Metadata Boundary

Packaging and distribution feedback is welcome, but package metadata changes
are not automatic quick fixes in this phase.

Do not change these without separate explicit approval:

- `pyproject.toml`
- `requirements.txt`
- `setup.py`
- `setup.cfg`

## Review Workflow

Recommended flow:

1. Pull `modularize-v1.34`.
2. Run quick status.
3. Read `Docs/NEXT_ACTION.md`.
4. Run passive CLI/status commands as needed.
5. Send findings as text or Markdown.
6. Wait for findings to be triaged before implementation.
7. Keep changes narrow, test-backed, and closeout-clean.

## Current Decision

Collaborator review is welcome and useful.

External findings remain advisory until verified locally and classified.

The project remains passive/mock-only, hardware-off, and protected by
closeout.

## Next Recommended Task

If review findings arrive:

- create a filled collaborator review triage document
- classify findings before implementation

If no findings have arrived:

- continue with safe passive/mock-only behavior parity, visibility, or
  documentation work
