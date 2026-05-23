# Style analysis (WS-V Layers 1-2)

`rytm_randomizer/style_analysis/` is the **deterministic measurement**
half of the four-layer guardrails system described in
`GUARDRAILS_DESIGN_SPEC.md`. It turns reference material (audio files,
libraries, descriptions) into a typed `FeatureReport`, which the WS-V
interpretation skill (`.claude/skills/MusicLibraryGuardrails/`) then
turns into a draft `GuardrailProfile` for the WS-W validator.

## The four-layer model

| Layer | Owner | Module / file | Output |
|---|---|---|---|
| **1. Measurement** | code | `rytm_randomizer/style_analysis/` | `FeatureReport` (typed, content-hashed, confidence-tagged) |
| **2. Interpretation** | agent (+ skill) | `.claude/skills/MusicLibraryGuardrails/` + `.claude/skills/DataAnalysisGuardrails/` | DRAFT-state `GuardrailProfile` |
| **3. Validation** | code | `rytm_randomizer/guardrails/validation.py` (WS-W, future) | VALIDATED or REJECTED profile |
| **4. Consumption** | code | `rytm_randomizer/guardrails/resolver.py` (WS-W, future) + engines | Resolved bounds the randomizer mutates within |

WS-V owns **Layers 1 and 2**. WS-W owns Layers 3 and 4. The seam is the
typed Guardrail Profile contract in
`rytm_randomizer/guardrails/schema.py` (already shipped by WS-W's first
step); WS-V *produces* it, WS-W *validates and consumes* it.

## Installing the `style` extra

