# Dual-Machine Subpackage Cleanup Design

Date: 2026-05-18

## Purpose

Move the dual-machine milestone modules that predate PR #35's Gate 9 hardening
out of top-level `rytm_randomizer/*.py` and into focused subpackages. This is a
no-behavior-change cleanup stacked after PR #21 so the working Rytm + Analog
Four milestone remains reviewable while the architecture debt is paid down in a
separate branch.

## Current Problem

PR #35 added the top-level module guard in
`tests/architecture/test_no_new_top_level_modules.py`. PR #21 currently carries
temporary allowlist entries for the dual-machine files because those modules
were created before the guard existed. The allowlist kept the milestone moving,
but the correct long-term shape is subpackages.

## Package Layout

- `rytm_randomizer/analog_four/`: Analog Four reference data, smoke tests,
  saved-kit decoder, offset candidates, snapshot mock runtime, mutation planner,
  and starter profiles.
- `rytm_randomizer/dual_machine/`: dual-machine bridge, active send plan,
  guarded sender, hardware sender, and live snapshot readiness.
- `rytm_randomizer/sysex/`: shared SysEx bank/project analyzers and complete
  message splitting helpers.
- `rytm_randomizer/performance/`: performance mode and target selection models.
- `rytm_randomizer/essence/`: essence tag adapter, machine catalog, style intent,
  12-pad mock runtime, engine-cycle plans, and snapshot-essence send/overlay
  planning.
- Existing `rytm_randomizer/snapshot/` keeps the generic Elektron envelope
  helpers from PR #35; Rytm-specific saved-snapshot planner modules may move
  there only if doing so keeps imports simple and side-effect-free.

## Compatibility Strategy

Prefer direct import updates over long-lived shim modules. Tests and CLI imports
should move to the new package paths in the same commit series. If a public CLI
surface needs old import compatibility, use a tiny temporary shim with a clear
deprecation comment and remove it before the branch closes.

## Import Direction

The move must preserve passive import safety:

- No eager `mido` or `rtmidi` imports.
- `cli.py` remains passive and does not import active MIDI layers.
- Active hardware senders stay below app/CLI entry points.
- Data-like modules remain side-effect-free and report-only commands remain
  mock/passive unless already explicitly armed.

## Out Of Scope

This cleanup does not add new MIDI behavior, new snapshot decoding, new hardware
send paths, new engine cycling, or audio analysis. It also does not redesign the
dual-machine feature APIs beyond import paths and package placement.

## Testing

Run at least:

- `python -m pytest tests/architecture -q -n 0`
- `python -m pytest -m fast -q -n 0`
- `python -m pytest -q -n 0`
- `python -m ruff check .`
- `python -m isort --check-only --profile black rytm_randomizer tests`

The final branch should remove the temporary dual-machine Gate 9 allowlist
entries and keep GitHub required checks green.
