# CLI reference

This is the full passive `rytm_randomizer.cli` surface for RytmRandomizer. Every CLI command here is **passive by construction** — it opens no MIDI port and sends no MIDI. Companion `rytm_randomizer.app` invocations are labeled separately when a passive report has a dry-run or armed operator bridge. The project-wide passive-safety sweep in [`tests/test_real_midi_passive_cli_safety.py`](../tests/test_real_midi_passive_cli_safety.py) auto-discovers CLI commands from the lazy registry and runs every one in a subprocess to assert no `mido` / `rtmidi` / adapter modules load and no armed-output tokens leak.

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

## Analog Rytm — scoped randomization + kit morphing (preview)

The competitive-parity mask+intensity and morph surfaces, guardrailed as
**passive previews**. Each renders a deterministic plan (no RNG) the operator
can audit and then arm-and-send through the `senders` ArmedApply seam; neither
command reaches a transmit path.

| Command | Purpose |
| --- | --- |
| `scoped-randomization-preview [--json]` | Deterministic **ScopeMask + depth macro** preview: choose which of the 12 pads and which parameter groups (`src`/`filter`/`amp`/…) move, anchored on the current kit, from a single depth macro (0..1). Renders the per-parameter delta plan. |
| `kit-morph-preview [--json]` | Deterministic **kit morph** preview: interpolate a source kit toward a target — linear on continuous params, threshold on discrete selectors — at a morph amount (0..1). Renders the per-parameter interpolation plan. |

```bash
python -m rytm_randomizer.cli scoped-randomization-preview
python -m rytm_randomizer.cli scoped-randomization-preview --json
python -m rytm_randomizer.cli kit-morph-preview
python -m rytm_randomizer.cli kit-morph-preview --json
```

The interactive versions (a per-track/per-group mask grid + depth slider, and a
morph-amount slider strip) live in the cockpit's schema-driven panels; the CLI
surface renders the canonical demonstration plan.

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

## Long-form reference-audio atlas

`reference-audio-atlas-report` scans a long audio file with bounded,
sequential windows, deterministically selects acoustically distinct moments,
and generates an Analog Four patch genome plus a Rytm/Analog Four style
blueprint for each selected moment.

```bash
python -m rytm_randomizer.cli reference-audio-atlas-report \
  --audio long-mix.wav \
  --window-seconds 30 \
  --hop-seconds 30 \
  --max-windows 240 \
  --moments 8 \
  --min-novelty 0.08 \
  --track 1 \
  --candidates 4 \
  --json
```

Windows must be 5–120 seconds; the hard ceilings are 240 decoded windows and
eight selected moments. The command is passive and output-only. It does not
separate stems, identify artists or equipment, claim forensic reconstruction,
produce hardware-verified settings, open a MIDI port, or send MIDI/SysEx.

---

## Analog Four — style routing + mutation planning

| Command | Description |
|---|---|
| `analog-four-style-snapshot-routing-report` | Passive **Analog Four style snapshot routing** balanced/wild-discovery routing |
| `analog-four-style-mutation-intent-report` | Passive Analog Four track/zone mutation intent |
| `analog-four-style-mutation-mock-preview-report` | Passive Analog Four mock CC rows (deferred while saved-kit offsets are promoted) |
| `analog-four-kit-catalog-report` | Passive Analog Four decoded kit catalog |
| `analog-four-baseline-report` | Passive initialized A4 SysEx baseline comparison across kit, pattern+kit, and whole-project exports |
| `analog-four-patch-genome-report` | Passive four-candidate Analog Four single-sound patch DNA from audio or text |
| `analog-four-patch-learning-report` | Passive Analog Four patch learning routes, capture matrix, and live-dial readiness |
| `analog-four-patch-corpus-report` | Passive nearest-match ranking against starter or captured Analog Four patch/audio examples |
| `analog-four-patch-send-plan-report` | Passive CC/NRPN live-dial send plan for a generated Analog Four patch |
| `analog-four-saved-kit-export` | Guarded local-file saved-kit export; currently admits hardware-validated Filter2 Resonance only |
| `al16-rytm-kit-export` | Offline AL16 Analog Rytm audit/evidence compiler; Phase R1 validates the exact initialized reference, writes deterministic mapping-gap evidence, and emits no `.syx` |
| `rio145-inspect-sysex` | Strict offline inspection of one native Elektron SysEx object |
| `rio145-diff-sysex` | Offline wire and native-payload comparison of two Elektron SysEx objects |
| `rio145-validate-roundtrip` | Byte-identical decode/encode validation for one native Elektron SysEx object |
| `rio145-build-kit` | Deterministic offline Analog Four or Analog Rytm KIT recipe build selected by `--device`, with explicit slot and output |
| `rio145-validate-return` | Offline device-selected target-return validation against the deterministic recipe build |
| `rio145-export-oxi-manifest` | Validate and export the RIO145 OXI sequence-evidence bundle offline |
| `al16-rytm-mapping-evidence` | Passive AL16 Rytm mapping-closure analyzer; cryptographically binds initialized/configured saved-kit evidence to the exact recipe, R1 gap manifest, recipe identity, and reference SHA without promoting offsets or writing SysEx |
| `audio-patch-dna` | Passive one-analysis workspace with readable sound DNA, exactly eight fixed directions, and optional selected-candidate Analog Four SysEx export |
| `audio-patch-studio-session` | Passive resumable session that binds one DNA selection, selected A4 export, recorded render, and bounded accept/refine result behind SHA-verified state |
| `analog-four-audio-patch-batch` | Real local audio analysis; the documented/default workflow deterministically commits exactly four immutable `.syx` candidates, complete DNA sidecars, and one manifest; `--studio-handoff` prints the bounded four-audition workflow with zero calibration rounds |
| `analog-four-audio-patch-rank` | Passive acoustic ranking of recorded A4 candidates against the exact batch reference |
| `analog-four-audio-patch-refine` | Passive bounded feedback pass for one recorded A4 candidate; accepts a close render or emits exactly one corrected target and optional offline SysEx artifact |
| `local-model-copilot-report` | Passive local model docs, mutation-intent, and Analog Four patch-review packets; optional local model subprocess call with `--ask-local-model` |
| `analog-four-oxi-macro-report` | Passive in-memory Analog Four OXI-style four-track macro preview |
| `analog-four-oxi-macro-readiness-report` | Passive Analog Four OXI macro readiness, soft-capture preflight, and operator-present validation commands |
| `analog-four-style-kit-readiness-report` | Passive per-kit Analog Four style-readiness sweep |

