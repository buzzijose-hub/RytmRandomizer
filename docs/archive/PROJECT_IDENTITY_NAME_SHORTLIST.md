# Project Identity Name Shortlist

> STATUS: PARKED — not an active workstream as of 2026-05-14. The project ships as rytm-randomizer until/unless this is revisited.

## Purpose

Provide a short creative-name shortlist for the broader dream project while
keeping all technical project names unchanged.

This is documentation-only. It does not rename the repository, package,
imports, CLI path, tests, fixtures, package metadata, files, or GitHub
settings.

## Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this slice:

- `de6d327 Add project identity rename plan`

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

## Naming Boundary

The new name under discussion is the creative dream-project identity only.

These remain unchanged:

- repository name: `RytmRandomizer`
- package/import name: `rytm_randomizer`
- CLI path: `python -m rytm_randomizer.cli`
- tests and fixtures
- package metadata
- historical checkpoint document names
- V1.34 reference file

## Selection Criteria

A strong creative identity should:

- feel musical and performance-oriented
- support sound design, randomization, anchors, morphing, and live control
- leave room for Analog Rytm first and possible Analog Four later
- avoid sounding like only a generic randomizer utility
- be easy to say out loud
- be easy to remember
- coexist with `RytmRandomizer` as the technical engine name
- avoid public confusion with Elektron, Analog Rytm, Analog Four, Overbridge,
  or other protected product names

No legal, trademark, domain, or app-store availability check has been
performed.

## Recommended Top Candidates

### KitForge

Why it fits:

- short and memorable
- strongly connected to drum kit creation and sound design
- suggests deliberate building rather than uncontrolled randomness
- broad enough to include Rytm kits, future Analog Four ideas, and larger
  performance workflows
- works as a creative identity while the technical repo remains
  `RytmRandomizer`

Current position:

- leading working candidate

### MorphDeck

Why it fits:

- suggests performance control, state changes, and morphing
- feels like a playable system rather than a one-off script
- leaves room for future hardware surfaces and scene-like workflows

Current position:

- strong alternate if the project identity should emphasize live control and
  transformation

### AnchorEngine

Why it fits:

- connects directly to the project's anchor and safe-return concepts
- suggests a controlled engine rather than a random-only tool
- matches the safety-first design language already used in the docs

Current position:

- strong alternate if the project identity should emphasize stable anchors,
  recovery, and safe exploration

## Additional Candidate Pool

Other possible directions:

- PulseFoundry
- PatternFoundry
- MotionKit
- DriftKit
- KitPilot
- SignalForge
- MachineGarden
- SoundPilot

These are not selected. They are useful for exploring tone and direction.

## Names To Avoid For Now

Avoid names that:

- rely on `Elektron`, `Analog Rytm`, `Analog Four`, or `Overbridge` as the
  core identity
- sound like an official manufacturer product
- force a package/import rename
- make the project sound like only a randomizer
- imply real-time hardware execution before that layer exists

## Current Recommendation

Use `KitForge` as the leading working creative identity candidate.

Keep these as alternates:

- `MorphDeck`
- `AnchorEngine`

Do not adopt any name yet. The next step should be a short name
review/acceptance checkpoint.

## Non-Goals

This shortlist does not:

- choose the final name
- rename the repository
- rename the Python package
- rename imports
- rename CLI paths
- rename tests or fixtures
- edit package metadata
- change behavior
- add execution
- add MIDI
- open ports
- require hardware

## Safety Boundaries

This shortlist adds no:

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

The creative identity remains undecided.

The leading working candidate is:

- `KitForge`

The next recommended task is:

- review and accept a creative identity candidate, or request one more
  shortlist pass with a different tone
