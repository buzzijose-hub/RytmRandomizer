# Project Identity Rename Plan

## Purpose

Define a safe path for renaming the creative dream project identity while
leaving the technical repository, package, imports, CLI paths, tests, and
history untouched for now.

This is documentation-only. It does not rename code, files, imports, the
GitHub repository, or package/module names.

## Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this slice:

- `d02d494 Add progress checkpoint after structured lane coverage`

Current technical project name:

- `RytmRandomizer`

Current Python package name:

- `rytm_randomizer`

Current GitHub repository:

- `buzzijose-hub/RytmRandomizer`

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## Accepted Approach

Approach A is accepted:

- rename the creative project identity first
- keep all technical names unchanged for now
- choose and apply the new public/dream-project name in a later approved slice

This separates the creative identity from the technical engine name.

## Why This Approach

The current codebase is stable around these technical names:

- repository: `RytmRandomizer`
- package/import path: `rytm_randomizer`
- CLI module path: `python -m rytm_randomizer.cli`
- tests and fixtures that reference the existing package
- long checkpoint history that references the current repository name

Changing those technical names now would create avoidable risk and distract
from behavior-parity and mock/active planning.

The safer move is to define a creative identity layer first.

## What May Be Renamed Later

Future creative-facing references may use the new dream project name once it is
selected:

- roadmap language
- user-facing progress reports
- README/project description text
- GitHub repository description
- high-level architecture narrative
- future website/portfolio language
- future product/brand references

These surfaces can change without breaking imports, tests, or CLI usage.

## What Must Not Be Renamed Yet

Do not rename these in the first identity slice:

- `RytmRandomizer` repository name
- `rytm_randomizer` package directory
- Python imports
- CLI module path
- test module names
- fixture names
- `Scripts/closeout_check.ps1`
- historical checkpoint document names
- V1.34 reference file
- package metadata

These remain technical/stability names until a separate technical rename plan
is explicitly approved.

## Naming Status

No final new creative name has been selected yet.

Until a new name is explicitly chosen:

- creative project identity remains in planning
- technical name remains `RytmRandomizer`
- all commands and imports remain unchanged

## Future Name Selection Criteria

A good dream-project name should:

- feel musical and performance-oriented
- leave room for Analog Rytm first, and possible Analog Four later
- avoid sounding like a generic randomizer utility
- support future sound-design, performance, and hardware-control ambitions
- be easy to say out loud
- be easy to remember
- not force a technical package rename

## Current Name Shortlist

`Docs/PROJECT_IDENTITY_NAME_SHORTLIST.md` records the current docs-only
creative name shortlist.

Current leading working candidate:

- `KitForge`

Strong alternates:

- `MorphDeck`
- `AnchorEngine`

No final creative name has been adopted yet. The shortlist does not rename the
repository, package, imports, CLI paths, tests, fixtures, package metadata, or
GitHub settings.

## Safe Future Rename Path

Recommended future sequence:

1. Create a short name shortlist.
2. Select one creative/dream-project name.
3. Create a docs-only identity adoption plan.
4. Update user-facing docs and descriptions only.
5. Keep `RytmRandomizer` as the technical repository/package name.
6. Reconsider technical renaming only after the creative identity is stable.

## Non-Goals

This plan does not:

- rename the repository
- rename the Python package
- rename imports
- rename the CLI module path
- rename tests or fixtures
- edit package metadata
- change behavior
- add execution
- add MIDI
- open ports
- require hardware

## Safety Boundaries

This plan adds no:

- runtime execution
- dispatch
- command execution
- mutation execution
- active CLI command
- real MIDI
- port discovery
- port opening
- package metadata change
- active behavior
- hardware behavior

## Decision

The project may adopt a new creative dream-project identity later, but the
technical project remains `RytmRandomizer` for now.

Next recommended task:

- review and accept a creative identity candidate, or request one more
  shortlist pass with a different tone