```bash
python -m rytm_randomizer.cli analog-four-style-snapshot-routing-report KITS.syx industrial_dark --slot 0 --discovery 50
python -m rytm_randomizer.cli analog-four-style-mutation-intent-report KITS.syx birmingham_pressure --slot 0 --discovery 45
python -m rytm_randomizer.cli analog-four-style-mutation-mock-preview-report KITS.syx jose_core_techno --slot 0 --discovery 45 --events --limit 24
python -m rytm_randomizer.cli analog-four-kit-catalog-report KITS.syx --limit 16
python -m rytm_randomizer.cli analog-four-baseline-report --kit A4_Test1_Init_Kit.syx --pattern-kit A4_Test1_Init_A01_PatternKit.syx --whole-project A4_Test1_Init_WholeProject.syx --json
python -m rytm_randomizer.cli analog-four-patch-genome-report --description "hypnotic metallic HP2 stab" --track 1 --candidate 1
python -m rytm_randomizer.cli analog-four-patch-genome-report --audio reference.wav --track 2 --json
python -m rytm_randomizer.cli analog-four-patch-learning-report --description "hypnotic metallic HP2 stab" --track 1 --candidate 1
python -m rytm_randomizer.cli analog-four-patch-learning-report --audio reference.wav --track 2 --json
python -m rytm_randomizer.cli analog-four-patch-corpus-report --description "hypnotic metallic HP2 stab" --track 1 --limit 4
python -m rytm_randomizer.cli analog-four-patch-corpus-report --audio reference.wav --corpus-file a4-captures.json --json
python -m rytm_randomizer.cli analog-four-patch-send-plan-report --description "hypnotic metallic HP2 stab" --track 1 --candidate 1
python -m rytm_randomizer.cli analog-four-saved-kit-export --source INIT.syx --output PATCH.syx --filter2-resonance 1:64
python -m rytm_randomizer.cli al16-rytm-kit-export --reference output/local/reference/RYTM_Test1_Init_Kit.syx --recipe specs/al16/AL02_LOCK_RYTM.yaml --destination-slot 127 --output output/local/al16/AL02_LOCK_RYTM.syx
python -m rytm_randomizer.cli rio145-inspect-sysex --input A4_NATIVE.syx
python -m rytm_randomizer.cli rio145-diff-sysex --left A4_GENERATED.syx --right A4_TARGET_RETURN.syx
python -m rytm_randomizer.cli rio145-validate-roundtrip --input RYTM_NATIVE.syx
python -m rytm_randomizer.cli rio145-build-kit --device analog_four_mk2 --reference A4_NATIVE.syx --recipe specs/rio145/come_to_rio_a4_core.json --destination-slot 0 --output output/local/rio145/RIO_A4_CORE.syx
python -m rytm_randomizer.cli rio145-build-kit --device analog_rytm_mk2 --reference RYTM_NATIVE.syx --recipe specs/rio145/come_to_rio_rytm_core.json --destination-slot 0 --output output/local/rio145/RIO_RYTM_CORE.syx
python -m rytm_randomizer.cli rio145-validate-return --device analog_four_mk2 --reference A4_NATIVE.syx --recipe specs/rio145/come_to_rio_a4_core.json --returned A4_TARGET_RETURN.syx
python -m rytm_randomizer.cli rio145-validate-return --device analog_rytm_mk2 --reference RYTM_NATIVE.syx --recipe specs/rio145/come_to_rio_rytm_core.json --returned RYTM_TARGET_RETURN.syx
python -m rytm_randomizer.cli rio145-export-oxi-manifest --manifest RIO145_OXI_PROGRAM_MANIFEST.json --events RIO145_OXI_EVENTS.csv --output output/local/rio145/RIO145_OXI_EVIDENCE.json
python -m rytm_randomizer.cli al16-rytm-mapping-evidence --reference output/local/reference/RYTM_Test1_Init_Kit.syx --configured output/local/al16/AL02_LOCK_RYTM_CONFIGURED.syx --recipe specs/al16/AL02_LOCK_RYTM.yaml --gap-manifest output/al16/AL02_LOCK_RYTM_manifest.json --expected-gap-manifest-sha256 "<reviewed SHA-256>" --report output/local/al16/AL02_LOCK_RYTM_mapping_evidence.json
python -m rytm_randomizer.cli audio-patch-dna --audio reference.wav --output-dir output/local/audio-dna
python -m rytm_randomizer.cli audio-patch-dna --audio reference.wav --output-dir output/local/audio-dna --select 6 --source-kit INIT.syx
python -m rytm_randomizer.cli audio-patch-studio-session --reference reference.wav --source-kit INIT.syx --select 6 --output-dir output/local/audio-session
python -m rytm_randomizer.cli audio-patch-studio-session --session output/local/audio-session/studio-session.json --reference reference.wav --source-kit INIT.syx --render selected-a4-render.wav
python -m rytm_randomizer.cli analog-four-audio-patch-batch --audio reference.wav --source-kit INIT.syx --output-dir batch --track 1 --candidates 4
python -m rytm_randomizer.cli analog-four-audio-patch-batch --audio reference.wav --source-kit INIT.syx --output-dir batch --track 1 --studio-handoff --a4-output-port "<exact configured Analog Four output name>"
python -m rytm_randomizer.cli analog-four-audio-patch-rank --reference reference.wav --manifest batch/a4-t1-audio-patch-batch.json --render 1=candidate-1.wav
python -m rytm_randomizer.cli analog-four-audio-patch-refine --reference reference.wav --manifest batch/a4-t1-audio-patch-batch.json --candidate 1 --render candidate-1.wav --output-dir output/local/a4-refinement
python -m rytm_randomizer.cli local-model-copilot-report --question "Which A4 rows are staged only?" --workflow all --description "hypnotic metallic HP2 stab" --json
python -m rytm_randomizer.cli analog-four-oxi-macro-report hard-groove --seed 23 --intensity 6 --events --limit 0
python -m rytm_randomizer.cli analog-four-oxi-macro-readiness-report hard-groove --seed 0 --intensity 4 --limit 4
python -m rytm_randomizer.cli analog-four-style-kit-readiness-report KITS.syx jose_core_techno --limit 16
```

