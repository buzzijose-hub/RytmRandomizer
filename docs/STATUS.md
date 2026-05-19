# RytmRandomizer - Project Status

Last updated: 2026-05-18. This file is a hand-authored snapshot and is meant to be updated in place, never appended.

## Recent Cleanup

- 2026-05-18: corrected the Rytm 12-pad engine model against Analog Rytm MKII
  OS 1.72. The machine catalog now records the manual pad/track compatibility
  table, and the active engine-cycle/runtime planners enforce it before
  building CC15 machine-select streams. Pad 5 is BT Classic, Pads 6-8 are XT
  Classic lanes, Pad 9 is CH/hat, Pad 10 is OH/hat, Pad 11 is CY, and Pad 12
  is CB. The Analog Four reference report now records Jose's current
  OS1.51C manual path and MIDI appendix pages. No unguarded MIDI sending,
  SysEx writes, live snapshot receive, or audio analysis was added.
- 2026-05-18: added the passive 12-pad Rytm runtime foundation.
  `twelve-pad-rytm-runtime-report --style <text>` builds a mock-only setup
  stream with machine selects, engine-source starter values, and common
  filter/amp starter values across all 12 Analog Rytm pads. The existing
  guarded `--rytm-engine-cycle` dry-run/arm path remains unchanged. No live
  snapshot capture, audio analysis, Analog Four mutation, SysEx writes, or
  unguarded hardware sending was added.
- 2026-05-18: moved the dual-machine milestone modules that predated Gate 9
  into focused subpackages (`analog_four/`, `dual_machine/`, `sysex/`,
  `performance/`, `essence/`, `rytm/`, and `snapshot/`) and removed the
  temporary top-level architecture allowlist entries. No CLI behavior, MIDI
  behavior, hardware send behavior, or snapshot planning behavior changed.
- 2026-05-18: PR #35 Wave-1 simplification bundle merged into
  `modularize-v1.34`. The base now includes the `devices/`, `snapshot/`,
  `behavior/`, and `reports/` subpackages, shared test fixtures, the
  `MidiSender` / `PadRuntimeState` / `Device` protocol surfaces, the
  `PassiveReportFormatter`, CLI registry scaffolding, observability metrics,
  and the new architecture guard tests. The dual-machine branch now builds on
  that foundation instead of carrying parallel helper code.
- 2026-05-18: integrated Eddie's `modularize-v1.34` cleanup branch into
  `codex/dual-machine-mock-bridge`, preserving the dual-machine/snapshot
  planning work while accepting the monolith retirement, CI coverage
  hardening, and parity-fixture baseline.
- 2026-05-17: added optional Rytm engine-cycle source starters. When
  `--engine-cycle-source-starters` is paired with an engine-cycle starter
  profile, the guarded plan sends 132 messages: 12 machine selects, 48 mapped
  SRC-slot starter values, and 72 common filter/amp starter values.
- 2026-05-17: resolved the test-only API audit. Removed dead lookup/report
  shims and documented the kept V1.34 parity API surface in
  `docs/ARCHITECTURE.md` so future dead-code audits have a clear boundary.
- 2026-05-17: retired the V1.34 `rytm_hybrid_randomizer_v134.py` monolith.
  Its behavior is now frozen as JSON goldens under
  `tests/fixtures/v134_parity/`, and parity tests compare package output to
  those fixtures instead of running the monolith.
- 2026-05-17: raised coverage on `app.py`, `cli.py`,
  `observability/logging.py`, and `mido_provider.py`; CI/Black settings were
  tightened to match the supported Python matrix.
- 2026-05-17: added the first passive saved-kit snapshot decoder and
  `sysex-kit-snapshot-report <path> --slot <1-128>`. The decoder unpacks the
  Rytm kit record's Elektron 7-bit payload and exposes all 12 pad sound blocks
  as raw snapshot baselines with stable per-pad hashes. Jose's saved project
  dump and `ANALOGRYTMKITS2.syx` both decode slot 1 into 12 pad blocks, and
  slot 16 shows distinct per-pad hashes where the saved kit differs. Parameter
  maps are still intentionally blocked; no live SysEx receive, MIDI sending,
  hardware mutation, restore behavior, or SysEx writes were added.
