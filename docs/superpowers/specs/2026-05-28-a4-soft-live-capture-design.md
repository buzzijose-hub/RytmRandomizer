# Analog Four Soft Live Capture Design

Date: 2026-05-28

## Context

The Analog Four MKII is now registered through the shared `Device` Protocol and
has a manual-backed MIDI CC table beginning under `rytm_randomizer/data/`.
Hardware validation in this session confirmed the first live-observation facts
on Track 1:

- CC 72: OSC1 Pulsewidth
- CC 73: OSC1 PWM Speed
- CC 74: OSC1 PWM Depth

The long-term performance workflow should not depend on full SysEx kit dumps in
the middle of a set. The performer needs the software to listen to the Analog
Four while playing, remember the parameters it has actually observed, and use
that observed state as the baseline for later guarded kit design and mutation.

## Goal

Add a passive soft-capture foundation for the Analog Four MKII. The operator can
start an input listener, let the A4 emit CC messages through manual encoder
movement or other live changes, then capture the current observed state for all
four A4 tracks at once.

The first implementation should be observation and reporting only. It should not
generate mutations, send MIDI, request SysEx, save kits, or claim to know
parameters it has not observed.

## Non-Goals

- No armed MIDI output.
- No A4 SysEx request or kit dump parsing.
- No kit save, project write, transport, clock, program change, or pattern
  change behavior.
- No mutation generation from the captured baseline in this first slice.
- No GUI.
- No audio analyzer or artist-style prompt system.
- No V1.34 parity fixture regeneration.

## Recommended Approach

Build the first slice as **Soft Live Capture**:

1. Open only the Analog Four MIDI input port when the operator explicitly starts
   capture mode.
2. Decode incoming `control_change` messages.
3. Map MIDI channels 0-3 to Analog Four tracks 1-4.
4. Map CC numbers through the manual-backed `ANALOG_FOUR_MANUAL_CC_BY_MSB`
   table.
5. Maintain a live observed-state store keyed by track and parameter.
6. On `capture all`, freeze the latest observed values for all four tracks into
   an immutable snapshot object.
7. Print a deterministic report that distinguishes known parameters from
   unknown parameters.

This matches the intended live-performance model. It is honest about partial
knowledge while still giving the operator one simple command: capture the A4's
current observed live state.

## Data Model

Add immutable state records under `rytm_randomizer/state/a4_soft_capture.py`
and report formatting under `rytm_randomizer/reports/a4_soft_capture.py`.
Input-port construction stays in the existing real-MIDI provider boundary; do
not add a new top-level package.

Suggested records:

- `ObservedA4Parameter`
  - `track`: 1-4
  - `parameter`: manual-backed parameter name
  - `section`: manual section such as `OSC 1` or `FILTERS`
  - `cc`: MIDI CC number
  - `value`: latest observed value, 0-127
  - `observed_at`: monotonic or wall-clock timestamp suitable for reports
- `A4ObservedTrackState`
  - `track`: 1-4
  - `parameters`: mapping from parameter name to `ObservedA4Parameter`
- `A4SoftCaptureSnapshot`
  - `tracks`: four `A4ObservedTrackState` entries
  - `source`: `"passive_cc_observation"`
  - `known_parameter_count`
  - `unknown_policy`: `"unknown_parameters_untouched"`

The live store may be mutable while listening, but the captured snapshot is
frozen.

## Manual Mapping

The capture decoder must consume the data layer. It must not hardcode A4 CC
labels in listener code.

Manual-backed table coverage includes every Appendix D row that exposes a CC MSB
value: track/common, performance, modulation, and synth-track CC rows. FX and CV
rows in this manual section are NRPN-only and are not treated as CC send targets.
Unknown CCs are recorded separately as raw observations or ignored with a visible
report note; they must not be mislabeled.

## Operator Workflow

The first user-facing workflow can be text-based:

```powershell
python -m rytm_randomizer.app --arm --a4-soft-capture
```

The command should:

- List MIDI input ports and require the operator to choose the A4 input.
- Open only that input port.
- Show that no output port is open.
- Listen until the operator stops capture with a clear keyboard action.
- Print a report like:

```text
A4 soft live capture
Input: Elektron Analog Four MKII 0
Opened output: False
Sent MIDI: False

Track 1: 3 observed params
- OSC1 Pulsewidth: 96
- OSC1 PWM Speed: 32
- OSC1 PWM Depth: 96

Track 2: 0 observed params
Track 3: 0 observed params
Track 4: 0 observed params

Unknown parameters: left untouched
```

The later interactive performance command can expose this as `capture all`, but
the first slice should keep a small command surface until the input boundary is
well tested.

## Safety

This feature is passive input only. It must:

- Never open a MIDI output port.
- Never send MIDI.
- Never import `mido` at module import time.
- Never request SysEx.
- Never mutate unknown parameters.
- Never claim a complete kit snapshot unless all required values were actually
  observed or imported from a later approved SysEx workflow.

Unknown state is not an error. It is a first-class report value.

## Error Handling

- No input ports: return a clean non-zero exit with a clear message.
- Invalid port selection: return a clean non-zero exit.
- Non-CC message: ignore or count by message type in the report.
- CC outside the manual-backed table: count as unknown raw CC, do not label.
- Channel outside 0-3: count as out-of-scope for the A4 four-track capture.
- Keyboard interrupt / EOF: stop listening cleanly and print the current report
  if any observations were captured.

## Testing

Use TDD with fake input ports first. No automated test may open real MIDI.

Focused tests should cover:

- Incoming channel 0 / CC 72 updates Track 1 OSC1 Pulsewidth.
- Incoming channel 1 / CC 72 updates Track 2 OSC1 Pulsewidth.
- Incoming channel 3 / CC 74 updates Track 4 OSC1 PWM Depth.
- Unknown CC is not mislabeled.
- Non-CC messages do not crash the listener.
- `capture all` returns four track entries even when some tracks are empty.
- The report clearly marks unknown parameters as untouched.
- Passive/import-safety tests prove no output port is opened and no real MIDI
  backend is imported outside the explicit armed input path.

Recommended verification:

```powershell
python -m pytest tests/test_a4_soft_capture.py -n 0
python -m pytest tests/test_app_entry.py -n 0
python -m pytest tests/test_real_midi_passive_cli_safety.py -n 0
python -m pytest tests/architecture/test_no_side_effects.py -q
python -m pytest tests/architecture/test_data_not_code.py -q
python -m pytest -m fast
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
```

## Follow-Up Sequence

1. Soft live capture report for all four A4 tracks.
2. Guided capture prompts for important manual-backed pages such as OSC,
   FILTERS, AMP, ENV, LFO, and FX sends.
3. Guarded baseline design that mutates only observed parameters.
4. Optional pre-show SysEx snapshot import for fuller state, merged with live
   CC observations during performance.