Active companion app bridge for the selected patch send plan:

```bash
python -m rytm_randomizer.app --dry-run --a4-patch-send-plan --batch-manifest batch/a4-t1-audio-patch-batch.json --batch-manifest-sha256 "<reviewed manifest SHA-256>" --candidate 1
python -m rytm_randomizer.app --arm --a4-patch-send-plan --batch-manifest batch/a4-t1-audio-patch-batch.json --batch-manifest-sha256 "<reviewed manifest SHA-256>" --candidate 1 --confirm-a4-patch-send-plan --a4-output-port "<exact configured Analog Four output name>"
python -m rytm_randomizer.app --dry-run --a4-patch-send-plan --description "hypnotic metallic HP2 stab" --track 1 --candidate 1
```

The manifest form is the only armed audition-to-hardware path: it requires the
operator-supplied SHA-256 of the exact reviewed manifest, then verifies the
committed batch, selected sidecar, source-audio identity, candidate DNA, and
CC/NRPN plan before any output port opens. The direct `--description` and
`--audio` forms are dry-run-only one-off inference paths; they rebuild a plan
and are not bound to a previously published or auditioned batch artifact.
Armed delivery does not prompt from enumerated ports: `--a4-output-port` must
match exactly one discovered output name or the command fails before opening it.

`analog-four-baseline-report` is the passive clean-slate intake for A4 patch
capture work. It reads three local SysEx export scopes - kit, pattern+kit, and
whole-project - decodes supported saved-kit frames, compares their first kit
payload fingerprints, and reports whether the initialized baseline is coherent
enough for future changed-patch diffs. It does not open MIDI ports, send MIDI,
write SysEx, or claim parameter-level DNA extraction while the A4 saved-kit
offsets remain candidate-only.

`analog-four-patch-genome-report` is the passive patch-DNA bridge for manual
studio tests. It takes one description or audio file, builds four candidate
columns for a selected A4 track, and prints the selected candidate with A4
front-panel values plus CC/NRPN metadata. Bipolar screen values such as
Filter Overdrive and LFO depths are shown as `-64..+63` targets; CC-ready rows
also show the raw `0..127` value; NRPN-only destination labels remain
screen-only until their exact ordinals are captured for live dial-in.

`analog-four-patch-learning-report` is the passive intelligence/learning layer
above the genome. It ranks the four candidate columns, maps measured traits
such as metallic pressure and tempo drive to the selected A4 controls, prints a
future capture matrix for real A4 recordings, and separates CC/NRPN-ready rows
from screen-only NRPN destinations before any live dial-in work is promoted.