- 2026-05-17: added the passive whole-project SysEx analyzer and
  `sysex-project-report <path>` CLI command. Jose's Rytm and Analog Four
  whole-project dumps now resolve as complete 405-record streams with grouped
  kits, sounds, patterns, song/project slots, global slots, and project
  settings. This gives Live Snapshot planning a real project-dump inventory
  layer without live SysEx receive, parameter decoding, MIDI sending, hardware
  mutation, or SysEx writes.
- 2026-05-16: added the first guarded Analog Four MKII hardware smoke path.
  The app now supports `rytm-randomizer --dry-run --analog-four-smoke` and
  `rytm-randomizer --arm --analog-four-smoke`, plus the one-track
  `--analog-four-track-smoke <1-4>` variant and the first filter validation
  path, `--analog-four-track-filter-smoke <1-4>`. The pan paths emit
  deterministic Amp Pan CC10 left/right/center moves across A4 Tracks 1-4 or
  a single selected track, returning Pan to 64. The filter path emits Filter 1
  Frequency CC18 low/open/open-return on one selected track, ending at
  127/open. This proves a cautious Track 1-4 channel-validation path and the
  first A4 parameter smoke without Rytm sends, resonance/level/pitch mutation,
  engine cycling, NRPN, CV, SysEx, cross-device scenes, snapshot capture, or
  Analog Four runtime mutation.
- 2026-05-16: added the first guarded 12-pad hardware smoke path. The app now
  supports `rytm-randomizer --dry-run --twelve-pad-smoke` and
  `rytm-randomizer --arm --twelve-pad-smoke`, emitting the same deterministic
  Pads 5-12 Pan CC10 / Filter Frequency CC74 stream Jose validated manually on
  hardware. This proves channel targeting across MIDI channels 5-12 without
  engine cycling, SysEx, snapshot capture, Analog Four sends, or full Pads 5-12
  runtime mutation.
- 2026-05-16: added the first passive Analog Four MKII reference intake.
  `analog-four-reference-report` records the midi.guide A4 source, license,
  update date, parameter count, four planning track roles, and a starter
  CC/NRPN mutation surface for tracks, oscillators, filters, envelopes, sends,
  noise, and LFOs. This is reference-known/mock-only planning metadata. It
  does not add Analog Four runtime support, port selection, MIDI sending, live
  SysEx receive/write behavior, cross-device scene execution, or hardware
  mutation.
- 2026-05-16: added the first mock-only 12-pad runtime contract.
  `twelve-pad-mock-runtime-report --style <text> [--discovery <0..1>]`
  turns Style Intent into mapped 12-pad machine selections, MIDI channel
  assignments, and inert mock CC messages. It uses currently mapped V1.34-safe
  profiles only and falls back from preferred future-only engines to mapped
  candidates, making all 12 pads inspectable before any active hardware path
  exists. No MIDI sending, port opening, live SysEx receive/write behavior,
  runtime state mutation, hardware mutation, or Analog Four behavior was added.
- 2026-05-16: added a passive Style Intent Kit layer.
  `style-intent-report --style <text> [--discovery <0..1>]` maps broad
  genre/style prompts such as broken techno, dark techno, Birmingham techno,
  hardcore, schranz, classic Detroit techno, driving techno, and peak-time
  techno into non-copying essence tags and the existing passive 12-pad plan.
  `essence-application-readiness-report --mode <mode> --style <text> ...`
  now feeds those same prompts into the per-pad readiness gate, using profile
  Discovery hints unless overridden. Analog Four is recorded as future-only
  metadata. No audio analysis, MIDI sending, hardware mutation, live SysEx
  capture, Pads 5-12 runtime mutation, or Analog Four runtime behavior was
  added.
