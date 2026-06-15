# Controller Brain Design

## Goal

Build the first passive foundation for an E16/OXI-style controller workflow where
RytmRandomizer is the musical brain and a 16-encoder controller is only the hands.
The system should not compete by being another raw MIDI mapper. It should expose
device-aware performance intent: Style Crates, macro depth, pad roles, queue moves,
snapshot recovery, Analog Rytm 12-pad behavior, Analog Four runway macros, and safe
send readiness.

## Competitive Framing

The OXI E16 proves there is a market for compact 16-encoder pages, snapshots,
morphing, grouping, gesture recording, and an app-based mapping workflow. Our
advantage is that RytmRandomizer already understands Jose's live performance
language: OXI One handles triggers and pattern motion, while RytmRandomizer rides
sound design safely. A controller page should therefore map to intents such as
"push Hard Groove pressure" or "bring Pad 6 tom source movement wider", not only
"send CC20 on channel 5".

This first build slice creates a passive controller-brain contract. It does not
open controller MIDI input, does not listen to an E16, does not send MIDI feedback,
does not send hardware MIDI, and does not arm the Rytm or A4. It makes the intended
controller pages reviewable and exportable as deterministic text and JSON so the
future Cockpit and hardware-input layers can consume one shared source of truth.

## Feature Scope

### In Scope

- A static controller mapping catalog under `rytm_randomizer/data/` for a
  generic 16-encoder controller profile.
- Seven deterministic pages, each with exactly 16 controls:
  - Global Brain
  - Rytm Pads 1-4
  - Rytm Pads 5-8
  - Rytm Pads 9-12
  - Analog Four Tracks
  - Style Crates + Queue
  - Snapshot Recovery + Journal
- Every control carries enough metadata for GUI and future controller binding:
  slot, label, target device, target scope, intent key, action type, lane,
  safety tier, recovery action, and notes.
- A passive report under `rytm_randomizer/reports/` that formats the mapping as
  operator-readable text and deterministic JSON.
- One passive CLI command:
  `controller-brain-mapping-report [--json]`.
- Tests proving:
  - every page has 16 controls and slots 1-16,
  - mappings are intent/device aware rather than raw CC dumps,
  - Rytm 12-pad and A4 track targets are present,
  - safety blocks active controller/hardware behavior,
  - the CLI report is passive and deterministic.
- Docs updates in `README.md`, `docs/CLI_REFERENCE.md`, `docs/STATUS.md`, and
  architecture docs/diagrams if the new CLI/report surface requires it.

### Out Of Scope

- Reading from the OXI E16, any MIDI controller, or any hardware input port.
- LED-ring or OLED feedback to a controller.
- MIDI learn, direct CC/NRPN assignment, or E16 app export files.
- Live WebSocket controller events in Cockpit.
- Raw MIDI sends to Analog Rytm or Analog Four.
- Audio analyzer work, song upload processing, or profile-wizard changes.

## Architecture

The catalog is data because it is a table of static facts. It belongs in
`rytm_randomizer/data/controller_mapping_profiles.py` and stays leaf-like: stdlib
only, frozen dataclasses, `Final` constants, and immutable `MappingProxyType`
catalogs. The catalog must not import Cockpit, reports, devices, engines, MIDI,
or style-analysis runtime modules.

The report lives in `rytm_randomizer/reports/controller_mapping_profile_catalog.py`.
It reads the data catalog, projects it into a passive report DTO, formats
operator-readable text with `reports/formatter.py`, and emits deterministic JSON.
The report may reference existing macro names and replay command strings, but it
must not execute commands or import active runtime code.

The CLI command is wired through the existing lazy `CliCommand` path in
`rytm_randomizer/cli.py`. The command accepts only an optional `--json` flag. It
must be covered by the passive CLI safety sweep.

## Controller Profile Shape

Each page models a 4x4 encoder grid. Slot numbers are 1-based and stable. A
future controller-input bridge can translate physical encoder movement into an
intent event by looking up `(profile, page, slot)`.

Controls use action names that describe intent, not device transport:

- `adjust_macro_depth`
- `adjust_pad_amount`
- `adjust_pad_density`
- `adjust_pad_bias`
- `select_style_crate`
- `queue_move`
- `stage_snapshot`
- `save_journal_entry`
- `recover_anchor`
- `toggle_lock`
- `prepare_dry_run`

The catalog can include implementation hints such as "derived from kit-core" or
"future WebSocket set_depth", but it must not include raw MIDI port names or
direct controller send instructions.

## Safety Contract

The report must state these blocked active actions:

- open MIDI controller input
- MIDI learn or raw CC capture
- send controller feedback
- open Analog Rytm or Analog Four output
- arm hardware
- send hardware MIDI
- mutate a snapshot
- dispatch Cockpit WebSocket commands

This keeps the build mock-first. Later live-controller work must pass through a
separate active design that validates input ports, event throttling, hardware
arming, stuck-control recovery, and visible disconnect states.

## Future Live Path

After this passive contract lands, the live path can be built in a later bundle:

1. Cockpit loads the profile JSON and displays the selected page.
2. A controller-input adapter opens an input port only after explicit arm.
3. Incoming controller events resolve to `(page, slot, value)`.
4. The resolver converts that into an existing Cockpit command such as
   `set_depth`, `set_pad_lock`, `toggle_preview`, `regen`, `prepare_send_plan`,
   or `send`.
5. Send remains gated by existing `CockpitSendPlan` readiness and hardware arm
   policy.

The passive contract in this spec gives that future layer one stable shape to
consume.

## Success Criteria

- Operators can run `python -m rytm_randomizer.cli controller-brain-mapping-report`
  and inspect the 16-control pages without hardware.
- Operators can run the same command with `--json` and get deterministic
  machine-readable profile data.
- The mapping demonstrates why RytmRandomizer is not just a MIDI controller:
  every row names musical intent, target device, target scope, safety, and
  recovery.
- The implementation changes no V1.34 parity fixtures and no live send behavior.