`analog-four-patch-corpus-report` is the first passive corpus-learning surface.
It ranks a description or audio reference against A4 patch/audio examples,
using clearly labeled synthetic starter rows when no corpus file is supplied
and operator-recorded hardware examples when `--corpus-file` is provided. It
does not train a model, open ports, send MIDI, or write SysEx; it tells us
which real captures are still missing before that matching can become
hardware-backed.

`analog-four-patch-send-plan-report` is the passive rehearsal surface for that
promotion. It compiles the selected candidate into ordered CC/NRPN live-dial
events, counts the exact transport messages, and lists skipped front-panel rows
such as destination labels that still need ordinal capture. The matching active
path lives in `rytm_randomizer.app`: use `--dry-run --a4-patch-send-plan` to
render the plan through the mock sender, or `--arm --a4-patch-send-plan
--batch-manifest ... --batch-manifest-sha256 "<reviewed digest>" --candidate N
--confirm-a4-patch-send-plan
--a4-output-port "<exact configured Analog Four output name>"` to require one
exact output match and send only the compiler-approved rows from the exact
hash-verified plan stored with that batch.

`analog-four-saved-kit-export` is the narrow hardware-validated file writer.
It reads a saved-kit dump, applies explicit `TRACK:VALUE` Filter2 Resonance
assignments through the registered Analog Four device capability, and writes a
new `.syx` through the canonical atomic writer. It never opens a MIDI port and
refuses unsupported or unvalidated saved-kit parameters.

`audio-patch-dna` is the passive reference-to-discovery workspace. It decodes
one immutable audio snapshot once, reports pitch, envelope, transients,
rhythm, brightness, noise, spectral movement, and tonal stability, then builds
exactly eight deterministic directions in this order: Closest, Darker,
Brighter, Metallic, Percussive, Atmospheric, Deeper, and Animated. The default
run writes JSON and readable Markdown for comparison only. A selected export
requires `--select 1..8` and `--source-kit` together, then routes only that
candidate through the existing validated Analog Four batch/SysEx exporter
without analyzing the audio again. The command imports no MIDI backend,
enumerates no ports, sends no data, and performs no network access. Analog Rytm
selection/export is not included in this command yet; it follows the separate
Rytm codec integration rather than duplicating that architecture here.

`audio-patch-studio-session` is the resumable operator layer over
`audio-patch-dna` and `analog-four-audio-patch-refine`. Start mode requires
`--reference`, `--source-kit`, `--select 1..8`, and `--output-dir`; it commits
the DNA workspace and selected one-candidate A4 export before publishing
`studio-session.json` and `studio-session.md`. Resume mode requires
`--session`, the same reference and source kit, and one `--render`; it verifies
all recorded hashes before invoking exactly one accept/refine pass. The
session records both the DNA direction number and the selected batch's local
manifest candidate number, so those identities cannot be confused. Completed
requests are idempotent, a different render cannot replace a terminal result,
and failures leave the prior state intact. This command performs file I/O
only and never imports a MIDI backend, enumerates ports, opens hardware, or
transmits MIDI/SysEx.

`al16-rytm-kit-export` is the offline Analog Rytm audit/evidence compiler for
the original AL16 Reference -> Discovery performance bank. It is not a
forensic recreation workflow. Store the private initialized reference under
the gitignored `output/local/reference/` subtree so following this operator
workflow cannot create an unallowlisted repo-root directory or stage the dump.
Phase R1 requires `output/local/reference/RYTM_Test1_Init_Kit.syx` with SHA-256
`8bda94d6d5031e038c8d810789301f35242ed539338a0399548869a34e1dc4dd`, and the
destination slot is always explicit. The compiler round-trips that initialized
reference, validates permanent pad roles, machine-specific fields, typed
converters, tuning evidence, and a strict known-byte allowlist. It opens no
MIDI backend or port. The current `AL02 LOCK` proof is deliberately
fail-closed: 18 critical writer mappings remain unverified, so the command
returns `2`, writes manifest/validation/byte-diff evidence, emits no `.syx`,
and authorizes no manual hardware import. Positive kit generation remains
future work after those writer mappings are verified.

The six `rio145-*` commands are passive, file-only tooling for the preserved
RIO145 native-object evidence. The shared parser validates Elektron framing,
MIDI-safe data bytes, native MSB packing, encoded length, and checksum before
exposing a payload. A build compiles the strict device recipe twice, requires
byte-identical output, reparses and reserializes the result, verifies the
known-field allowlist, requires an explicit `0..127` destination slot, and
refuses an existing output unless `--overwrite` is supplied. Target-return
validation requires exact native-payload identity and exact whole-wire identity
after normalizing only the returned destination slot. The OXI export validates
the preserved four-variant, 360-event, 191-bar sequence evidence; it does not
author Elektron patterns. None of these commands imports or constructs a MIDI
provider, enumerates ports, or sends data. Binary target-return validation is
not a claim of sonic equivalence; listening refinement remains pending.

