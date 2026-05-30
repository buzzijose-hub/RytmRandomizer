# Manual Validation Kit Design

## Goal

Give Jose and reviewers a deterministic passive report that turns installer,
desktop UI, profile export, mock rehearsal, and optional armed hardware smoke
testing into one operator-ready checklist.

The report is guidance only. It must not start the desktop app, open a MIDI
port, inspect live ports, write files, send MIDI, run an analyzer, or execute
any of the commands it prints.

## Product Fit

This fills the gap between:

- `docs/BUILDING_INSTALLERS.md`, which explains how maintainers build unsigned
  installers.
- `docs/MANUAL_HARDWARE_VALIDATION.md`, which records focused hardware
  validation procedures.
- The growing passive report surface that already emits readiness packets for
  snapshots, send plans, 12-pad compatibility, and live GUI planning.

The kit gives an operator a single passive itinerary before testing the
current installer or a source checkout with an Analog Rytm attached.

## Non-Goals

- No MIDI send path.
- No port discovery.
- No GUI launch or sidecar launch.
- No audio analysis.
- No profile export execution.
- No mutation execution.
- No automatic hardware loop.
- No parity fixture changes.

## Architecture

Add a small fact table under `rytm_randomizer/data/` and a passive report module
under `rytm_randomizer/reports/`.

The data layer owns immutable phase and step definitions. The report layer
filters those definitions, emits text/JSON, and registers one lazy CLI command:

```bash
python -m rytm_randomizer.cli manual-validation-kit-report [--phase <slug>] [--json]
```

The command is safe to run on any machine because every active command appears
only as quoted text for the human operator.

## Data Model

### ManualValidationPhase

- `slug`: stable phase id.
- `title`: operator-facing title.
- `summary`: one-line purpose.
- `step_ids`: ordered validation step ids included in the phase.

### ManualValidationStep

- `step_id`: stable step id.
- `phase`: phase slug.
- `title`: operator-facing title.
- `mode`: `passive`, `mock`, or `armed-manual`.
- `requires_installer`: whether this step assumes the installed desktop build.
- `requires_hardware`: whether this step requires the Analog Rytm to be powered
  and intentionally selected by the operator.
- `operator_actions`: ordered human actions.
- `expected_observations`: what the operator should see or hear.
- `evidence_prompts`: screenshots, logs, exported files, or notes to collect.
- `stop_conditions`: reasons to stop and report back.
- `passive_commands`: commands that are safe to run directly.
- `manual_commands`: active commands printed as instructions only.

## Initial Phases

1. `installer_bootstrap`
   - install or launch the unsigned desktop build
   - confirm sidecar/server connection and Mock Safe state
   - confirm no MIDI port is open by default

2. `profile_workflow`
   - create a profile from reference material
   - capture analyzer/profile errors such as missing optional extras
   - verify export affordances and output expectations

3. `mock_rehearsal`
   - rehearse preview, regen, prepare, send-disabled/apply-disabled behavior,
     undo/history, save, and control states without hardware mutation

4. `armed_smoke`
   - manually verify one intended Rytm output path only after explicit operator
     arming and port selection
   - keep the existing single-CC command as the only printed armed smoke
     command

5. `evidence_closeout`
   - gather screenshots, logs, terminal output, exported profile artifacts, and
     hardware observations into a reviewer-friendly packet

## Safety Contract

The report must always declare:

- `passive_report`: true
- `opens_midi_ports`: false
- `sends_midi`: false
- `launches_gui`: false
- `runs_audio_analyzer`: false
- `writes_files`: false
- `executes_printed_commands`: false

Any command containing `--arm` is instruction text only and must be listed under
manual commands, never replay commands.

## Acceptance Criteria

- Text output lists phases, steps, evidence prompts, stop conditions, and safety.
- `--phase <slug>` filters to one phase and rejects unknown slugs.
- JSON output is deterministic and serializable with sorted keys.
- The lazy CLI command is covered by the passive CLI safety sweep.
- Importing and rendering the report does not import `mido`, `rtmidi`, or
  `rytm_randomizer.real_midi_adapter`.
- Docs link the kit from manual validation and CLI reference.
