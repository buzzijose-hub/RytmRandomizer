# Summary

Turn the first hardware-validated Analog Four SysEx calibration into a guarded saved-kit writer. This PR adds the shared Elektron 7-bit packer, a pure A4 frame validator/mutator/renderer, a local-file exporter that reuses the canonical atomic writer, and immutable evidence for the reference, novel-value, and four-track studio passes.

## What changed

- Added `pack_elektron_7bit` beside the shared unpacker and pinned its exact wire format.
- Added a pure A4 saved-kit renderer that validates framing, family, object, body size, checksum, and packed length; preserves neighboring high bits; and rebuilds the complete frame after one or four track mutations.
- Added a guarded `.syx` exporter that refuses silent overwrite and permits only hardware-write-validated fields. It never opens a MIDI port.
- Promoted Filter2 Resonance to `hardware-write-validated` with immutable file names, hashes, expected track values, and operator confirmation.
- Recorded the 2026-07-16 hardware results and updated the runbook, status, architecture, diagrams, and patch-genome plan.

## Why this matters

The Analog Four can now receive exact generated saved-kit parameter values without depending on Synplant output or manual front-panel entry. The scope remains deliberately narrow: Filter2 Resonance is proven; all other captured fields remain candidate-only and blocked from operator-facing export.

## Test plan

```bash
python -m pytest
python -m pytest tests/architecture/ -q
python -m pytest tests/test_snapshot_envelope.py tests/test_devices_strategies_analog_four_saved_kit_writer.py tests/cockpit/test_analog_four_kit_export.py tests/test_analog_four_sysex_calibration.py -n 0 --cov=rytm_randomizer.snapshot.envelope --cov=rytm_randomizer.devices.strategies.analog_four_saved_kit_writer --cov=rytm_randomizer.cockpit.export.analog_four_kit --cov=rytm_randomizer.data.analog_four_sysex_calibration --cov-branch --cov-report=term-missing
python scripts/code_review_gate.py --mode cli
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
python -m vulture rytm_randomizer/devices/strategies/analog_four_saved_kit_writer.py rytm_randomizer/cockpit/export/analog_four_kit.py rytm_randomizer/data/analog_four_sysex_calibration.py rytm_randomizer/snapshot/envelope.py --min-confidence 80
```

- [x] Local pytest passes: 6,209 passed, 3 skipped.
- [x] `tests/architecture/` passes: 671 passed.
- [x] Lint trio (ruff + black + isort) clean.
- [x] Touched core modules have 100% branch coverage.
- [x] 685/685 V1.34 parity items byte-identical.
- [x] No new dead code at vulture confidence 80.
- [ ] CI matrix pending PR execution.

Hardware validation:

- [x] Generated T1 Filter2 Resonance `127` matched the hardware reference byte-for-byte and displayed `127`.
- [x] Generated novel T1 value `64` displayed `64`.
- [x] One generated kit displayed T1/T2/T3/T4 values `16`/`48`/`80`/`112` correctly.

## Plan-requirements conformance

Per [`docs/PLAN_REQUIREMENTS.md`](../../PLAN_REQUIREMENTS.md) — every non-trivial PR must satisfy all 18 gates.

- [x] **Gate 1** — 100% branch coverage on touched files; project pure-branch requirement preserved.
- [x] **Gate 2** — V1.34 parity byte-identical (685/685 pytest items).
- [x] **Gate 3** — lint clean (ruff + black `--target-version=py311` + isort `--profile black`).
- [x] **Gate 4** — no new dead code (vulture --min-confidence 80).
- [x] **Gate 5** — runbook, status, architecture, diagrams, plan, and dated hardware evidence updated.
- [x] **Gate 6** — frozen typed DTOs, `Final` constants, and no bare `Any`.
- [x] **Gate 7** — no new MIDI hot path; local file I/O reuses the existing classified canonical atomic writer.
- [x] **Gate 8** — focused behavior tests, malformed-frame tests, and shared fixture coverage added.
- [x] **Gate 9** — new modules live under existing `devices/strategies/` and `cockpit/export/` subpackages.
- [x] **Gate 10** — no string-literal dispatch surface added.
- [x] **Gate 11** — the observed saved-kit frame builder is shared through `tests/conftest.py`.
- [x] **Gate 12** — all new module constants use `Final`.
- [x] **Gate 13** — no environment variables added.
- [x] **Gate 14** — renderer and export adapter are bounded, single-responsibility modules.
- [x] **Gate 15** — the existing shared-envelope and device-strategy guidance covered the reusable learning; no duplicate skill added.
- [x] **Gate 16** — one direct PR against `modularize-v1.34`; no stacked base branch.
- [x] **Gate 17** — reuses `snapshot.envelope`, calibration data, and the single canonical `atomic_write` surface.
- [x] **Gate 18** — `docs/ARCHITECTURE.md` and `docs/ARCHITECTURE_DIAGRAMS.md` updated for the new path.

## Strict rules — non-negotiables

Per [`CONTRIBUTING.md` § Strict rules](../../../CONTRIBUTING.md#strict-rules--non-negotiables):

- [x] **No hardware in tests** — no test opens a real MIDI port; no test mutates a connected device.
- [x] **Lazy MIDI imports** — `mido` and `python-rtmidi` remain confined to the approved lazy boundaries.
- [x] **Hardware-pinned packages** — `mido==1.3.3` and `python-rtmidi==1.5.8` were not bumped.
- [x] **Passive default** — `python -m rytm_randomizer.cli` does not open a real port.
- [x] **No stacked PRs** — this PR targets `modularize-v1.34` directly.
- [x] **No `--no-verify`** — hooks were not bypassed.

## Plan document

Plan doc: `docs/superpowers/plans/2026-07-03-analog-four-audio-patch-genome.md`

## Reviewer notes

The pure renderer permits candidate calibration exercise in tests, but the operator-facing export adapter rejects every field not marked `hardware-write-validated`. Filter1 Frequency, Filter1 Resonance, and Filter2 Frequency are intentionally still blocked.