`al16-rytm-mapping-evidence` is the passive Phase R2 mapping-closure analyzer.
It compares the initialized saved-kit dump with one manually configured
AL02-like dump, limits candidate locations to the existing Rytm layout
metadata and canonical parameter resolver, and writes a deterministic JSON
review packet covering the R1 mapping gaps. Before comparing payloads it
verifies SHA-256 provenance for the exact recipe and gap-manifest files, the
operator-supplied expected SHA-256 for those exact manifest bytes, the
deterministic recipe identifier, and the initialized-reference SHA recorded in
the manifest. Path roles are validated against the canonical AL16 gap grammar
before file I/O; failures use bounded error codes and safe basenames, and
success/failure metrics are recorded under the mapping-evidence operation. A
second scratch-slot import/dump supplies the bounded destination-slot proof
described in the linked plan. The command never opens or enumerates MIDI ports,
writes SysEx, or promotes a candidate mapping; the ambiguous Pad 9 machine
request remains explicitly unresolved until device evidence identifies the
intended machine. One configured saved-KIT capture is intended to close many
gaps together; repeated single-parameter calibration rounds are not the
operator workflow.

`analog-four-audio-patch-batch` is the end-to-end offline candidate generator.
With the documented/default `--candidates 4` workflow, it analyzes an immutable
reference-audio snapshot and deterministically builds exactly four
audio-dependent A4 candidates. It renders the currently validated SysEx subset
and commits each candidate's complete DNA plus CC/NRPN plan behind a
hash-addressed sidecar and one stable manifest. The bounded `--candidates`
compatibility option can request a leading subset for focused tests, but the
operator workflow and product contract use all four candidates.
Local sidecars and manifests retain the reference-audio and source-kit
basenames for operator traceability. Use neutral filenames before generation
and review those local artifacts before sharing them outside the studio.

`--studio-handoff` turns the successful four-candidate batch into one finite
operator packet. It requires exactly four candidates and an exact
`--a4-output-port` string, then emits `calibration_rounds_required: 0`, four
full-path dry-run commands, four guarded `app --arm` audition commands, four
deterministic recording destinations, and the final acoustic-ranking command.
The option remains passive: the port name is copied into the prepared armed
commands but is not enumerated, opened, or contacted by the batch process.
The only required human comparison is the four-candidate audition; the retired
Rush16 calibration sweep is not part of this workflow.

The command performs local file I/O only and does not transfer a kit or send
MIDI. Native audio decoding runs in a spawned child process. An abnormal native
exit becomes a classified `inference_failed` result in the parent, which owns
and removes the private audio/SysEx staging directory. This prevents a decoder
crash from taking down the CLI or retaining private staging, but it is not a
claim that the native decoder is reliable on Windows.

`analog-four-audio-patch-rank` closes the passive studio feedback loop. It
verifies every candidate sidecar and the original reference hash before
comparing recorded A4 renders across 11 normalized synthesis measurements.
The result is an explainable ranking packet; it is not promoted into training
data automatically.

`analog-four-audio-patch-refine` performs one bounded correction after that
ranking step. It verifies the exact reference hash, manifest, and selected
candidate before analyzing one recorded A4 render. A similarity score at or
above `--accept-similarity` (default `92`) produces an `accept` decision with
no new candidate. A lower score applies `reference + gain * (reference -
render)` to the 11 normalized acoustic features, clamps each feature to its
valid domain, preserves the reference duration, and infers exactly one
follow-up candidate. The default `--gain` is `0.65`. Supplying
`--source-kit` routes that one candidate through the existing passive A4
saved-kit exporter; omitting it writes only JSON/Markdown analysis artifacts.
This is not iterative training or a forensic-recreation claim. The command
never imports a MIDI backend, enumerates ports, opens hardware, or transmits
MIDI/SysEx.

`local-model-copilot-report` is the passive local-AI bridge. By default it
does not run a model; it prints deterministic source packets and JSON schemas
for docs/MIDI answers, staged natural-language mutation intent, and Analog Four
patch co-design review. Add `--ask-local-model` only after `LOCAL_MODEL_COMMAND`
points to a local model executable. The command is run as a subprocess, JSON
stdout is validated, and the output remains staged-only: no ports open, no MIDI
is sent, and no hardware-send plan is promoted. The local model cannot invoke
the real MIDI provider; only `python -m rytm_randomizer.app --arm` can cross the
hardware boundary.

`analog-four-oxi-macro-report` is a snapshot-free planning surface for the
Analog Four side of an OXI-style live rig. It uses existing manual-backed A4 CC
metadata to preview deterministic values across four tracks, but it does not
open a port, render real MIDI, or send anything. Use it to audition macro
shapes such as `home`, `hard-groove`, `dub-pressure`, and
`industrial-transition` before promoting any future A4 path into a gated
hardware plan.

`analog-four-oxi-macro-readiness-report` is the next passive promotion gate. It
reuses the same deterministic macro rows, marks manual-backed CC rows as
`cc-ready`, and prints an input-only soft-capture preflight command, explicit
operator-present validation commands, stop/recovery notes, and promotion gates.
It does not arm hardware, open ports, send MIDI, or implement full A4 macro
SEND.