- 2026-05-16: added passive mock 12-pad snapshot fixtures for Live Snapshot
  planning. `rytm_randomizer.snapshot.fixtures` now exposes the AM9-inspired
  `am9-slot-01` fixture, and
  `essence-application-readiness-report ... --fixture am9-slot-01` uses that
  captured-machine support mix to block unmapped snapshot pads before any live
  SysEx receive or hardware capture exists.
- 2026-05-16: added a passive Essence Application Readiness gate.
  `rytm_randomizer.essence.application` evaluates whether a 12-pad Essence
  Plan is ready, blocked, or future-only under Safe Anchors or Live Snapshot,
  and the CLI now exposes
  `essence-application-readiness-report --mode <mode> ...`. This makes the
  current boundary explicit: Safe Anchors is four-pad runtime-ready today, Live
  Snapshot needs a complete 12-pad snapshot, and unmapped future engines remain
  blocked. No MIDI sending, live SysEx receive, hardware mutation, or Pads 5-12
  runtime mutation was added.
- 2026-05-16: added a passive description-to-essence bridge. The new
  `rytm_randomizer.essence.tag_adapter` derives broad, non-copying musical
  tags from written reference language or a passive `FeatureReport`, and
  `essence-plan-report --description <text> --discovery <0..1>` now feeds
  those tags into the existing 12-pad engine plan preview. No audio file
  analysis, MIDI, hardware mutation, SysEx writes, or Pads 5-12 runtime
  mutation was added.
- 2026-05-16: exposed the passive Essence Plan Preview through
  `essence-plan-report --tags <csv> --discovery <0..1>`. This prints a 12-pad
  role plan and candidate Rytm engines from manually supplied essence tags,
  making the future audio-analyzer-to-engine-choice path visible without audio
  analysis, MIDI, hardware, or Pads 5-12 runtime mutation.
- 2026-05-16: added the first passive Machine Catalog and Essence Matcher.
  `rytm_randomizer.essence.machine_catalog` records currently mutable V1.34 machines,
  future inventory-only engines such as SY Chip and Dual VCO, a 12-pad
  reference-role template, and passive ranking from role/essence tags. This is
  planning metadata for future audio-analyzer-driven engine choice; it does not
  add audio analysis, Pads 5-12 runtime mutation, new MIDI sends, or SysEx
  capture/write behavior.
- 2026-05-16: added the first passive SysEx kit bank analyzer and CLI report
  command. `sysex-kit-bank-report <path>` reads an existing `.syx` file,
  splits complete SysEx records, identifies fixed-length kit slots, and marks
  repeated unnamed records as blank/default candidates. Jose's `AM9KITS.syx`
  reports slots 1-16 as nonblank and 17-128 as blank/default candidates. No
  MIDI receive path, parameter decoding, SysEx writes, or hardware capture was
  added.
- 2026-05-16: added the Live Snapshot mode design checkpoint and the first
  passive `performance.modes` model. This records startup mode semantics and
  blocks Live Snapshot mutation unless a complete 12-pad snapshot exists. No
  MIDI receive path, hardware capture, or runtime mutation behavior was added.
- 2026-05-15: completed the first end-user Analog Rytm MKII hardware
  validation pass for V1.34 alpha. The freshly rebuilt installer wheel
  installed cleanly, `--dry-run` completed the canonical flow, `--arm`
  opened `Elektron Analog Rytm MKII 1`, scene mutations were audible, and
  `S5`/`Z` returned all four pads to clean anchors.
- 2026-05-15: prepared the first real-machine validation session by updating
  the manual hardware checklist with a dry-run preflight, volume/restorable-kit
  reminders, and a notes template. No runtime behavior change.
- 2026-05-15: captured the future audio analyzer Reference/Discovery slider
  direction in `docs/FUTURE_AUDIO_ANALYZER_REFERENCE_DISCOVERY.md`. No runtime
  behavior change.
- 2026-05-15: captured the future Analog Four expansion direction in
  `docs/FUTURE_ANALOG_FOUR_EXPANSION.md`. No runtime behavior change.
