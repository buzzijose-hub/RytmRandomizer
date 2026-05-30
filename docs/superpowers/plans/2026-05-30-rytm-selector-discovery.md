# Rytm Selector Discovery Implementation Plan

> Status: in-flight (branch codex/rytm-snapshot-pad-compatibility-pr1)

**Goal:** Let explicit `amount wide` randomizer contracts explore selector-style
parameters such as BD Acoustic `Waveform` without making default live mode
riskier.

**Architecture:** Keep the behavior inside
`rytm_randomizer/engines/analog_rytm_snapshot_shell.py`. Reuse the existing
selector metadata and randomizer contract path. Add one deterministic helper for
wide selector discovery, then call it only from the `randomize` path when a pad
contract is `amount wide` and the lane policy is not micro.

**Tech Stack:** Python dataclasses, existing snapshot shell tests, pytest,
ruff, black, isort.

## File Map

- Modify `tests/test_analog_rytm_snapshot_shell.py`: add red/green tests for BD
  Acoustic `Waveform` selector edge behavior.
- Modify `rytm_randomizer/engines/analog_rytm_snapshot_shell.py`: add
  deterministic selector discovery for wide randomizer contracts.
- Modify `docs/hardware-validation/2026-05-29-rytm-live-safe-performance-session.md`:
  record selector discovery as the next hardware target.

## Steps

- [x] Add tests proving micro stays cautious and wide changes a top-edge BD
  Acoustic waveform selector.
- [x] Verify the wide selector test fails before production changes.
- [x] Implement a deterministic different-value selector helper for wide
  randomizer contracts.
- [x] Run focused snapshot-shell tests.
- [x] Update hardware-validation notes with the selector-discovery follow-up.
- [x] Run lint and full verification.

## Self-Review

- Default live commands stay cautious.
- The behavior is opt-in through `pad N amount wide`.
- Lane `off` and lane `micro` remain stronger than amount-wide discovery.
- `Z` still returns selectors to the captured anchor.