`analog-four-oxi-macro-set-planner-report` is the passive queue layer for those
macro rows. It sequences the default `warehouse-arc` current/up-next plan
(`home`, `hard-groove`, `dub-pressure`, `industrial-transition`, `home`) for
Cockpit review, emits its own passive JSON replay command, and keeps `A4 full
macro SEND` plus unattended playback blocked.

---

## OXI live macro strategy

| Command | Description |
|---|---|
| `oxi-live-macro-catalog-report` | Passive Rytm macro cards, recovery actions, live flow, and A4 runway state |
| `controller-brain-mapping-report [--json]` | Passive 16-encoder controller-brain intent pages for Rytm, A4, crates, queue, snapshots, and journal |
| `controller-brain-rehearsal-report [--json]` | Passive controller-template export rows plus virtual gesture outcomes for future controller software |
| `controller-brain-live-runbook-report [--json]` | Passive controller-brain live runbook that composes controller gestures, OXI chapters, and Cockpit readiness into stage/inspect/fire/recover metadata |
| `controller-brain-live-state-report [--json]` | Passive controller-brain live state rows, queued intents, audit events, readiness gates, and blocked bridge actions |
| `controller-brain-live-bridge-readiness-report [--json]` | Passive controller-brain bridge contract packets, readiness gates, and blocked runtime actions |
| `controller-brain-live-dispatch-rehearsal-report [--json]` | Passive controller-brain shadow dispatch decisions, dispatch groups, and blocked transport gates |
| `controller-brain-live-feedback-rehearsal-report [--json]` | Passive controller-brain feedback frames, feedback zones, and blocked output gates |
| `controller-brain-live-cockpit-handoff-report [--json]` | Passive controller-brain Cockpit handoff cards, panels, disabled controls, and replay commands |
| `controller-brain-live-implementation-bridge-report [--json]` | Passive controller-brain GUI implementation bindings, fixture bundles, and implementation gates |
| `controller-brain-operator-package-report [--json]` | Passive controller gestures to Live Kit Operator Package slot/readiness ledger |
| `rytm-live-macro-hardware-rehearsal-report` | Passive next-studio Rytm macro checklist with launch command, pad-lane checks, and recovery notes |
| `oxi-live-set-strategy-report` | Passive OXI-style set chapters, operator cues, rehearsal/replay commands, all-12-pad policy, and A4 review-only actions |

```bash
python -m rytm_randomizer.cli oxi-live-macro-catalog-report
python -m rytm_randomizer.cli controller-brain-mapping-report
python -m rytm_randomizer.cli controller-brain-mapping-report --json
python -m rytm_randomizer.cli controller-brain-rehearsal-report
python -m rytm_randomizer.cli controller-brain-rehearsal-report --json
python -m rytm_randomizer.cli controller-brain-live-runbook-report
python -m rytm_randomizer.cli controller-brain-live-runbook-report --json
python -m rytm_randomizer.cli controller-brain-live-state-report
python -m rytm_randomizer.cli controller-brain-live-state-report --json
python -m rytm_randomizer.cli controller-brain-live-bridge-readiness-report
python -m rytm_randomizer.cli controller-brain-live-bridge-readiness-report --json
python -m rytm_randomizer.cli controller-brain-live-dispatch-rehearsal-report
python -m rytm_randomizer.cli controller-brain-live-dispatch-rehearsal-report --json
python -m rytm_randomizer.cli controller-brain-live-feedback-rehearsal-report
python -m rytm_randomizer.cli controller-brain-live-feedback-rehearsal-report --json
python -m rytm_randomizer.cli controller-brain-live-cockpit-handoff-report
python -m rytm_randomizer.cli controller-brain-live-cockpit-handoff-report --json
python -m rytm_randomizer.cli controller-brain-live-implementation-bridge-report
python -m rytm_randomizer.cli controller-brain-live-implementation-bridge-report --json
python -m rytm_randomizer.cli controller-brain-operator-package-report
python -m rytm_randomizer.cli controller-brain-operator-package-report --json
python -m rytm_randomizer.cli rytm-live-macro-hardware-rehearsal-report
python -m rytm_randomizer.cli rytm-live-macro-hardware-rehearsal-report --json
python -m rytm_randomizer.cli oxi-live-set-strategy-report
python -m rytm_randomizer.cli oxi-live-set-strategy-report --json
```

`rytm-live-macro-hardware-rehearsal-report` is the passive checklist for the
next operator-present Rytm hardware session. It prints the armed live snapshot
shell launch command, the `kit-core`, `hard-groove`, `industrial`,
`dub-pressure`, `transition`, and `home` macro rehearsal cards, Pad 5/9/10/11
SRC-first notes, Pad 6-8 tom/source notes, Pad 12 product-availability notes,
and the `home`/`Z` recovery checks. The report itself does not arm hardware,
open MIDI ports, send MIDI, or mutate hardware.

