# Dual-Machine Strategy Redo Migration Map

## Source Material

- PR #36: architecture review source for the redo.
- PR #36 state at review intake: open, dirty, changes requested.
- PR #43: merged governance and Device Strategy architecture baseline.
- Closed stacked PRs #37-#41: source material only; do not reopen the cascade.
- PR #21 and the older Analog Four work: historical reference only; consume useful behavior through the PR #43 architecture.

## Review Direction

Eddie's PR #36 review accepts the product intent: Rytm, Analog Four, and both-machine flows are the right direction. The required redo is architectural:

- Use the `Device` Protocol Strategy surface added by PR #43.
- Add one registered `AnalogFourDevice`.
- Put A4 decode, planning, and rendering behind strategies under `rytm_randomizer/devices/strategies/`.
- Keep `dual_machine` as orchestration/reporting only.
- Collapse duplicate senders into generic sender modules.
- Keep one bundled PR against `modularize-v1.34`; do not reopen the stacked cascade.

## Migration Table

| Old surface | New home | Action |
|---|---|---|
| `rytm_randomizer/analog_four/snapshot_decoder.py` | `rytm_randomizer/devices/strategies/analog_four_snapshot_decoder.py` | Migrate public decode behavior behind `AnalogFourSnapshotDecoder.decode(raw, slot)`. |
| `rytm_randomizer/analog_four/snapshot_mock_runtime.py` | `rytm_randomizer/devices/strategies/analog_four_message_renderer.py` and `rytm_randomizer/senders/guarded.py` | Split pure rendering from sending. |
| `rytm_randomizer/analog_four/controlled_diff.py` | `rytm_randomizer/devices/strategies/analog_four_mutation_planner.py` | Keep planning intent; remove cross-family private imports. |
| `rytm_randomizer/analog_four/offset_candidates.py` | `rytm_randomizer/devices/strategies/analog_four_snapshot_decoder.py` or a small strategy-owned manifest module | Keep candidate offset facts behind the A4 strategy boundary. |
| `rytm_randomizer/dual_machine/*` | `rytm_randomizer/dual_machine/targets.py` and `rytm_randomizer/dual_machine/reports.py` | Keep orchestration/reporting only; depend on `devices.all_devices()`. |
| per-device sender modules | `rytm_randomizer/senders/guarded.py` and `rytm_randomizer/senders/hardware.py` | Collapse duplicate arm-gate, dry-run-gate, ready-gate, render-and-send logic. |
| Rytm engine internals under `essence/` or `rytm/` | existing `data/`, `engines/`, or `devices/strategies/` modules | Do not create parallel device subpackages. |
| `rytm_randomizer/sysex/*` bank analyzers | existing `snapshot/` helpers or strategy-owned modules | Keep shared SysEx envelope behavior in `snapshot/envelope.py`; keep family-specific interpretation behind strategies. |

## Preserved Operator Contracts

- `rytm` / `rytm-only`
- `a4` / `a4-only`
- `both`
- Snapshot mode as the primary live-performance workflow.
- Anchor mode retained as an explicit controlled baseline.
- Manual hardware validation only; automated tests must not open MIDI ports or send MIDI.

## Device Strategy Shape

`AnalogFourDevice` belongs at `rytm_randomizer/devices/analog_four.py` as a sibling of `analog_rytm.py`. Importing `rytm_randomizer.devices` should register both devices through `devices/registry.py`.

The A4 device composes:

- `AnalogFourSnapshotDecoder`
- `AnalogFourMutationPlanner`
- `AnalogFourMessageRenderer`

The convenience methods on `AnalogFourDevice` should delegate to those strategies, matching `AnalogRytmDevice`.

## Readiness Policy

Analog Rytm is the mature reference device. Analog Four starts as candidate/manifest-gated until kit offsets and outbound mappings are promoted by tests and manual review.

The readiness state belongs on the returned mutation plan:

- `ready=False`
- a human-readable `readiness_reason`
- enough planned context for passive reports

The generic guarded sender must refuse not-ready plans cleanly. No per-family sender should contain a special A4 readiness check.

## Dropped Or Deferred

- GUI implementation.
- Audio analyzer.
- Genre prompt kit generation.
- Continuous knob tracking.
- Automated hardware sends in tests.
- Reopening the old stacked PR cascade.

## Architecture Guardrails

- No new `rytm_randomizer/analog_four/` package.
- No new `rytm_randomizer/rytm/` package.
- No new `rytm_randomizer/essence/` package.
- No parallel `register_device` definitions.
- No `dual_machine` imports from concrete device-family modules.
- No cross-family private imports.
- No architecture-test allowlist entries unless the PR body explains a reviewer-approved exception.

## Implementation Status

- Design checkpoint committed on branch `codex/dual-machine-strategy-redo`.
- Detailed implementation plan committed at `docs/superpowers/plans/2026-05-19-dual-machine-strategy-redo.md`.
- `AnalogFourDevice` registered through `devices/registry.py`.
- `dual_machine` target selection goes through `devices.all_devices()`.
- Generic sender package added; readiness gates are centralized.
- Passive CLI target report added for `rytm`, `a4`, and `both`.
- No architecture-test allowlist entries were added.