- 2026-05-15: aligned the coverage policy doc with the live `.coveragerc`
  floor and ratchet workflow. No CI behavior change.
- 2026-05-15: extracted PadRuntimeMixin (engines/_runtime.py) consolidating ~150 LOC duplicated across 5 engines/runners. No behavior change.
- 2026-05-15: dead-code audit removed three trivially-unused symbols (`_lazy_rehome_imports` in `observability/errors.py`, `log_extra` in `observability/logging.py`, the unused `self._provider` bookkeeping in `RealMidiSender.__init__`). No behavior change; 197 tests still green.
- 2026-05-15: extracted scene_menu_lines() data-driven generator; dedupes scene menu strings across shell.py + scene_runner.py + SCENE_PRESETS. No output change.
- 2026-05-16: shell.dispatch converted from a 92-arm if/elif chain (~396 LOC) to a module-level `_DISPATCH` table where each uniform arm is a one-line closure. Special-shaped arms (quit, target/profile re-selection that updates `self.channel`, scene preset lookup, depth-guardrail 1/2/3 message, depth-prompting zone mutations, unknown-command fallback) stay inline. shell.py net ~186 LOC reduction. Behavior byte-identical: full parity suite green.
- 2026-05-16: small-gap coverage tests added in tests/test_coverage_small_gaps.py — plugs single-branch holes in active_boundary, mock_midi, inspection, and validation (8 tests total). Bumps pure-branch coverage per the ratchet.
- 2026-05-17: coverage on observability/logging.py raised from 57% to 100% via tests/test_observability_logging.py.
- 2026-05-17: coverage on app.py raised from 69% to 100% via additional tests in tests/test_app_entry.py (covers --arm port-open production path, list_output_names dependency/port errors, _choose_arm_port_name EOF / invalid / out-of-range branches, --dry-run shell EOF swallowing, --arm/--dry-run mutually-exclusive flag conflict, unknown-flag rejection, --debug/--log-json passive boot). No behavior change.
- 2026-05-17: coverage on cli.py raised from 5% to 100% via tests/test_cli_coverage.py additions. Closes the largest single coverage gap in the package.
- 2026-05-17: coverage on mido_provider.py raised from 33% to 100% via tests/test_mido_provider.py.

## Current Version

**V1.34** musical behavior, owned end-to-end by the modular package as of Wave 4 / WS-O. Stable tag: `v1.34-stable-expanded-scene-layer`. Working branch: `modularize-v1.34`.

## What Works

- **The package IS the tool.** `pip install rytm-randomizer` provides the `rytm-randomizer` console entry point. It opens a real MIDI port (via the `mido`-backed provider in `rytm_randomizer.mido_provider`) and sends CC messages to the Elektron Analog Rytm MK2 hardware. Three modes are exposed by `rytm_randomizer.app`:
  - **Default (no flag)**: passive read-only inspection / preview menu. Opens no port, sends no MIDI.
  - `--arm`: opens a real MIDI port and runs the interactive command shell (`rytm_randomizer.shell.InteractiveShell`). This is the supported way to drive the Rytm.
  - `--dry-run`: runs the same interactive command shell against `rytm_randomizer.mock_midi.MockMidiSender`. No hardware, no port opened.
- The active app also exposes a guarded `--twelve-pad-smoke` modifier with
  `--dry-run` or `--arm`. It sends only Pan CC10 and Filter Frequency CC74 to
  Pads 5-12, returning both controls to 64, then exits. This is channel
  validation only, not full Pads 5-12 mutation support.
- The active app also exposes a guarded `--analog-four-smoke` modifier with
  `--dry-run` or `--arm`. It sends only Amp Pan CC10 to Analog Four Tracks
  1-4, returning Pan to 64, then exits. This is channel validation only, not
  Analog Four runtime mutation support. The companion
  `--analog-four-track-smoke <1-4>` modifier runs the same pan-only validation
  for one selected A4 track. The
  `--analog-four-track-filter-smoke <1-4>` modifier runs Filter 1 Frequency
  CC18 low/open/open-return for one selected A4 track.
