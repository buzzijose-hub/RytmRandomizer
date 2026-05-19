# Dual-Machine Strategy Redo Design

## Why

PR #43 merged the new contribution rules and widened the `Device` Protocol with
capability strategies: `snapshot_decoder`, `mutation_planner`,
`message_renderer`, and `report_header`. Eddie's architecture review on PR #36
requires the previous stacked dual-machine work to be redone as one bundled PR
against `modularize-v1.34`, using that protocol instead of parallel Rytm,
Analog Four, and dual-machine sender surfaces.

The musical goal stays the same: make RytmRandomizer usable live with the
Analog Rytm MKII and Analog Four MKII as separate or combined targets, with
snapshot mode as the realistic live-performance default and anchor mode kept as
an optional controlled baseline.

## Approved Operator Shape

The user-facing language should stay performance-friendly:

- `rytm` / `rytm-only`: target only the Analog Rytm MKII.
- `a4` / `a4-only`: target only the Analog Four MKII.
- `both`: target both machines together.

The implementation should not expose programmer-oriented names such as
`analog_rytm_mk2` as the primary live command language. Those stable device IDs
remain internal registry keys and are acceptable in reports, JSON, tests, and
future advanced CLI flags.

The GUI can later present the same choice as a simple target selector:
`Rytm`, `A4`, or `Both`.

## Architecture

All machine-specific behavior routes through registered `Device` instances.
The generic flow is:

1. Resolve one or more devices from the registry.
2. Decode a snapshot through `device.snapshot_decoder`.
3. Plan mutations through `device.mutation_planner`.
4. Render messages through `device.message_renderer`.
5. Send through one generic guarded or hardware sender.

`AnalogRytmDevice` already exists as the reference implementation. The redo
adds `AnalogFourDevice` beside it at `rytm_randomizer/devices/analog_four.py`,
with three strategies under `rytm_randomizer/devices/strategies/`:

- `analog_four_snapshot_decoder.py`
- `analog_four_mutation_planner.py`
- `analog_four_message_renderer.py`

No top-level `rytm_randomizer/analog_four/`, `rytm_randomizer/rytm/`, or
`rytm_randomizer/essence/` package should be introduced in the redo. If Rytm
engine internals need a home, they should live under an approved package such as
`rytm_randomizer/devices/strategies/` or an existing shared data/engine layer,
not as a parallel device surface.

## Snapshot And Anchor Modes

Snapshot mode is the primary live path:

- The operator can capture the currently loaded machine state from one target
  (`rytm` or `a4`) or both targets.
- Mutations operate relative to that captured state.
- The software does not need continuous knob tracking after the snapshot.
- Each target can be captured and mutated independently, so a live set can
  mutate only the Rytm while leaving the A4 alone, or the reverse.

Anchor mode remains useful and should not be removed:

- It loads known safe defaults and mutates from those anchors.
- It is appropriate for demos, repeatable tests, and controlled exploration.
- It should be available as an explicit operator choice, not silently forced
  before every live mutation.

## Analog Four Readiness Rule

The Analog Four is less mature than the Rytm snapshot path. The A4 saved-offset
mapping work is still valuable, but it must be expressed through the new
strategy shape.

Until A4 offsets are promoted from candidate status, the A4 mutation planner
should return a plan with clear readiness metadata instead of allowing a real
send that looks safer than it is. The generic guarded sender should refuse real
hardware sends when a plan is not ready and should print the reason.

This keeps the live workflow honest: dry-run reports can keep improving while
real sends stay behind explicit readiness gates.

## Generic Sender Shape

The old stacked work duplicated sender logic across Rytm, A4, and dual-machine
modules. The redo should collapse that into generic senders:

- `rytm_randomizer/senders/guarded.py`: dry-run/mock and readiness-checked
  report flow.
- `rytm_randomizer/senders/hardware.py`: real MIDI boundary flow, still gated
  by `--arm` and plan readiness.

The senders consume `Device.message_renderer` and never import concrete device
families. Real MIDI calls remain behind `RealMidiSender` /
`RealMidiPortProvider`, preserving the passive default and lazy MIDI imports.

## Dual-Machine Orchestration

`dual_machine` remains a legitimate shared orchestration/reporting concept, but
it should not import concrete Rytm or A4 modules. It should receive a mapping of
registered devices, normally from `devices.all_devices()`, then filter by the
operator target:

- `rytm`: one device, 12 tracks/pads.
- `a4`: one device, 4 tracks.
- `both`: both registered devices, independent plans, one combined report.

This keeps the door open for future devices without rewriting the orchestration
layer.

## Hardware Safety

No tests may open a real MIDI port or mutate connected hardware. Hardware tests
remain operator-driven only and must be clearly separated from CI.

The package default stays passive. Running `rytm-randomizer` without `--arm`
must never open a port. Imports of `mido` and `python-rtmidi` stay lazy inside
the real-MIDI adapter boundary.

Because Jose's machines are on during this design checkpoint, no automated MIDI
send is performed as part of this document. Hardware will be used only after the
new strategy path has tests and an explicit manual test script or CLI command.

## Workstream Design

The redo should be one bundled PR, but the implementation can be broken into
clear internal workstreams:

1. **Plan and migration map**
   - Capture which pieces of PR #36 and the closed stacked PRs migrate,
     collapse, or get dropped.
   - Write the required implementation plan with the 16-gate checklist.

2. **Analog Four device strategy**
   - Add `AnalogFourDevice`.
   - Move candidate offset decoding/planning/rendering into strategies.
   - Register the device and test protocol conformance.

3. **Generic sender layer**
   - Add guarded and hardware senders that operate on `Device`.
   - Keep readiness gates and passive defaults central.

4. **Dual-machine target selection**
   - Map `rytm`, `a4`, and `both` to registered devices.
   - Produce combined reports without direct concrete imports.

5. **Operator docs and manual validation**
   - Document Rytm-only, A4-only, both-machine, snapshot, and anchor paths.
   - Keep hardware validation manual and explicit.

## Testing Strategy

The redo starts test-first:

- Device protocol tests for `AnalogFourDevice` registration and strategy
  conformance.
- Strategy unit tests for A4 snapshot decoding, mutation readiness, and message
  rendering.
- Sender tests using mock messages only.
- Dual-machine target tests proving `rytm`, `a4`, and `both` resolve through
  the registry.
- Architecture tests must pass with no allowlist additions.
- Full verification before PR: `python -m pytest`, `python -m pytest
  tests/architecture/ -q`, lint trio, and coverage.

## Out Of Scope For The Redo PR

- Audio analyzer / genre prompt kit generation.
- GUI implementation.
- Continuous knob tracking.
- New hardware package versions.
- V1.34 parity fixture regeneration.
- Real hardware sends from automated tests.

Those remain future milestones once the two-machine foundation is clean.

## Open Decisions

- Whether the first implementation slice should land A4 snapshot decode first
  or the generic sender first.
- Whether CLI compatibility should keep every older command alias or introduce
  a smaller new command family while preserving only the live-critical names.
- Where any reusable Rytm engine internals belong if they cannot fit cleanly in
  existing data/engine modules.

The current recommendation is to start with `AnalogFourDevice` plus tests,
because it proves the new strategy seam before generic senders and
dual-machine orchestration depend on it.