Layer 1's deterministic audio extraction relies on
[`librosa`](https://librosa.org/). It is an **optional** dependency -
the core install does not pull it in, so a user who only needs the
description-only path (or only the rest of the package) is not paying
for the heavy audio stack.

```bash
# Core install (description-only path works; no audio measurement):
pip install -e ".[dev]"

# Full audio-extraction install:
pip install -e ".[style,dev]"
```

If you call `extract_from_audio` / `extract_from_partial` /
`analyze_library` (with audio files present) without the `style` extra,
the call raises `StyleAnalysisDependencyError` with an actionable
message. Lazy-import discipline means importing
`rytm_randomizer.style_analysis` itself never touches `librosa`; that
happens only when an audio path actually runs.

## Running an analysis

### Description only (no audio, LOW confidence)

```python
from rytm_randomizer.style_analysis import extract_from_description
from rytm_randomizer.guardrails.schema import SourceType

report = extract_from_description(
    "rolling hypnotic techno, 128 BPM, anchored low end",
    source_type=SourceType.STYLE_DESCRIPTION_ONLY,
)
# report.confidence is Confidence.LOW; numeric fields are zeroed
# placeholders. The interpretation skill (Layer 2) fills in mutation
# intent from the description directly.
```

### Single audio file (HIGH confidence)

```python
from pathlib import Path
from rytm_randomizer.style_analysis import extract_from_audio

report = extract_from_audio(Path("reference.wav"))
# report.bpm, .kick_density, .low_end_weight, .spectral_brightness,
# .texture_noise, .energy_arc, .tempo_stability are measured
# deterministically by librosa.
```

### Library (folder of audio, HIGH confidence)

```python
from pathlib import Path
from rytm_randomizer.style_analysis import analyze_library

report = analyze_library(Path("library/"))
# Walks WAV/AIF/AIFF/FLAC/MP3 files (sorted, deterministic), aggregates
# per-file features with median (scalars) + element-wise mean (energy
# arc). Empty directory -> LOW-confidence zeroed report.
```

### Partial (some audio + user notes, MEDIUM confidence)

```python
from pathlib import Path
from rytm_randomizer.style_analysis import extract_from_partial

report = extract_from_partial(
    [Path("a.wav"), Path("b.wav")],
    notes="user prefers tighter kicks, dryer texture",
)
```

### Hashing for traceability

```python
from rytm_randomizer.style_analysis import compute_feature_report_hash

digest = compute_feature_report_hash(report)
# Same canonical-JSON SHA-256 pattern as
# rytm_randomizer.guardrails.schema.compute_content_hash. The WS-V
# interpretation skill stamps `digest` into
# `Provenance.feature_report_hash` so the validated profile points back
# to the exact measurement it was derived from.
```

## Determinism guarantee

For a given audio file, `extract_from_audio` always returns the same
measurements (modulo the `derived_at` timestamp, which is wall-clock).
This is asserted by the librosa-gated test
`test_extract_from_audio_runs_on_synthetic_signal` in
`tests/test_style_analysis.py`: a second extraction on the same WAV
yields identical `bpm`, `tempo_stability`, `spectral_brightness`, and
`energy_arc`.

Implementation choices that make this hold:

- Librosa is called with `sr=22050, mono=True` (explicit sample rate +
  channel collapse). No defaults that vary by system.
- The energy arc is sampled at 8 evenly-spaced indices via
  `numpy.linspace`, then normalised against the peak RMS. No
  randomness.
- The library walker sorts file paths before aggregation
  (`Path.rglob("*")` -> `sorted(...)`), so the per-file order is
  deterministic across machines/filesystems.

The description-only path is deterministic by construction (it never
reads audio).

## Copyright safety - "influence, not replica"

The schema can express *behavioral mutation boundaries* (ranges,
classes, directions, risk). It deliberately has **no field for a
melody, an arrangement map, a copyrighted hook, or a sound-alike
patch**. The Guardrail Profile literally cannot carry a replica through
this contract because the contract has nowhere to put one
(`GUARDRAILS_DESIGN_SPEC.md` section 7.3). Reference -> discovery is
enforced by the *shape* of the artifact, not by the agent's goodwill.

When the user analyzes a commercial track or reference artist, the
interpretation skill captures *high-level musical traits* (energy
profile, density, texture, mutation directions) - never melodies,
arrangements, or sound-alike sound design. The skill explicitly bans
language like "clone this track" / "make it identical" and uses
language like "inspired by the reference behavior" / "original anchor
direction".

This is the **influence not replica** rule, lifted unchanged from the
pre-schema `MusicLibraryGuardrails` skill.

## Reference arcs to live render bundles and cue sheets

The current passive bridge from influence language to machine-planning
metadata is the style-profile / style-target / performance-arc report
stack. Reference arcs such as `jose_warehouse_five_hour` remain
high-level planning narratives; they do not copy arrangements, melodies,
or patches from Jeff Mills, Oscar Mulero, Glenn Wilson, Stigmata,
Regis, Surgeon, or other references.

For live rehearsal, the most complete passive surfaces are:

```bash
python -m rytm_randomizer.cli style-performance-arc-live-render-bundle-report \
  --rytm <rytm-syx-path> --analog-four <a4-syx-path> --events --limit 8

python -m rytm_randomizer.cli style-performance-arc-live-cue-sheet-report \
  --rytm <rytm-syx-path> --analog-four <a4-syx-path> --events --limit 8

python -m rytm_randomizer.cli style-performance-arc-reference-match-report \
  --description "Jeff Mills Oscar Mulero Birmingham pressure" \
  --rytm <rytm-syx-path> --analog-four <a4-syx-path> --events --limit 8

python -m rytm_randomizer.cli style-performance-arc-stage-routing-report \
  --description "Jeff Mills Oscar Mulero Birmingham pressure" \
  --rytm <rytm-syx-path> --analog-four <a4-syx-path> --events --limit 8

python -m rytm_randomizer.cli style-performance-arc-stage-rehearsal-state-report \
  --description "Jeff Mills Oscar Mulero Birmingham pressure" \
  --rytm <rytm-syx-path> --analog-four <a4-syx-path> --events --limit 8

python -m rytm_randomizer.cli style-performance-arc-live-set-cockpit-report \
  --description "Jeff Mills Oscar Mulero Birmingham pressure" \
  --rytm <rytm-syx-path> --analog-four <a4-syx-path> --events --limit 8

python -m rytm_randomizer.cli style-performance-arc-live-show-export-report \
  --description "Jeff Mills Oscar Mulero Birmingham pressure" \
  --rytm <rytm-syx-path> --analog-four <a4-syx-path> --events --limit 8

python -m rytm_randomizer.cli style-performance-arc-live-transition-timeline-report \
  --description "Jeff Mills Oscar Mulero Birmingham pressure" \
  --rytm <rytm-syx-path> --analog-four <a4-syx-path> --events --limit 8

python -m rytm_randomizer.cli style-performance-arc-live-command-deck-report \
  --description "Jeff Mills Oscar Mulero Birmingham pressure" \
  --rytm <rytm-syx-path> --analog-four <a4-syx-path> \
  --cue 1 --lookahead 2 --events --limit 8

python -m rytm_randomizer.cli style-performance-arc-live-state-report \
  --description "Jeff Mills Oscar Mulero Birmingham pressure" \
  --rytm <rytm-syx-path> --analog-four <a4-syx-path> \
  --cue 1 --lookahead 2 --events --limit 8

python -m rytm_randomizer.cli style-performance-arc-live-analyzer-targets-report \
  --description "Jeff Mills Oscar Mulero Birmingham pressure" \
  --rytm <rytm-syx-path> --analog-four <a4-syx-path> \
  --cue 1 --lookahead 2 --matches 3

python -m rytm_randomizer.cli style-performance-arc-live-gui-analyzer-readiness-report \
  --description "Jeff Mills Oscar Mulero Birmingham pressure" \
  --rytm <rytm-syx-path> --analog-four <a4-syx-path> \
  --cue 1 --lookahead 2 --matches 3

python -m rytm_randomizer.cli style-performance-arc-live-gui-rehearsal-session-report \
  --description "Jeff Mills Oscar Mulero Birmingham pressure" \
  --rytm <rytm-syx-path> --analog-four <a4-syx-path> \
  --cue 1 --lookahead 2 --matches 3 --takes 2

python -m rytm_randomizer.cli style-performance-arc-live-gui-capture-queue-report \
  --description "Jeff Mills Oscar Mulero Birmingham pressure" \
  --rytm <rytm-syx-path> --analog-four <a4-syx-path> \
  --cue 1 --lookahead 2 --matches 3 --takes 2 --capture-prefix warehouse

python -m rytm_randomizer.cli style-performance-arc-live-gui-capture-review-report \
  --description "Jeff Mills Oscar Mulero Birmingham pressure" \
  --capture-description "captured warehouse take with tight low end and building pressure" \
  --rytm <rytm-syx-path> --analog-four <a4-syx-path> \
  --cue 1 --lookahead 2 --matches 3 --takes 2 --slot capture-001 --capture-prefix warehouse

python -m rytm_randomizer.cli style-performance-arc-live-gui-sidecar-session-report \
  --description "Jeff Mills Oscar Mulero Birmingham pressure" \
  --capture-description "captured warehouse take with tight low end and building pressure" \
  --rytm <rytm-syx-path> --analog-four <a4-syx-path> \
  --cue 1 --lookahead 2 --matches 3 --takes 2 --slot capture-001 --capture-prefix warehouse \
  --sidecar-label "Warehouse sidecar"

python -m rytm_randomizer.cli style-performance-arc-live-gui-render-tree-report \
  --description "Jeff Mills Oscar Mulero Birmingham pressure" \
  --capture-description "captured warehouse take with tight low end and building pressure" \
  --rytm <rytm-syx-path> --analog-four <a4-syx-path> \
  --cue 1 --lookahead 2 --matches 3 --takes 2 --slot capture-001 --capture-prefix warehouse \
  --sidecar-label "Warehouse sidecar" --screen-label "Warehouse screen" \
  --render-target desktop-sidecar --density standard

python -m rytm_randomizer.cli style-performance-arc-live-gui-analyzer-overlay-report \
  --description "Jeff Mills Oscar Mulero Birmingham pressure" \
  --capture-description "captured warehouse take with tight low end and building pressure" \
  --rytm <rytm-syx-path> --analog-four <a4-syx-path> \
  --cue 1 --lookahead 2 --matches 3 --takes 2 --slot capture-001 --capture-prefix warehouse \
  --sidecar-label "Warehouse sidecar" --screen-label "Warehouse screen" \
  --render-target desktop-sidecar --density standard --overlay-label "Warehouse overlay"

python -m rytm_randomizer.cli style-performance-arc-live-gui-analyzer-frame-report \
  --description "Jeff Mills Oscar Mulero Birmingham pressure" \
  --capture-description "captured warehouse take with tight low end and building pressure" \
  --rytm <rytm-syx-path> --analog-four <a4-syx-path> \
  --cue 1 --lookahead 2 --matches 3 --takes 2 --slot capture-001 --capture-prefix warehouse \
  --sidecar-label "Warehouse sidecar" --screen-label "Warehouse screen" \
  --render-target desktop-sidecar --density standard --overlay-label "Warehouse overlay" \
  --frame-label "Warehouse frame"

python -m rytm_randomizer.cli style-performance-arc-live-gui-interaction-script-report \
  --description "Jeff Mills Oscar Mulero Birmingham pressure" \
  --capture-description "captured warehouse take with tight low end and building pressure" \
  --rytm <rytm-syx-path> --analog-four <a4-syx-path> \
  --cue 1 --lookahead 2 --matches 3 --takes 2 --slot capture-001 --capture-prefix warehouse \
  --sidecar-label "Warehouse sidecar" --screen-label "Warehouse screen" \
  --render-target desktop-sidecar --density standard --overlay-label "Warehouse overlay" \
  --frame-label "Warehouse frame" --interaction-label "Warehouse interactions"

python -m rytm_randomizer.cli style-performance-arc-live-gui-action-reducer-report \
  --description "Jeff Mills Oscar Mulero Birmingham pressure" \
  --capture-description "captured warehouse take with tight low end and building pressure" \
  --rytm <rytm-syx-path> --analog-four <a4-syx-path> \
  --cue 1 --lookahead 2 --matches 3 --takes 2 --slot capture-001 --capture-prefix warehouse \
  --sidecar-label "Warehouse sidecar" --screen-label "Warehouse screen" \
  --render-target desktop-sidecar --density standard --overlay-label "Warehouse overlay" \
  --frame-label "Warehouse frame" --interaction-label "Warehouse interactions" \
  --reducer-label "Warehouse reducer"

python -m rytm_randomizer.cli style-performance-arc-live-gui-controller-state-report \
  --description "Jeff Mills Oscar Mulero Birmingham pressure" \
  --capture-description "captured warehouse take with tight low end and building pressure" \
  --rytm <rytm-syx-path> --analog-four <a4-syx-path> \
  --cue 1 --lookahead 2 --matches 3 --takes 2 --slot capture-001 --capture-prefix warehouse \
  --sidecar-label "Warehouse sidecar" --screen-label "Warehouse screen" \
  --render-target desktop-sidecar --density standard --overlay-label "Warehouse overlay" \
  --frame-label "Warehouse frame" --interaction-label "Warehouse interactions" \
  --reducer-label "Warehouse reducer" --controller-label "Warehouse controller"

python -m rytm_randomizer.cli style-performance-arc-live-gui-implementation-bridge-report \
  --description "Jeff Mills Oscar Mulero Birmingham pressure" \
  --capture-description "captured warehouse take with tight low end and building pressure" \
  --rytm <rytm-syx-path> --analog-four <a4-syx-path> \
  --cue 1 --lookahead 2 --matches 3 --takes 2 --slot capture-001 --capture-prefix warehouse \
  --sidecar-label "Warehouse sidecar" --screen-label "Warehouse screen" \
  --render-target desktop-sidecar --density standard --overlay-label "Warehouse overlay" \
  --frame-label "Warehouse frame" --interaction-label "Warehouse interactions" \
  --reducer-label "Warehouse reducer" --controller-label "Warehouse controller" \
  --playback-label "Warehouse playback" --validation-label "Warehouse validation" \
  --harness-label "Warehouse harness" --readiness-label "Warehouse readiness" \
  --bridge-label "Warehouse implementation bridge"

python -m rytm_randomizer.cli style-performance-arc-live-gui-desktop-blueprint-report \
  --description "Jeff Mills Oscar Mulero Birmingham pressure" \
  --capture-description "captured warehouse take with tight low end and building pressure" \
  --rytm <rytm-syx-path> --analog-four <a4-syx-path> \
  --cue 1 --lookahead 2 --matches 3 --takes 2 --slot capture-001 --capture-prefix warehouse \
  --sidecar-label "Warehouse sidecar" --screen-label "Warehouse screen" \
  --render-target desktop-sidecar --density standard --overlay-label "Warehouse overlay" \
  --frame-label "Warehouse frame" --interaction-label "Warehouse interactions" \
  --reducer-label "Warehouse reducer" --controller-label "Warehouse controller" \
  --playback-label "Warehouse playback" --validation-label "Warehouse validation" \
  --harness-label "Warehouse harness" --readiness-label "Warehouse readiness" \
  --bridge-label "Warehouse implementation bridge" \
  --blueprint-label "Warehouse desktop blueprint" --desktop-shell operator-dashboard

python -m rytm_randomizer.cli style-performance-arc-live-gui-desktop-app-plan-report \
  --description "Jeff Mills Oscar Mulero Birmingham pressure" \
  --capture-description "captured warehouse take with tight low end and building pressure" \
  --rytm <rytm-syx-path> --analog-four <a4-syx-path> \
  --cue 1 --lookahead 2 --matches 3 --takes 2 --slot capture-001 --capture-prefix warehouse \
  --sidecar-label "Warehouse sidecar" --screen-label "Warehouse screen" \
  --render-target desktop-sidecar --density standard --overlay-label "Warehouse overlay" \
  --frame-label "Warehouse frame" --interaction-label "Warehouse interactions" \
  --reducer-label "Warehouse reducer" --controller-label "Warehouse controller" \
  --playback-label "Warehouse playback" --validation-label "Warehouse validation" \
  --harness-label "Warehouse harness" --readiness-label "Warehouse readiness" \
  --bridge-label "Warehouse implementation bridge" \
  --blueprint-label "Warehouse desktop blueprint" --desktop-shell operator-dashboard \
  --app-plan-label "Warehouse desktop app plan" --framework-target desktop-python

python -m rytm_randomizer.cli style-performance-arc-live-gui-desktop-component-contract-report \
  --description "Jeff Mills Oscar Mulero Birmingham pressure" \
  --capture-description "captured warehouse take with tight low end and building pressure" \
  --rytm <rytm-syx-path> --analog-four <a4-syx-path> \
  --cue 1 --lookahead 2 --matches 3 --takes 2 --slot capture-001 --capture-prefix warehouse \
  --sidecar-label "Warehouse sidecar" --screen-label "Warehouse screen" \
  --render-target desktop-sidecar --density standard --overlay-label "Warehouse overlay" \
  --frame-label "Warehouse frame" --interaction-label "Warehouse interactions" \
  --reducer-label "Warehouse reducer" --controller-label "Warehouse controller" \
  --playback-label "Warehouse playback" --validation-label "Warehouse validation" \
  --harness-label "Warehouse harness" --readiness-label "Warehouse readiness" \
  --bridge-label "Warehouse implementation bridge" \
  --blueprint-label "Warehouse desktop blueprint" --desktop-shell operator-dashboard \
  --app-plan-label "Warehouse desktop app plan" --framework-target desktop-python \
  --component-contract-label "Warehouse component contract" --selector-prefix warehouse-live
```

The capture review report is the passive decision layer after the queue: it
compares captured FeatureReport evidence against the queued target metrics and
prints go/repeat/hold guidance, metric drift notes, hold reasons, deterministic
JSON, and replayable passive commands without recording audio, opening ports, or
sending MIDI.

The sidecar session report consumes that capture review and emits one
sidecar-ready GUI state: overview/current-cue/machine/analyzer/capture/safety
panels, analyzer rows, capture decision rows, disabled active controls, blocked
actions, deterministic JSON, and replayable passive commands without opening
ports or sending MIDI.

The render-tree report consumes the screen contract and emits deterministic
root/region/component/table-row GUI nodes plus source bindings, blocked actions,
JSON, and replayable passive commands for future desktop GUI and audio-analyzer
test harnesses without launching a GUI, writing files, opening ports, or
sending MIDI.

The analyzer-overlay report consumes the render tree and emits meter widgets,
threshold markers, selected capture badges, render-node annotations, blocked
actions, JSON, and replayable passive commands for future desktop GUI and
audio-analyzer overlays without launching a GUI, recording audio, opening ports,
or sending MIDI.

The analyzer-frame report consumes the overlay and emits ordered frame events,
visual assertions, blocked actions, JSON, and replayable passive commands for
future desktop GUI test harnesses without rendering frames, recording audio,
opening ports, or sending MIDI.

The interaction-script report consumes the analyzer frame and emits ordered
interaction steps, GUI control bindings, disabled hardware locks, blocked
actions, JSON, and replayable passive commands for future desktop GUI operator
flows without launching a GUI, dispatching GUI events, opening ports, or
sending MIDI.

The action-reducer report consumes the interaction script and emits deterministic
control transition decisions, blocked active actions, controller state metadata,
JSON, and replayable passive commands for future desktop GUI reducer tests
without launching a GUI, dispatching GUI events, dispatching reducer events,
opening ports, or sending MIDI.

The controller-state report consumes the action reducer and emits deterministic
control-state rows, queued allowed GUI actions, blocked controls, JSON, and
replayable passive commands for future desktop GUI state-machine tests without
launching a GUI, dispatching GUI events, mutating a GUI state store, opening
ports, or sending MIDI.

The playback-transcript report consumes the controller state and emits
deterministic playback timeline events, GUI playback assertions, analyzer
checkpoints, blocked active actions, JSON, and replayable passive commands for
future desktop GUI and GUI test-harness flows without launching a GUI,
dispatching GUI events, mutating a GUI state store, recording audio, opening
ports, or sending MIDI.

The playback-validation report consumes the playback transcript and emits a
deterministic validation matrix for future desktop GUI and audio-analyzer test
harnesses. It preserves harness steps, timeline/assertion/analyzer/safety
cases, blocked active actions, JSON, and replayable passive commands without
launching a GUI, running a test harness, executing commands, recording audio,
opening ports, or sending MIDI.

The test-harness contract report consumes the playback-validation matrix and
emits deterministic GUI/audio-analyzer harness metadata. It preserves Harness
suites, fixture contracts, selector bindings, blocked active actions, JSON, and
replayable passive commands without launching a GUI, running a harness, writing
files, reading audio streams, opening ports, or sending MIDI.

The test-harness readiness report consumes that contract and emits deterministic
GUI/audio-analyzer rehearsal readiness metadata. It preserves readiness gates,
readiness checks, rehearsal steps, blocked active actions, JSON, and replayable
passive commands without launching a GUI, running a harness, writing files,
reading or comparing audio streams, opening ports, or sending MIDI.

The implementation bridge report consumes that readiness packet and emits
deterministic future-GUI wiring metadata. It preserves view-model packets,
disabled component mounts, fixture bundles, implementation gates, blocked
active actions, JSON, and replayable passive commands without launching a GUI,
starting a renderer, running a harness, writing files, reading or comparing
audio streams, opening ports, or sending MIDI.

The desktop blueprint report consumes that implementation bridge and emits
future desktop-GUI layout metadata. It preserves desktop shell selection,
viewports, regions, widgets, view-model bindings, fixture file hints,
acceptance checks, blocked active actions, JSON, and replayable passive
commands without launching a GUI, starting a renderer, writing files, opening
ports, or sending MIDI.

The desktop app-plan report consumes that blueprint and emits future GUI desktop
app implementation metadata. It preserves app shell selection, routes, component
file hints, state slices, style tokens, acceptance checks, blocked active
actions, JSON, and replayable passive commands without launching a GUI, starting
a dev server or bundler, writing files, opening ports, or sending MIDI.

The desktop component-contract report consumes that app plan and emits future GUI
desktop component implementation metadata. It preserves component props,
disabled actions, test selectors, acceptance checks, blocked active actions,
JSON, and replayable passive commands without launching a GUI, mounting
components, dispatching GUI events, writing files, opening ports, or sending
MIDI.

The live render bundle selects the best ready or partial reference arc
for the saved kit banks, embeds the live-session packet, then exposes
each segment's mock render preview rows and Analog Four deferred rows.
The live cue sheet consumes that bundle and turns it into operator cues:
preflight checks, per-segment risk labels, hands-on moves, go/no-go
cues, and recovery actions. The reference-match report is the passive
bridge from text/audio/library influence evidence into arc selection:
it rejects blank/no-evidence references, ranks curated arcs, preserves
audio/library source paths for traceability, explains the matched terms
and style-axis scores, and can embed the selected cue sheet when saved-kit
paths are present. When saved-kit snapshots are supplied, the same report
can feed a passive live command deck: the transition timeline is reduced
to a current cue, lookahead cues, command cards, launch/hold/recovery
actions, machine handoff checks, and replayable passive commands. The
live state packet then normalizes that command deck into a GUI-ready
current screen state with now/next cues, Rytm/A4 machine panels, action
bar rows, warning stack rows, recovery stack rows, and replay commands
for a future live-show screen.
It also exposes a reference-selected snapshot preview with readiness,
mock/deferred totals, kit names, planned Rytm pads, planned Analog Four
tracks, and passive operator action. The same saved-kit path also emits a
stage packet: compact cue cards with the selected arc, scope, readiness,
mock/deferred totals, planned pads/tracks, operator moves, listening targets,
recovery actions, and risk labels for each segment. The live set cockpit
consumes that rehearsal state and turns it into a single show dashboard with
launch controls, machine panels, cue cockpit cards, recovery controls,
next-best-action text, optional capped event previews, and deterministic JSON
for future GUI/live-performance routing.
The live show export report consumes the cockpit and adds the final passive
show handoff shape: a deterministic export id, machine handoff manifest, cue
launch script, recovery script, replayable passive commands, and JSON for the
future GUI/live-performance surface. Despite the export name it writes no
files, opens no ports, and sends no MIDI.
The live transition timeline report consumes that export and arranges each cue
into operator-facing prep windows, transition cards, launch/hold/recovery
prompts, machine handoff summaries, passive replay commands, and optional
capped event previews. It is the rehearsal timeline shape for the future GUI;
it writes no files, opens no ports, and sends no MIDI.
The live command deck and live state packet are the current UI handoff
surfaces: the deck answers "what should I do right now?", and the state
packet answers "what should a screen render right now?" without opening
ports or sending MIDI.
The live analyzer handoff and target reports are the current audio-analyzer
handoff surfaces: the handoff answers "what reference evidence and GUI state
should the analyzer see?", and the target packet answers "what bands,
checkpoints, calibration steps, and warning thresholds should a rehearsal
capture compare against?" without opening ports or sending MIDI.
The live GUI/audio-analyzer readiness bundle consumes that target packet and
adds the panel manifest, stream wiring, operator workflow, blocked active
actions, replay commands, and deterministic JSON that a future desktop screen
or analyzer handoff can render without opening ports or sending MIDI.
The live GUI rehearsal session packet consumes that readiness bundle and adds
session task cards, listen-only rehearsal take cards, operator checklists,
blocked active actions, replay commands, and deterministic JSON so a future
desktop screen can guide repeated cue captures without touching hardware.
The live GUI/audio analyzer capture queue consumes that session and adds
deterministic capture slots, suggested filenames, analyzer job cards, operator
capture checklists, blocked active actions, replay commands, and JSON so a
future desktop screen can queue listen-only rehearsal takes without recording
audio, opening ports, or sending MIDI. The GUI implementation bridge then
turns the test-harness readiness packet into view-model packets, disabled
component mounts, fixture bundles, and implementation gates for the future
desktop GUI while staying metadata-only.
The stage-routing report turns the runbook into the show-day handoff:
cue-by-cue route cards with saved-kit slots, payload fingerprints,
planned Rytm pads, planned Analog Four tracks, Rytm mock row counts,
A4 deferred/candidate rows, blocker summaries, and the live rescue
sequence. It is still a passive report; it opens no ports and sends no
MIDI.
The stage-rehearsal-state report is the next passive handoff: it consumes
those route cards and produces go/rehearse/do-not-arm cue states, aggregate
Rytm and Analog Four machine states, rehearsal steps, operator prompts,
capped event previews, and recovery cues. It is meant for show-day or studio
soundcheck: green cues can be practiced as ready, rehearse cues stay in
soundcheck until deferred/candidate rows are resolved, and blocked cues are
explicitly kept out of armed use.
Together they are the current handoff shape for the future
GUI/audio-analyzer planner: the analyzer can choose or bias a reference
arc later, and these reports already show which segment-level machine
rows and operator actions would be available without opening ports or
sending MIDI.

## See also

- `GUARDRAILS_DESIGN_SPEC.md` - the full four-layer design.
- `rytm_randomizer/guardrails/schema.py` - the typed Guardrail Profile
  contract (the seam between WS-V and WS-W).
- `.claude/skills/MusicLibraryGuardrails/SKILL.md` - the Layer 2
  interpretation skill (the tight version; reads
  `reference.md` on demand at analysis time).
- `.claude/skills/DataAnalysisGuardrails/SKILL.md` - the sibling
  interpretation skill for parameter / capture-data input.
- `tests/test_style_analysis.py` - schema, immutability, hashing,
  lazy-import discipline, librosa-gated synthetic-signal tests.
