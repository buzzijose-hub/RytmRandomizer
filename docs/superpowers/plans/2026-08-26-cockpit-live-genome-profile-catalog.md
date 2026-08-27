# Cockpit live Patch Genome, profile catalog + dual-device kit capture plan

Date: 2026-08-26

Status: in-flight

## Why

The Cockpit already ships a tested desktop shell, passive Python sidecar,
Profile Wizard, profile registry, and an Analog Four patch-genome compiler.
The current React Patch Genome panel still renders a static design fixture,
and the profile chips still come from a hard-coded fallback list. That makes
the newest UI read as a demo even though both data sources already exist.

This slice closes those two gaps without expanding hardware authority. It is
the first implementation pass against the approved passive Patch Genome
workspace preview: real compiler candidates, real registry profiles, local
candidate/family/lock interactions, and an unmistakably locked hardware-send
state.

The operator review exposed one additional first-class requirement: both the
Analog Rytm MKII and Analog Four MKII device cards need a **Capture Current
Kit** control. Capture is receive-only. The software waits for the operator to
send a KIT dump from the selected machine, validates the complete saved-kit
frame through the existing device codec, and records a name + fingerprint
anchor without sending a request or opening an output port.

Visual grounding:

- `docs/assets/rytmrandomizer-cockpit-cinematic-ui-reference-2026-06-09.png`
- `docs/assets/synplant-2-reference/` (interaction inspiration only; no clone)
- The generated 2026-08-26 approved next-milestone Cockpit preview in the
  active Codex design session.

## What changes

### WS-1 — passive sidecar contracts

Owns:

- `rytm_randomizer/cockpit/ws/protocol.py`
- `rytm_randomizer/cockpit/ws/handlers.py`
- focused tests under `tests/cockpit/`

Changes:

1. Add a `profile_catalog_changed` bootstrap event containing the complete
   `ProfileRegistry.list_profiles()` result.
2. Emit the same event after a Wizard profile is saved so the chip/catalog
   surface refreshes without reconnecting.
3. Add a passive `analyze_patch_genome` command accepting a description and
   Analog Four track number.
4. Reuse `build_analog_four_patch_genome_report_from_source` and
   `build_analog_four_patch_genome_payload`; do not duplicate feature
   extraction, candidate templates, display conversions, or safety lines.
5. Return and emit the full four-candidate payload. The handler opens no MIDI
   port, writes no file, sends no MIDI/SysEx, and grants no SEND authority.

### WS-2 — Cockpit workspace

Owns:

- `desktop/web/src/ws/protocol.ts`
- `desktop/web/src/state/`
- `desktop/web/src/cockpit/`
- focused Vitest and Playwright coverage under `desktop/web/`

Changes:

1. Mirror the two new wire events and passive command in TypeScript.
2. Store the current profile catalog and Patch Genome payload in Zustand.
3. Replace `DEFAULT_AVAILABLE_PROFILES` with the server-supplied catalogue.
4. Turn the A4-selected center surface into the approved Patch Genome
   workspace: description source, track selector, four candidate cards,
   family tabs, real gene values/readiness, local locks, and passive safety.
5. Make Grow Variant select the next real candidate; remove the artificial
   `+3` candidate-value behavior.
6. Keep the Rytm snapshot/mutation workflow unchanged and keep A4 hardware
   SEND visibly locked.

### WS-3 — product docs and visual verification

Owns:

- `README.md`
- `docs/COCKPIT_QUICKSTART.md`
- `docs/STATUS.md`
- `docs/ARCHITECTURE.md` and diagrams if the event flow changes their current
  documented boundary
- Product Design `design-qa.md`

Changes:

1. Document the live registry and passive real-data Patch Genome behavior.
2. Remove the stale claim that Phase 1 is still being implemented on its old
   feature branch.
3. Capture the running A4 workspace and compare it with the approved preview.

### WS-4 — shared current-kit capture (Rytm + A4)

Owns:

- `rytm_randomizer/cockpit/capture/`
- the additive capture fields/commands/events in `rytm_randomizer/cockpit/ws/`
- `rytm_randomizer/cockpit/__main__.py` and the explicitly armed `app.py`
  composition seam
- `desktop/shell/src/sidecar.rs`
- `desktop/web/src/cockpit/KitCapturePanel.tsx`, `DeviceRail.tsx`, and their
  typed state/protocol tests

Changes:

1. Add one generic input-only capture service parameterized by the canonical
   Rytm/A4 codecs and snapshot decoders. Do not create per-device capture
   implementations or duplicate Elektron packing/envelope logic.
2. Keep the passive Cockpit entrypoint disabled for hardware discovery. The
   desktop shell launches the capture-capable sidecar only through
   `python -m rytm_randomizer.app --arm ...`, preserving `app.py --arm` as the
   sole real-MIDI boundary.
3. Enumerate MIDI inputs only after an explicit operator action. Capture one
   complete KIT frame on the selected input in a worker thread, validate its
   checksum/length and lossless round trip, and emit a typed result.
4. Add **Capture Current Kit** to both device cards. The shared panel identifies
   the selected machine, explains the device-side KIT-dump action, exposes the
   input selector, and shows the last verified name/fingerprint/byte count.
5. Treat Rytm as a decoded mutation anchor. Treat A4 as a verified exact
   saved-kit anchor while its semantic parameter offsets remain candidate-level;
   the UI must state that difference rather than overclaiming parity.