`oxi-live-set-strategy-report` is the passive bridge between the OXI-style
operator idea and the current macro vocabulary. It describes OXI as the source
of notes, triggers, mutes, and pattern motion; RytmRandomizer as the second
performer riding captured-kit sound design; and Analog Four as review-only
until its outbound macro path is separately validated. It also keeps Jose's
current pad discipline explicit: pads 5, 9, 10, and 11 stay SRC-first with
filter/LFO off and AMP limited to overdrive, delay, and reverb; pads 6-8 stay
tom/source-focused with light filter motion and LFO off; Pad 12 remains
available for users who rely on it. The JSON payload also includes an operator
cue sheet that maps each chapter to stage, inspect, fire, recover, expected
result, and blocked-action steps. Rehearsal checkpoints cover capture,
first-macro staging, `changes` review, manual fire, anchor recovery, A4 gate,
and after-set notes. Replay command metadata separates passive CLI reports,
passive A4 macro review, the operator-present Rytm shell launch, `changes`,
manual fire, and anchor recovery so a future GUI can render buttons without
executing them. It also includes a
hardware-validation runway for the next Rytm kit-core smoke, Dual VCO
center-band check, A4 input-only soft capture, and passive A4 macro dry-run.
Analog Four promotion criteria keep outbound macros blocked until input-label
coverage, passive macro review, an explicit arm gate, and a tested recovery
path exist.

`controller-brain-mapping-report` is the passive planning layer for OXI E16,
E16-like, or generic 16-encoder controller surfaces. It does not open a
controller input, learn raw MIDI CCs, send controller feedback, dispatch
WebSocket commands, arm hardware, or send MIDI. Instead it maps paged encoder
slots to reviewed RytmRandomizer intent: global macro depth and safety, all 12
Rytm pad lanes, Analog Four runway macro controls, Style Crates, live queue
staging, snapshot recovery, and Mutation Journal actions. That keeps the
hardware-controller idea product-shaped without bypassing the existing passive
preview and explicit-arm rules.

`controller-brain-rehearsal-report` is the passive export and rehearsal packet
for that map. It derives all 112 controller-template rows from
`controller_mapping_profiles.py`, resolves representative virtual gestures into
their reviewed intent keys, records blocked active actions, and emits a JSON
shape that a future Cockpit/controller bridge can render without opening
controller input, learning raw MIDI messages, dispatching WebSocket commands,
opening hardware ports, or sending MIDI.

`controller-brain-live-runbook-report` composes the controller rehearsal packet,
the OXI live set strategy, and the Cockpit performance console payload into a
stage, inspect, fire, and recover runbook for a future fixed-controller
surface. The report stays passive: it opens no controller input, performs no
MIDI learn or raw CC capture, dispatches no WebSocket commands, opens no MIDI
ports, sends no MIDI, and mutates no snapshots.

`controller-brain-live-state-report` derives the next bridge contract from that
runbook: deterministic `state.*` rows, `queued.*` intents, `audit.*` events,
readiness gates, blocked active actions, and replay commands. It is still
metadata only. It opens no controller input, performs no MIDI learn or raw CC
capture, dispatches no WebSocket commands, opens no MIDI ports, sends no MIDI,
and mutates no snapshots.

`controller-brain-live-bridge-readiness-report` is the passive implementation
handoff after the state report. It turns each `state.*`, `queued.*`, and
`audit.*` row into a deterministic bridge packet, marks only the state, queue,
and audit contracts ready, and keeps controller input, gesture reducer runtime,
WebSocket dispatch, controller feedback, MIDI output, hardware send, and
snapshot mutation blocked until a separate active bridge is designed and
approved.

`controller-brain-live-dispatch-rehearsal-report` is the passive dry-run after
bridge readiness. It turns bridge packets into shadow dispatch decisions,
summarizes state/queue/audit dispatch groups, and keeps controller input,
runtime reducers, WebSocket dispatch, controller feedback, MIDI output, hardware
send, and snapshot mutation blocked.

`controller-brain-live-feedback-rehearsal-report` is the passive output-side
follow-up after dispatch rehearsal. It turns shadow dispatch decisions into
metadata-only LED, encoder-ring, and display feedback frames while keeping the
controller output adapter, WebSocket feedback, MIDI output, hardware feedback,
and snapshot mutation blocked.

`controller-brain-live-cockpit-handoff-report` is the passive GUI handoff after
feedback rehearsal. It turns the metadata-only feedback frames into GUI-ready
handoff cards, Cockpit panel summaries, disabled Cockpit controls, replay
commands, and safety evidence while keeping controller input, runtime reducers,
WebSocket dispatch, controller feedback, MIDI output, hardware send, and
snapshot mutation blocked.

