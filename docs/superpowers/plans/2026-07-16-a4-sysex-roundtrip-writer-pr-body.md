# Summary

Turn the first hardware-validated Analog Four MKII saved-kit calibration into a guarded writer and connect it to real audio-dependent, four-candidate batch generation. The complete DNA remains available in sidecars while saved-kit SysEx stays honestly limited to Filter2 Resonance.

## What changed

- Added `pack_elektron_7bit` beside the shared unpacker and pinned the bidirectional wire format with exact tests.
- Added canonical A4 saved-kit layout facts under `data/` and one shared codec used by both snapshot decoding and saved-kit rendering.
- Added a pure A4 renderer that validates framing, family, object type, packed/unpacked lengths, checksum, and trailer; preserves neighboring bits; and rebuilds the complete frame.
- Added a guarded exporter that permits only `hardware-write-validated` fields, refuses silent overwrite, classifies failures, records structured logs/metrics, and uses the hardened canonical atomic writer.
- Added `analog-four-saved-kit-export`, a passive operator command supporting repeated `track:value` assignments and text or JSON acknowledgements. It writes a `.syx` file and never opens a MIDI port.
- Added exact source/expected binary fixtures, hardware evidence, operator documentation, architecture diagrams, and an updated reusable Elektron SysEx skill.
- Hardened atomic publication for short writes, zero-progress writes, overwrite races, Windows FAT/exFAT removable media, and POSIX cleanup failures.
- Added deterministic measured-audio A4 inference and a manifest-backed batch service that writes up to four candidate `.syx` files plus complete DNA/CC-NRPN sidecars.
- Added `analog-four-audio-patch-batch` with bounded track/candidate options, text/JSON artifact summaries, classified failures, and no MIDI behavior.

## Why this matters

The Analog Four can now receive exact generated saved-kit parameter values without depending on Synplant output or manual front-panel entry. The scope remains deliberately narrow: Filter2 Resonance is proven on all four tracks; every other captured parameter remains candidate-only and is blocked from operator-facing export.

Audio changes candidate DNA using measured local features; this is real
audio-dependent inference, not a trained-model or Synthplant-equivalent accuracy
claim. Each sidecar carries the complete DNA and CC/NRPN plan. Each `.syx`
currently applies only hardware-write-validated Filter2 Resonance.

Example:

```bash
python -m rytm_randomizer.cli analog-four-saved-kit-export \
  --source A4_Test1_T1_Filter2Res_000_Kit.syx \
  --output A4_Test1_FourTrack_Filter2Res_Kit.syx \
  --filter2-resonance 1:16 \
  --filter2-resonance 2:48 \
  --filter2-resonance 3:80 \
  --filter2-resonance 4:112 \
  --json
```

## Test plan

```bash
python -m pytest
python -m pytest tests/cockpit/test_analog_four_patch_batch_cli.py tests/test_cli.py -n 0
python -m pytest tests/architecture/ -q
python -m pytest tests/test_engines_pad*.py tests/test_group_runner.py tests/test_scene_runner.py
python scripts/code_review_gate.py --mode cli
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
python -m vulture --min-confidence 80 <feature paths>
python -m pyright --project .pyright-a4-temp.json <feature-owned production paths>
git diff --check
```

- [x] Full repository suite: 6,254 passed, 3 skipped.
- [x] Architecture suite: 676 passed.
- [x] V1.34 frozen parity: 685 passed byte-for-byte.
- [x] Focused feature suite: 217 passed with 100% statement and branch coverage across 11 changed feature modules.
- [x] CLI integration module: 298 passed.
- [x] Strict Pyright on 10 feature-owned production modules: 0 errors, 0 warnings.
- [x] Lint trio and `git diff --check` clean.
- [x] Vulture at confidence 80 clean on feature paths.
- [x] Mechanical code-review gate passed.
- [x] Audio patch-batch CLI focused tests and command-help fixture passed locally.
- [ ] CI matrix pending PR execution.

Hardware validation:

- [x] Generated T1 Filter2 Resonance `127` matched the hardware reference byte-for-byte and displayed `127`.
- [x] Generated novel T1 value `64` displayed `64`.
- [x] One generated kit displayed T1/T2/T3/T4 values `16`/`48`/`80`/`112` correctly.
- [x] All four tracks independently received the requested resonance values on the Analog Four MKII.

## Plan-requirements conformance

Per [`docs/PLAN_REQUIREMENTS.md`](../../PLAN_REQUIREMENTS.md), every non-trivial PR must satisfy all 18 gates.

- [x] **Gate 1** - 100% statement and branch coverage across the 11 changed feature modules.
- [x] **Gate 2** - V1.34 parity byte-identical across all 685 items.
- [x] **Gate 3** - ruff, black, and isort clean; strict Pyright clean on all 10 feature-owned production modules. Legacy central aggregators remain outside project-wide strict mode and passed the full and architecture suites.
- [x] **Gate 4** - no new dead code at vulture confidence 80.
- [x] **Gate 5** - runbook, status, architecture, diagrams, plan, dated evidence, README, and audio-batch operator help updated.
- [x] **Gate 6** - frozen typed DTOs, `Final` constants, and no `Any` escape hatches.
- [x] **Gate 7** - export success/failure logs and metrics added; no MIDI hot path introduced.
- [x] **Gate 8** - exact binary, malformed-frame, mutation, CLI, atomic-write, and integration tests added.
- [x] **Gate 9** - work is contained under existing `data/`, `style_analysis/`, `devices/strategies/`, and `cockpit/export/` ownership boundaries.
- [x] **Gate 10** - the operator command uses the canonical CLI registry and adds no ad hoc mode dispatch.
- [x] **Gate 11** - exact binary fixtures and shared fixture builders live under `tests/fixtures/` and `tests/conftest.py`.
- [x] **Gate 12** - all new module constants use `Final`.
- [x] **Gate 13** - no environment variables added.
- [x] **Gate 14** - codec, renderer, exporter, atomic writer, and CLI remain bounded single-responsibility units.
- [x] **Gate 15** - the existing Elektron SysEx skill now records the learned bidirectional codec and hardware-promotion workflow.
- [x] **Gate 16** - one direct PR against `modularize-v1.34`; no stacked base branch.
- [x] **Gate 17** - decoder and writer share one codec/layout surface and export reuses the canonical atomic writer, metrics, and CLI registry.
- [x] **Gate 18** - architecture and diagram documentation describe the final shared path and platform-specific atomic publication.

## Strict rules

- [x] **No hardware in tests** - no test opens a real MIDI port or mutates a connected device.
- [x] **Lazy MIDI imports** - `mido` and `python-rtmidi` remain confined to approved lazy boundaries.
- [x] **Hardware-pinned packages** - `mido==1.3.3` and `python-rtmidi==1.5.8` were not changed.
- [x] **Passive default** - `python -m rytm_randomizer.cli` does not open a real port.
- [x] **No stacked PRs** - this PR targets `modularize-v1.34` directly.
- [x] **No bypasses** - hooks were not bypassed.

## Plan document

Plan doc: `docs/superpowers/plans/2026-07-03-analog-four-audio-patch-genome.md`

## Reviewer notes

The pure renderer can exercise candidate calibrations in tests, but the operator-facing exporter rejects every field not marked `hardware-write-validated`. Filter1 Frequency, Filter1 Resonance, and Filter2 Frequency remain intentionally blocked. Batch sidecars preserve those complete DNA/live-dial rows without claiming they were encoded into SysEx.

The atomic writer fsyncs file data. It does not fsync parent-directory metadata, so persistence of the final filename after sudden power loss remains filesystem-dependent.