## Architecture shape

```text
ProfileRegistry.list_profiles()
    -> profile_catalog_changed
    -> Zustand profileCatalog
    -> Live Profile Catalog

description + selected A4 track
    -> analyze_patch_genome WS command
    -> existing passive report/compiler
    -> patch_genome_changed
    -> Zustand patchGenome
    -> A4 Patch Genome workspace

explicit Capture Current Kit action
    -> input-port discovery (armed app composition only)
    -> one received saved-KIT SysEx frame
    -> ANALOG_RYTM_KIT_CODEC or ANALOG_FOUR_KIT_CODEC
    -> existing device SnapshotDecoder
    -> kit_captures_changed
    -> shared Rytm/A4 capture panel
```

No new top-level module, device family, registry, renderer, data table, or
output boundary is introduced. The new `cockpit/capture/` subpackage consumes
the existing injected MIDI-input provider Protocol and canonical device
codecs/decoders.

## Parity and safety impact

- No V1.34 engine, runner, shell, parity fixture, CC map, or parameter range
  changes.
- No parity-fixture regeneration.
- The new command is passive and must remain safe under sidecar bootstrap,
  unit tests, and Playwright E2E.
- Analog Four hardware sending remains outside this slice.
- Kit capture never sends a SysEx request, never opens an output, and never
  writes the captured frame to disk automatically.
- The current uncommitted RUSH16 calibration files are unrelated user work and
  must remain untouched.

## Plan-requirements conformance

- Gate 1 — Add focused branch coverage for every touched Python branch.
- Gate 2 — Run the unchanged V1.34 parity suite.
- Gate 3 — Ruff, Black, isort, TypeScript typecheck, and ESLint clean.
- Gate 4 — No dead or duplicate static-model surface remains.
- Gate 5 — Update README, Quickstart, STATUS, and architecture docs as needed.
- Gate 6 — TypedDict wire records; no new `Any` or untyped DTO boundary.
- Gate 7 — Structured logging for the passive analysis decision.
- Gate 8 — The additive internal sidecar flag is documented and guarded by
  `--arm`; ordinary passive CLI behavior is unchanged.
- Gate 9 — Work stays under the existing `cockpit/` and `desktop/web/` trees.
- Gate 10 — New wire discriminators use literal constants/unions.
- Gate 11 — Reuse existing cockpit fixtures and add focused shared fixtures
  only when duplication appears.
- Gate 12 — New Python constants are annotated `Final`.
- Gate 13 — N/A: no interactive shell command changes.
- Gate 14 — New passive command is explicit, deterministic, and fail-closed.
- Gate 15 — N/A unless implementation reveals a reusable workflow not already
  covered by the Cockpit and Product Design guides.
- Gate 16 — One bundled logical change; no stacked PR cascade.
- Gate 17 — Reuse ProfileRegistry, report compiler, event dispatcher, and
  Zustand binding abstractions; dual-device capture reuses the Device strategy
  decoders and canonical Elektron kit codecs.
- Gate 18 — Refresh architecture text/diagram if the documented bootstrap
  event set or UI data flow would otherwise be stale.

## Test plan

1. Python handler/protocol tests:
   - bootstrap profile catalog includes built-ins and saved users;
   - Wizard save queues a catalog refresh;
   - patch analysis returns four real candidates for a description;
   - invalid track/source fails categorically;
   - passive proof: no MIDI provider/port/send/write path is reached.
2. Frontend Vitest:
   - new event guards and store bindings;
   - catalog renders registry profiles and filters/searches them;
   - candidate selection uses real compiler rows;
   - family and lock interactions remain local;
   - Analyze dispatches only the passive command;
   - hardware SEND remains disabled.
3. Playwright:
   - real sidecar boots the A4 workspace;
   - description analysis replaces the initial payload;
   - a Wizard-saved profile appears in the live catalogue without reload;
   - axe scan for the updated root surface.
4. Required gates:
   - focused Python tests;
   - `tests/cockpit`;
   - web unit/lint/typecheck/build/E2E;
   - `tests/architecture/`;
   - V1.34 parity;
   - full pytest suite if time permits.
5. Dual-device capture:
   - synthetic valid Rytm and A4 saved-kit frames decode through the same
     service and produce truthful device-specific readiness;
   - malformed/checksum-wrong/wrong-family/multiple-frame captures fail closed;
   - passive sidecar performs no port discovery;
   - both device cards open the shared capture panel and the panel dispatches
     only typed input-list/capture commands;
   - shell composition reaches real input only through `app.py --arm`.

## Rollback plan

The slice is additive at the wire level. Reverting the single logical change
restores the prior bootstrap set and static UI. No profile or hardware data is
migrated, and no parity fixtures or saved profile formats change.

## Done criteria

- A real sidecar-generated four-candidate A4 genome is visible and interactive.
- A Wizard-saved profile appears in the catalog without reconnecting.
- No hard-coded profile catalogue or artificial `+3` genome growth remains.
- Hardware controls stay locked and the passive safety language is visible.
- Both device cards expose Capture Current Kit; verified Rytm/A4 anchors show
  their kit name, fingerprint, byte count, and honest decode readiness.
- Focused, architecture, frontend, and browser tests pass.
- Visual design QA compares the same A4-selected state and passes.