`controller-brain-live-implementation-bridge-report` is the passive GUI
implementation handoff after the Cockpit handoff. It turns disabled handoff
cards into deterministic implementation bindings, fixture bundles,
implementation gates, replay commands, and safety evidence for a future GUI
test harness while keeping GUI launch, renderer startup, runtime reducers,
WebSocket dispatch, controller feedback, MIDI output, hardware send, and
snapshot mutation blocked.

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
| `live-gui-performance-console-report` | **Cockpit performance console packet** with device rail, 12-pad Rytm snapshot surface, passive macro action deck, live-kit capture panel/workbench/package audition/operator package/review ledger, controller-brain panel, A4 set-plan review, Style Crates queue, snapshot history, command queue, safety checklist, and blocked hardware actions |
| `style-performance-arc-live-gui-analyzer-readiness-report` | **GUI/audio-analyzer readiness bundle** with panel manifest, stream wiring, operator workflow, **blocked active actions** |
| `style-performance-arc-live-gui-rehearsal-session-report` | **GUI rehearsal session packet** with task cards, **listen-only rehearsal take** cards, operator checklist |
| `style-performance-arc-live-gui-capture-queue-report` | **GUI/audio analyzer capture queue** with capture slots, suggested filenames, **analyzer job** cards |
| `style-performance-arc-live-gui-capture-review-report` | **GUI/audio analyzer capture review** with **go/repeat/hold** decisions, metric drift notes, hold reasons |
| `style-performance-arc-live-gui-sidecar-session-report` | **sidecar-ready GUI state** with panels, analyzer rows, capture decisions, **disabled active controls** |
| `style-performance-arc-live-gui-analyzer-overlay-report` | **GUI analyzer overlay** with **meter widgets**, threshold markers, selected capture badge, node annotations |
| `style-performance-arc-live-gui-analyzer-frame-report` | **GUI analyzer frame** with ordered **frame events**, visual assertions, blocked actions |
| `style-performance-arc-live-gui-action-reducer-report` | **GUI action reducer** with deterministic **control transition** decisions, disabled hardware locks |
| `style-performance-arc-live-gui-controller-state-report` | **GUI controller state** with deterministic **control-state** rows, queued allowed actions, blocked controls |
| `style-performance-arc-live-gui-playback-transcript-report` | **GUI playback transcript** with deterministic **playback transcript** events, GUI assertions, analyzer checkpoints |
| `style-performance-arc-live-gui-playback-validation-report` | **GUI playback validation** matrix with deterministic future test-harness cases, harness steps (**validation matrix**) |

```bash
python -m rytm_randomizer.cli live-gui-performance-console-report
python -m rytm_randomizer.cli live-gui-performance-console-report --json
```

`live-gui-performance-console-report` is the composed Cockpit packet for the
cinematic performance-console direction. It aggregates existing passive report
builders instead of duplicating facts, emits a single JSON object for a GUI
consumer, and includes a passive Live Kit Capture panel for the receive KIT
SysEx, review, mutate, `go`, recover, and `resnapshot` workflow. The paired
Live Kit Capture Workbench turns that workflow into capture slots, anchor
verification, mutation-readiness gates, recovery gates, and future
package-manifest metadata while keeping every apply/export/send control
disabled. The Live Kit Package Audition surface then exposes review-only
audition slots, queue order, package checks, disabled package/journal/send
controls, and a journal preview seed for favorite captured-kit variations. The
Live Kit Operator Package surface binds those audition slots into browser-local
set-plan staging actions, recovery requirements, journal/export preview
metadata, and local rehearsal package `auditionSource` / `operatorPackage`
evidence while keeping real package stage/send/write controls disabled. The
Operator Package Review Ledger then summarizes apply-preview, mock-apply, and
receipt-audit stages with one row per package step, package export-key evidence,
readiness proof, blocked actions, safety lines, and a disabled ledger apply
control. It keeps open-port, hardware send, Cockpit macro fire/prepare, queue dispatch,
snapshot-history SEND, live-kit receive/mutate/send, captured-kit package
apply/export/audition, controller MIDI learn/input, controller WebSocket
dispatch, and Analog Four outbound macro actions blocked.

The Operator Package Apply Preview surface stays on the same mock-safe sidecar
bridge. Its ack previews the whole package apply plan with ordered apply steps,
validated export keys, readiness checks, recovery requirements, blocked
real-send actions, safety lines, a dry-run summary, and proof that no port
opened, no MIDI was sent, and no package file was written. It is intentionally
not the real hardware apply/send path.

The Operator Package Mock Apply surface is the next mock-only acknowledgement
on that same bridge. Its `mock_apply_operator_package` ack accepts the current
package in review mode, returns deterministic mock-apply step evidence, and
keeps explicit proof that no MIDI port opened, no MIDI was sent, no package
file was written, no snapshot mutated, no send plan applied, and no event
stream emitted.

The Operator Package Receipt surface records that reviewed preview as a
passive audit packet through `build_operator_package_receipt`. The ack includes
a deterministic receipt id, short digest, ordered receipt steps, readiness
checks, recovery requirements, blocked actions, safety lines, and proof that
no MIDI port opened, no MIDI was sent, no file was written, no snapshot was
mutated, no send plan was applied, and no events were emitted. It is evidence
for a future journal/handoff path, not a package writer or hardware sender.

Run any one with `--help` for its full flag set, or check the lazy command registry in [`rytm_randomizer/cli.py`](../rytm_randomizer/cli.py) for the complete catalogue.