- Pad coverage is complete relative to V1.34: BD engine anchors/discovery (Pad 1), snare/secondary percussion (Pad 2), SY Raw bass (Pad 3), BD Acoustic (Pad 4), a four-pad group layer, scenes (S0-S5 plus variants), isolated single-pad mutation, legacy single-profile mutation, and the full command surface.
- The V1.34 reference behavior is preserved as JSON goldens under `tests/fixtures/v134_parity/`. The original `rytm_hybrid_randomizer_v134.py` monolith was retired in 2026-05-17; the parity tests (`tests/test_engines_pad*`, `tests/test_group_runner.py`, `tests/test_scene_runner.py`) now compare engine output to those fixtures via `tests/_parity_worker.py`.

## Decomposition Complete

Wave 4 is closed. The monolith decomposition extracted, in order:

- **WS-K** -- MIDI I/O primitives + randomization core (`rytm_randomizer.midi_io`, `rytm_randomizer.randomization`).
- **WS-L** -- per-domain runtime state (`rytm_randomizer.state.*`).
- **WS-M** -- per-pad engines (`rytm_randomizer.engines.pad1` .. `pad4`).
- **WS-N** -- group + scene orchestration (`rytm_randomizer.group_runner`, `rytm_randomizer.scene_runner`).
- **WS-O** -- the interactive command shell and final convergence (`rytm_randomizer.shell.InteractiveShell` + the wired-up `rytm_randomizer.app.main`).

Each step is locked against the V1.34 reference by characterization tests.

## What's Next

- Stabilize the V1.34 alpha around the first hardware pass: keep the canonical
  dry-run and project-status checks green after every installer rebuild.
- Polish the end-user operator flow without changing the validated MIDI
  ranges or the protected V1.34 reference.
- Further hardening: installer polish, release checklist, lint/type-check
  baseline, and repeat hardware validation before a release candidate.
- Out of scope for now: Pads 5-12 active runtime mutation, additional
  hardware-validated Rytm machines/profiles, GUI/capture, live SysEx
  receive/write behavior, Analog Four runtime mutation beyond pan-only smoke,
  and cross-device hardware execution.

## Reference Docs

- `docs/ARCHITECTURE_DIAGRAMS.md` -- current code-derived architecture maps.
- `docs/MODULARIZATION_RULES.md` -- modularization constraints. Historical CODEX briefs live in `docs/archive/`.
- `docs/V134_OPERATOR_COMMAND_SURFACE_REFERENCE.md` -- the V1.34 command surface, as preserved by `rytm_randomizer.shell`.
- `docs/archive/PASSIVE_CLI_OPERATOR_QUICKSTART.md` -- historical passive CLI quickstart.
- `docs/archive/HARDWARE_MANUAL_REFERENCE_INVENTORY.md`, `docs/LOCAL_DEV_TOOLING_NOTES.md` -- reference/tooling notes.
- `docs/FUTURE_AUDIO_ANALYZER_REFERENCE_DISCOVERY.md` -- future analyzer slider
  and 12-pad role-map direction; not current runtime scope.
- `docs/FUTURE_ANALOG_FOUR_EXPANSION.md` -- future cross-device Analog Four
  direction and passive reference-intake status; not current runtime scope.
- `docs/LIVE_SNAPSHOT_MODE_DESIGN_CHECKPOINT.md` -- startup mode selection,
  Safe Anchors versus Live Snapshot semantics, and the future 12-pad snapshot
  capture safety model.
- `docs/SYSEX_KIT_BANK_ANALYZER_CHECKPOINT.md` -- passive saved-kit-bank
  analyzer scope, AM9KITS observation, and Live Snapshot relevance.
- `docs/MACHINE_CATALOG_ESSENCE_MATCHER_CHECKPOINT.md` -- passive machine
  catalog, 12-pad role template, and future analyzer-to-engine-choice bridge.
- `docs/archive/TRIAGE_REPORT.md` -- audit record of the `docs/` accuracy triage.
