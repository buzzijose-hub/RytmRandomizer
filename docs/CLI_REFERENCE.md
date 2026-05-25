# CLI reference

This is the full passive CLI surface for RytmRandomizer. Every command here is **passive by construction** — it opens no MIDI port and sends no MIDI. The project-wide passive-safety sweep in [`tests/test_real_midi_passive_cli_safety.py`](../tests/test_real_midi_passive_cli_safety.py) auto-discovers commands from the lazy registry and runs every one in a subprocess to assert no `mido` / `rtmidi` / adapter modules load and no armed-output tokens leak.

For the headline commands (cockpit, wizard, export, live-set planning) see the [README](../README.md#cli-cheat-sheet).

For the armed runtime (the V1.34 four-pad interactive shell), launch `rytm-randomizer --arm` and follow the in-shell menu. The armed runtime is the original V1.34 behaviour; its byte-frozen reference output lives in [`tests/fixtures/v134_parity/`](../tests/fixtures/v134_parity/).

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

## Dual-machine target surface

```bash
python -m rytm_randomizer.cli dual-machine-target-report rytm   # Analog Rytm only
python -m rytm_randomizer.cli dual-machine-target-report a4     # Analog Four only
python -m rytm_randomizer.cli dual-machine-target-report both   # both registered devices
```

---

## Analog Rytm — kit + snapshot intelligence

```bash
# Passive Rytm 12-pad machine compatibility matrix
python -m rytm_randomizer.cli rytm-12-pad-machine-matrix-report

# Passive snapshot readiness per Rytm pad
python -m rytm_randomizer.cli rytm-snapshot-pad-compatibility-report

# List supported Rytm kit snapshots in a SysEx dump
python -m rytm_randomizer.cli rytm-snapshot-intelligence-report KITS.syx --list

# Passive intelligence for one Rytm kit snapshot
python -m rytm_randomizer.cli rytm-snapshot-intelligence-report KITS.syx --slot 7

# Passive mutation preview — mock-only, no MIDI send
python -m rytm_randomizer.cli rytm-snapshot-mutation-preview-report KITS.syx --slot 7 --depth 2
python -m rytm_randomizer.cli rytm-snapshot-mutation-preview-report KITS.syx --slot 7 --depth 2 --events --limit 24
```

---

## Analog Rytm — style routing + mutation planning

```bash
# Reference-close style routing
python -m rytm_randomizer.cli rytm-style-snapshot-routing-report KITS.syx birmingham_pressure --slot 7 --discovery 10
python -m rytm_randomizer.cli rytm-style-snapshot-routing-report KITS.syx birmingham_pressure --discovery 95 --json

# Style mutation intent (zone / parameter targets)
python -m rytm_randomizer.cli rytm-style-mutation-intent-report KITS.syx birmingham_pressure --slot 7 --discovery 45
python -m rytm_randomizer.cli rytm-style-mutation-intent-report KITS.syx birmingham_pressure --discovery 95 --json

# Render-plan target-value windows
python -m rytm_randomizer.cli rytm-style-mutation-render-plan-report KITS.syx birmingham_pressure --slot 7 --discovery 45
python -m rytm_randomizer.cli rytm-style-mutation-render-plan-report KITS.syx birmingham_pressure --discovery 95 --json

# Mock CC preview rows (no MIDI send)
python -m rytm_randomizer.cli rytm-style-mutation-mock-preview-report KITS.syx jose_core_techno --slot 7 --discovery 45 --events --limit 24
python -m rytm_randomizer.cli rytm-style-mutation-mock-preview-report KITS.syx jose_core_techno --json

# Per-kit style readiness sweep
python -m rytm_randomizer.cli rytm-style-kit-readiness-report KITS.syx jose_core_techno --limit 16
python -m rytm_randomizer.cli rytm-style-kit-readiness-report KITS.syx jose_core_techno --json
```

---

## Analog Four — style routing + mutation planning

```bash
python -m rytm_randomizer.cli analog-four-style-snapshot-routing-report KITS.syx industrial_dark --slot 0 --discovery 50
python -m rytm_randomizer.cli analog-four-style-snapshot-routing-report KITS.syx industrial_dark --discovery 95 --json
python -m rytm_randomizer.cli analog-four-style-mutation-intent-report KITS.syx birmingham_pressure --slot 0 --discovery 45
python -m rytm_randomizer.cli analog-four-style-mutation-intent-report KITS.syx birmingham_pressure --discovery 95 --json
python -m rytm_randomizer.cli analog-four-style-mutation-mock-preview-report KITS.syx jose_core_techno --slot 0 --discovery 45 --events --limit 24
python -m rytm_randomizer.cli analog-four-style-mutation-mock-preview-report KITS.syx jose_core_techno --json
python -m rytm_randomizer.cli analog-four-kit-catalog-report KITS.syx --limit 16
python -m rytm_randomizer.cli analog-four-kit-catalog-report KITS.syx --json
python -m rytm_randomizer.cli analog-four-style-kit-readiness-report KITS.syx jose_core_techno --limit 16
```

---

## Rig-level (Rytm + Analog Four together)

```bash
# Ranked kit-pair readiness across both machines
python -m rytm_randomizer.cli dual-machine-style-kit-readiness-report RYTM.syx A4.syx jose_core_techno --limit 16

# Best live kit selections across both machines
python -m rytm_randomizer.cli dual-machine-style-kit-selection-report jose_core_techno --rytm RYTM.syx --analog-four A4.syx --limit 8
python -m rytm_randomizer.cli dual-machine-style-kit-selection-report jose_core_techno --rytm RYTM.syx --scope rytm-only --json

# Mock preview without manually copying slots
python -m rytm_randomizer.cli dual-machine-style-selection-mock-preview-report jose_core_techno --rytm RYTM.syx --analog-four A4.syx --events --limit 24

# Live audition set across multiple style targets
python -m rytm_randomizer.cli dual-machine-style-live-audition-report jose_core_techno birmingham_pressure warehouse_peak --rytm RYTM.syx --analog-four A4.syx --events --limit 8

# Timed performance set plan for a long-form live arc
python -m rytm_randomizer.cli dual-machine-style-performance-set-plan-report jose_core_techno birmingham_pressure warehouse_peak --rytm RYTM.syx --analog-four A4.syx --total-minutes 300 --discovery-start 35 --discovery-end 75 --events --limit 8

# Rig-level routing + mutation intent + mock preview
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

# Rank all reference arcs against saved kit banks
python -m rytm_randomizer.cli style-performance-arc-readiness-report --rytm RYTM.syx --analog-four A4.syx --limit 8

# Pick the best-ready reference arc and embed its timed set-plan preview
python -m rytm_randomizer.cli style-performance-arc-audition-packet-report --rytm RYTM.syx --analog-four A4.syx --events --limit 8

# Preflight checklist + segment runbook
python -m rytm_randomizer.cli style-performance-arc-rehearsal-manifest-report --rytm RYTM.syx --analog-four A4.syx --events --limit 8

# Launch checklist + passive commands + live segment cards
python -m rytm_randomizer.cli style-performance-arc-live-session-packet-report --rytm RYTM.syx --analog-four A4.syx --events --limit 8

# Segment-level mock render rows
python -m rytm_randomizer.cli style-performance-arc-live-render-bundle-report --rytm RYTM.syx --analog-four A4.syx --events --limit 8

# Live cue sheet with risk labels, hands-on moves, recovery cues
python -m rytm_randomizer.cli style-performance-arc-live-cue-sheet-report --rytm RYTM.syx --analog-four A4.syx --events --limit 8
```

---

## Live GUI / sidecar / analyzer reports (40+ surfaces)

The codebase has a deep set of GUI-facing passive reports that compose into a future cockpit and analyzer pipeline. Each one is one-screen state that the live cockpit can render without executing anything.

```bash
# Reference-match nonblank text/audio/library influence evidence to an arc + cue sheet
python -m rytm_randomizer.cli style-performance-arc-reference-match-report \
    --description "Jeff Mills Oscar Mulero Birmingham pressure" \
    --rytm RYTM.syx --analog-four A4.syx --events --limit 8

# Live runbook (launch brief, stage packet, timeline cards, recovery cues)
python -m rytm_randomizer.cli style-performance-arc-live-runbook-report \
    --description "..." --rytm RYTM.syx --analog-four A4.syx --events --limit 8

# Stage routing (cue-by-cue route cards, saved-kit slots, recovery sequence)
python -m rytm_randomizer.cli style-performance-arc-stage-routing-report \
    --description "..." --rytm RYTM.syx --analog-four A4.syx --events --limit 8

# Stage rehearsal state (go / rehearse / do-not-arm states per cue)
python -m rytm_randomizer.cli style-performance-arc-stage-rehearsal-state-report \
    --description "..." --rytm RYTM.syx --analog-four A4.syx --events --limit 8

# One-screen live set cockpit packet
python -m rytm_randomizer.cli style-performance-arc-live-set-cockpit-report \
    --description "..." --rytm RYTM.syx --analog-four A4.syx --events --limit 8

# Live show export packet (deterministic export id, machine handoff manifest, cue scripts)
python -m rytm_randomizer.cli style-performance-arc-live-show-export-report \
    --description "..." --rytm RYTM.syx --analog-four A4.syx --events --limit 8

# Live transition timeline (prep windows, transition cards, hold/recovery prompts)
python -m rytm_randomizer.cli style-performance-arc-live-transition-timeline-report \
    --description "..." --rytm RYTM.syx --analog-four A4.syx --events --limit 8

# Live command deck for the current cue
python -m rytm_randomizer.cli style-performance-arc-live-command-deck-report \
    --description "..." --rytm RYTM.syx --analog-four A4.syx --cue 1 --lookahead 2 --events --limit 8

# GUI-ready live state packet (now/next cues, machine panels, action bar)
python -m rytm_randomizer.cli style-performance-arc-live-state-report \
    --description "..." --rytm RYTM.syx --analog-four A4.syx --cue 1 --lookahead 2 --events --limit 8

# GUI / audio-analyzer readiness gates + launch mode
python -m rytm_randomizer.cli style-performance-arc-live-readiness-report \
    --description "..." --rytm RYTM.syx --analog-four A4.syx --cue 1 --lookahead 2

# Live control surface (header tiles, transport, cue cards, analyzer cards)
python -m rytm_randomizer.cli style-performance-arc-live-control-surface-report \
    --description "..." --rytm RYTM.syx --analog-four A4.syx --cue 1 --lookahead 2

# Analyzer handoff packet (FeatureReport meters, influence matches, capture prompts)
python -m rytm_randomizer.cli style-performance-arc-live-analyzer-handoff-report \
    --description "..." --rytm RYTM.syx --analog-four A4.syx --cue 1 --lookahead 2 --matches 3

# Analyzer target packet (rehearsal target bands, cue checkpoints, calibration steps)
python -m rytm_randomizer.cli style-performance-arc-live-analyzer-targets-report \
    --description "..." --rytm RYTM.syx --analog-four A4.syx --cue 1 --lookahead 2 --matches 3
```

The full set of `live-gui-*` reports continues — capture queue, capture review, sidecar session, screen contract, render tree, analyzer overlay, analyzer frame, interaction script, action reducer, controller state, playback transcript, playback validation, test harness contract / readiness, implementation bridge, desktop blueprint / app plan / component contract / view model / render contract / render harness, cockpit boundary readiness — each composing into the next layer of the future GUI / analyzer pipeline.

Run any one with `--help` for its full flag set, or check the lazy command registry in [`rytm_randomizer/cli.py`](../rytm_randomizer/cli.py) for the complete catalogue.
