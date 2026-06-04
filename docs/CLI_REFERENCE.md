# CLI reference

This is the full passive CLI surface for RytmRandomizer. Every command here is **passive by construction** — it opens no MIDI port and sends no MIDI. The project-wide passive-safety sweep in [`tests/test_real_midi_passive_cli_safety.py`](../tests/test_real_midi_passive_cli_safety.py) auto-discovers commands from the lazy registry and runs every one in a subprocess to assert no `mido` / `rtmidi` / adapter modules load and no armed-output tokens leak.

For the headline commands (cockpit, wizard, export, live-set planning) see the [README](../README.md#cli-cheat-sheet).

For the armed runtime (the V1.34 four-pad interactive shell), launch `rytm-randomizer --arm` and follow the in-shell menu. The armed runtime is the original V1.34 behaviour; its byte-frozen reference output lives in [`tests/fixtures/v134_parity/`](../tests/fixtures/v134_parity/).

> **Adding a new passive command:** register through `rytm_randomizer.cli_registry.CliCommand.register(...)`. Inline `if args == ["my-cmd"]` arms in `cli.py:main()` are forbidden — the architecture test `tests/architecture/test_cli_no_inline_arms.py` enforces a grandfathered-ratchet floor on the existing inline arms (PR 8, H7+IH4+IH5) and refuses any new ones. See [`CONTRIBUTING.md` § Patterns introduced by the CODE_REVIEW.md sweep](../CONTRIBUTING.md#patterns-introduced-by-the-code_reviewmd-sweep-2026-05-25).

---

## Cockpit · export (Phase 3)

```bash
# Pre-flight passive rehearsal — shows what file would land, no write.
python -m rytm_randomizer.cli cockpit-export-rehearsal-report \
    --profile-id buzzi --profiles-dir ~/.rytm-randomizer/profiles \
    --key-id buzzi-2026

# The actual export (HMAC-SHA256 signed).
python -m rytm_randomizer.cli cockpit-export-profile-model \
    --profile-id buzzi \
    --profiles-dir ~/.rytm-randomizer/profiles \
    --output ~/exports/buzzi-v1.0.0.rymp \
    --key-hex $RYMP_SIGNING_KEY --key-id buzzi-2026

# Unsigned export (development).
python -m rytm_randomizer.cli cockpit-export-profile-model \
    --profile-id buzzi --output ~/exports/buzzi-dev.rymp --unsigned
```

---

## Cockpit · send-plan readiness (Phase 1 + PR #103/#104)

```bash
# Passive read of a prepared CockpitSendPlan JSON.
python -m rytm_randomizer.cli cockpit-send-plan-readiness-report \
    --plan-file ./send-plan.json --json

# Operator-facing rehearsal surface — panels, bindings, replay command.
python -m rytm_randomizer.cli cockpit-send-plan-rehearsal-surface-report \
    --plan-file ./send-plan.json
```

---

## Manual validation kit

```bash
# Full passive checklist for installer/UI/profile/mock/manual hardware smoke testing.
python -m rytm_randomizer.cli manual-validation-kit-report

# Focus one phase for the current test pass.
python -m rytm_randomizer.cli manual-validation-kit-report --phase mock_rehearsal

# GUI/reviewer-ready JSON.
python -m rytm_randomizer.cli manual-validation-kit-report --json
```

The report prints operator instructions only. It does not launch the cockpit,
run the analyzer, write profile files, open a MIDI port, send MIDI, or execute
the armed smoke command it includes as manual instruction text.

---

## Manual feedback packet

`manual-feedback-packet-report` turns installer, cockpit, Profile Wizard,
analyzer, export, mock-control, pad-scope, and approved hardware-boundary
observations into deterministic reviewer evidence. It does not launch the GUI,
run audio analysis, write export files, open MIDI ports, or send MIDI.

```bash
python -m rytm_randomizer.cli manual-feedback-packet-report
python -m rytm_randomizer.cli manual-feedback-packet-report --scenario profile
python -m rytm_randomizer.cli manual-feedback-packet-report --scenario hardware --json
```

Scenarios: `full`, `installer`, `profile`, `mock`, `hardware`, `review`.

---

## Dual-machine target surface

```bash
python -m rytm_randomizer.cli dual-machine-target-report rytm   # Analog Rytm only
python -m rytm_randomizer.cli dual-machine-target-report a4     # Analog Four only
python -m rytm_randomizer.cli dual-machine-target-report both   # both registered devices
```

---

## Analog Rytm — kit + snapshot intelligence

| Command | Description |
|---|---|
| `rytm-12-pad-machine-matrix-report` | Passive Rytm **12-pad machine matrix** with machine compatibility per pad |
| `rytm-outbound-cc-repeatability-report [--control N] [--value N] [--json]` | Passive all-12-track outbound CC repeatability checklist for the next manual validation pass |
| `manual-feedback-packet-report [--scenario full|installer|profile|mock|hardware|review] [--json]` | Passive manual feedback packet for installer, wizard, analyzer, export, pad-scope, mock-control, and hardware-boundary review |
| `rytm-snapshot-pad-compatibility-report` | Passive **snapshot-pad compatibility** report per Rytm pad |
| `rytm-snapshot-intelligence-report KITS.syx --slot N [--list]` | Passive **snapshot intelligence** for one supported Rytm kit snapshot, or `--list` every supported snapshot in a SysEx dump |
| `rytm-snapshot-mutation-preview-report KITS.syx --slot N --depth N [--events --limit N]` | Passive **snapshot mutation preview** for one slot at a given depth; with `--events` include mock CC event rows |

```bash
python -m rytm_randomizer.cli rytm-12-pad-machine-matrix-report
python -m rytm_randomizer.cli rytm-outbound-cc-repeatability-report --json
python -m rytm_randomizer.cli rytm-snapshot-pad-compatibility-report
python -m rytm_randomizer.cli rytm-snapshot-intelligence-report KITS.syx --list
python -m rytm_randomizer.cli rytm-snapshot-intelligence-report KITS.syx --slot 7
python -m rytm_randomizer.cli rytm-snapshot-mutation-preview-report KITS.syx --slot 7 --depth 2 --events --limit 24
```

---

## Analog Rytm — style routing + mutation planning

```bash
python -m rytm_randomizer.cli style-profile-report   # list curated style profiles
python -m rytm_randomizer.cli style-crates-queue-journal-report --json
python -m rytm_randomizer.cli rytm-style-snapshot-routing-report KITS.syx birmingham_pressure --slot 7 --discovery 10
python -m rytm_randomizer.cli rytm-style-mutation-intent-report KITS.syx birmingham_pressure --slot 7 --discovery 45
python -m rytm_randomizer.cli rytm-style-mutation-render-plan-report KITS.syx birmingham_pressure --slot 7 --discovery 45
python -m rytm_randomizer.cli rytm-style-mutation-mock-preview-report KITS.syx jose_core_techno --slot 7 --discovery 45 --events --limit 24
python -m rytm_randomizer.cli rytm-style-kit-readiness-report KITS.syx jose_core_techno --limit 16
```

---

## Style Crates + Mutation Journal

`style-crates-queue-journal-report` is the passive MVP for browsing curated
mutation directions, staging future moves, and keeping replayable favorite
accidents. It lists Style Crates such as Dark Hypnotic, Peak Time, Hard Groove,
Dub Pressure, Industrial/Broken, Deep Minimal, Chaos Fills, Transitions, and
Saved Accidents; a deterministic staged queue; journal seed/value metadata; and
future danger modes for Live Safe, Studio Wild, Chaos, One-Shot Blast, and
Evolve Mode.

This command is metadata-only: it does not run an analyzer, write journal
files, launch a GUI, dispatch queue moves, open MIDI ports, or send MIDI.

```bash
python -m rytm_randomizer.cli style-crates-queue-journal-report
python -m rytm_randomizer.cli style-crates-queue-journal-report --json
python -m rytm_randomizer.cli style-crate-rehearsal-deck-report
python -m rytm_randomizer.cli style-crate-rehearsal-deck-report --crate industrial_broken --json
```

---

## Style Crate Rehearsal Deck

`style-crate-rehearsal-deck-report` consumes the passive Style Crates,
staged queue, and Mutation Journal metadata and renders GUI-ready rehearsal
cards. It is the next passive step toward a crate browser and live queue UI:
crate cards expose primary move, energy, risk, target pads, and operator
action; queue cards expose staged moves, dry-run-only status, recovery action,
and risk; journal cards expose replay seeds and guardrail mode.

The optional `--crate <key>` flag filters the deck to one crate. This command
does not launch the GUI, dispatch queue moves, replay journal entries, open
MIDI ports, or send MIDI.

```bash
python -m rytm_randomizer.cli style-crate-rehearsal-deck-report
python -m rytm_randomizer.cli style-crate-rehearsal-deck-report --json
python -m rytm_randomizer.cli style-crate-rehearsal-deck-report --crate industrial_broken
```

---

## Reference-style blueprint (Rytm + Analog Four)

`reference-style-blueprint-report` translates a description, audio file,
or library folder into an influence-only starting blueprint: 12 Analog
Rytm pad roles, 4 Analog Four track roles, normalized traits, depth caps,
parameter focus lanes, modulation ideas, and passive safety flags. It
does not create patterns, write files, open ports, or send MIDI.

```bash
python -m rytm_randomizer.cli reference-style-blueprint-report --description "Glenn Wilson style industrial pressure" --json
python -m rytm_randomizer.cli reference-style-blueprint-report --audio reference.wav
python -m rytm_randomizer.cli reference-style-blueprint-report --library reference-folder
```

---

## Analog Four — style routing + mutation planning

| Command | Description |
|---|---|
| `analog-four-style-snapshot-routing-report` | Passive **Analog Four style snapshot routing** balanced/wild-discovery routing |
| `analog-four-style-mutation-intent-report` | Passive Analog Four track/zone mutation intent |
| `analog-four-style-mutation-mock-preview-report` | Passive Analog Four mock CC rows (deferred while saved-kit offsets are promoted) |
| `analog-four-kit-catalog-report` | Passive Analog Four decoded kit catalog |
| `analog-four-oxi-macro-report` | Passive in-memory Analog Four OXI-style four-track macro preview |
| `analog-four-style-kit-readiness-report` | Passive per-kit Analog Four style-readiness sweep |

```bash
python -m rytm_randomizer.cli analog-four-style-snapshot-routing-report KITS.syx industrial_dark --slot 0 --discovery 50
python -m rytm_randomizer.cli analog-four-style-mutation-intent-report KITS.syx birmingham_pressure --slot 0 --discovery 45
python -m rytm_randomizer.cli analog-four-style-mutation-mock-preview-report KITS.syx jose_core_techno --slot 0 --discovery 45 --events --limit 24
python -m rytm_randomizer.cli analog-four-kit-catalog-report KITS.syx --limit 16
python -m rytm_randomizer.cli analog-four-oxi-macro-report hard-groove --seed 23 --intensity 6 --events --limit 0
python -m rytm_randomizer.cli analog-four-style-kit-readiness-report KITS.syx jose_core_techno --limit 16
```

`analog-four-oxi-macro-report` is a snapshot-free planning surface for the
Analog Four side of an OXI-style live rig. It uses existing manual-backed A4 CC
metadata to preview deterministic values across four tracks, but it does not
open a port, render real MIDI, or send anything. Use it to audition macro
shapes such as `home`, `hard-groove`, `dub-pressure`, and
`industrial-transition` before promoting any future A4 path into a gated
hardware plan.

---

## Rig-level (Rytm + Analog Four together)

| Command | Description |
|---|---|
| `dual-machine-style-kit-readiness-report` | Passive ranked Rytm + A4 kit-pair readiness sweep |
| `dual-machine-style-kit-selection-report` | Passive best live kit selections across both machines |
| `dual-machine-style-selection-mock-preview-report` | Passive best-**selection mock preview** without manually copying slots |
| `dual-machine-style-live-audition-report` | Passive **live audition** set across multiple style targets |
| `dual-machine-style-performance-set-plan-report` | Passive timed **performance set plan** for a long-form live arc |
| `dual-machine-style-snapshot-routing-report` | Passive rig-level **dual-machine style snapshot routing** |
| `dual-machine-style-mutation-intent-report` | Passive rig-level mutation intent (Rytm + Analog Four) |
| `dual-machine-style-mutation-mock-preview-report` | Passive rig-level mock CC rows + Analog Four deferred rows |

```bash
python -m rytm_randomizer.cli dual-machine-style-kit-readiness-report RYTM.syx A4.syx jose_core_techno --limit 16
python -m rytm_randomizer.cli dual-machine-style-kit-selection-report jose_core_techno --rytm RYTM.syx --analog-four A4.syx --limit 8
python -m rytm_randomizer.cli dual-machine-style-selection-mock-preview-report jose_core_techno --rytm RYTM.syx --analog-four A4.syx --events --limit 24
python -m rytm_randomizer.cli dual-machine-style-live-audition-report jose_core_techno birmingham_pressure warehouse_peak --rytm RYTM.syx --analog-four A4.syx --events --limit 8
python -m rytm_randomizer.cli dual-machine-style-performance-set-plan-report jose_core_techno birmingham_pressure warehouse_peak --rytm RYTM.syx --analog-four A4.syx --total-minutes 300 --discovery-start 35 --discovery-end 75 --events --limit 8
python -m rytm_randomizer.cli dual-machine-style-snapshot-routing-report RYTM.syx A4.syx warehouse_peak --rytm-slot 7 --a4-slot 0 --discovery 45
python -m rytm_randomizer.cli dual-machine-style-mutation-intent-report RYTM.syx A4.syx birmingham_pressure --rytm-slot 7 --a4-slot 0 --discovery 45
python -m rytm_randomizer.cli dual-machine-style-mutation-mock-preview-report RYTM.syx A4.syx jose_core_techno --rytm-slot 7 --a4-slot 0 --discovery 45 --events --limit 24
```

---

## Reference performance arcs (curated long-form set plans)

```bash
# List curated reference arcs for long-form live planning
python -m rytm_randomizer.cli style-performance-arc-report

# Inspect a specific arc
python -m rytm_randomizer.cli inspect-style-performance-arc jose_warehouse_five_hour

# Expand a reference arc into a timed dual-machine performance set planner
python -m rytm_randomizer.cli style-performance-arc-set-plan-report jose_warehouse_five_hour --rytm RYTM.syx --analog-four A4.syx --events --limit 8
```

---

## Live performance reports (operator-facing surfaces)

Each command produces deterministic JSON describing one operator-facing surface — they compose into the future live cockpit and the analyzer pipeline.

| Command | Surface |
|---|---|
| `style-performance-arc-live-cue-sheet-report` | **live cue sheet** with risk labels, hands-on moves, recovery cues |
| `style-performance-arc-reference-match-report` | **Reference-match** evidence packet for a description / track / library |
| `style-performance-arc-live-runbook-report` | **live runbook** — launch brief, stage packet, timeline cards, recovery cues |
| `style-performance-arc-stage-routing-report` | **stage routing** with cue-by-cue **route cards**, saved-kit slots, mock/deferred rows, recovery sequence |
| `style-performance-arc-stage-rehearsal-state-report` | **stage rehearsal** state with **go/rehearse/do-not-arm** cue states per machine |
| `style-performance-arc-live-show-export-report` | **live show export** packet with deterministic export id, machine **show handoff** manifest, cue launch script, recovery script |
| `style-performance-arc-live-transition-timeline-report` | **live transition timeline** with prep windows, **transition cards**, launch/hold/recovery prompts |
| `style-performance-arc-live-command-deck-report` | **live command deck** with current-cue **command cards**, prep/launch/hold/recovery actions, machine handoffs |
| `style-performance-arc-live-state-report` | **GUI-ready** **live state packet** (now/next cues, machine panels, action bar, warning stack) |
| `style-performance-arc-live-control-surface-report` | GUI / audio-analyzer **control surface** with header tiles, transport controls, cue cards, machine cards |
| `style-performance-arc-live-analyzer-handoff-report` | **analyzer handoff** with **FeatureReport meters**, top influence matches, capture prompts |
| `style-performance-arc-live-analyzer-targets-report` | **analyzer target** packet (rehearsal target bands, cue checkpoints, calibration steps, **future live analyzer comparison** JSON) |

---

## Live GUI / sidecar reports (one-screen state for the future cockpit)

The `live-gui-*` family is the GUI consumer contract — each report is one screen of state the cockpit can render without executing anything. Every command is passive: every raise is `ValueError` or `TypeError`, every panel is frozen, every output is deterministic.

| Command | Surface |
|---|---|
| `style-performance-arc-live-gui-analyzer-readiness-report` | **GUI/audio-analyzer readiness bundle** with panel manifest, stream wiring, operator workflow, **blocked active actions** |
| `style-performance-arc-live-gui-rehearsal-session-report` | **GUI rehearsal session packet** with task cards, **listen-only rehearsal take** cards, operator checklist |
| `style-performance-arc-live-gui-capture-queue-report` | **GUI/audio analyzer capture queue** with capture slots, suggested filenames, **analyzer job** cards |
| `style-performance-arc-live-gui-capture-review-report` | **GUI/audio analyzer capture review** with **go/repeat/hold** decisions, metric drift notes, hold reasons |
| `style-performance-arc-live-gui-sidecar-session-report` | **sidecar-ready GUI state** with panels, analyzer rows, capture decisions, **disabled active controls** |
| `style-performance-arc-live-gui-screen-contract-report` | **GUI screen contract** with ordered regions, component state, table rows, **disabled interaction controls** |
| `style-performance-arc-live-gui-render-tree-report` | **GUI render tree** — **deterministic root/region/component tree**, source bindings, disabled controls |
| `style-performance-arc-live-gui-analyzer-overlay-report` | **GUI analyzer overlay** with **meter widgets**, threshold markers, selected capture badge, node annotations |
| `style-performance-arc-live-gui-analyzer-frame-report` | **GUI analyzer frame** with ordered **frame events**, visual assertions, blocked actions |
| `style-performance-arc-live-gui-interaction-script-report` | **GUI interaction script** with ordered interaction steps, **control bindings**, disabled hardware locks |
| `style-performance-arc-live-gui-action-reducer-report` | **GUI action reducer** with deterministic **control transition** decisions, disabled hardware locks |
| `style-performance-arc-live-gui-controller-state-report` | **GUI controller state** with deterministic **control-state** rows, queued allowed actions, blocked controls |
| `style-performance-arc-live-gui-playback-transcript-report` | **GUI playback transcript** with deterministic **playback transcript** events, GUI assertions, analyzer checkpoints |
| `style-performance-arc-live-gui-playback-validation-report` | **GUI playback validation** matrix with deterministic future test-harness cases, harness steps (**validation matrix**) |
| `style-performance-arc-live-gui-test-harness-contract-report` | **GUI test-harness contract** with **Harness suites**, fixtures, bindings, blocked actions |
| `style-performance-arc-live-gui-test-harness-readiness-report` | **GUI test-harness readiness** with **readiness gates**, checks, rehearsal steps |
| `style-performance-arc-live-gui-implementation-bridge-report` | **GUI implementation bridge** with **view-model packets**, disabled component mounts, fixture bundles |
| `style-performance-arc-live-gui-desktop-blueprint-report` | **GUI desktop blueprint** with **desktop shell**, viewports, regions, widgets, bindings |
| `style-performance-arc-live-gui-desktop-app-plan-report` | **GUI desktop app plan** with **app shell**, routes, component file hints, state slices, style tokens |
| `style-performance-arc-live-gui-desktop-component-contract-report` | **GUI desktop component contract** with **component props**, disabled actions, test selectors |
| `style-performance-arc-live-gui-desktop-view-model-report` | **GUI desktop view model** with component view models, **state bindings**, disabled actions, style tokens |
| `style-performance-arc-live-gui-desktop-render-contract-report` | **GUI desktop render contract** with **render surfaces**, render bindings, style-token bindings |
| `style-performance-arc-live-gui-desktop-render-harness-report` | **GUI desktop render harness** with **surface harnesses**, binding harnesses, style-token checks |

Run any one with `--help` for its full flag set, or check the lazy command registry in [`rytm_randomizer/cli.py`](../rytm_randomizer/cli.py) for the complete catalogue.
