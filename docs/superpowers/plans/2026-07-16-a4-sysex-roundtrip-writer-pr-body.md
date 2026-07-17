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
- Unified report and synthesis measurements behind one typed audio decode, with direct inference RED metrics and immutable provenance.
- Moved all 28 audio-to-parameter inference formulas into a canonical immutable data-layer model consumed by one generic evaluator.
- Made candidate publication interruption-safe: both inputs are snapshotted, every artifact is staged and closed before publication, candidate names carry a 128-bit identity covering every sidecar/SysEx input, a metadata-rich per-track lock serializes publishers, and the stable manifest switches last.
- Made generation artifacts write-once with exact-byte reuse, collision rejection, catchable process-interruption lock cleanup, explicit `publication_locked` classification, and committed-result lock-cleanup warnings with recovery metadata.
- Completed the current generated live-dial vocabulary: the closest-reference candidate now compiles 39/39 rows into 29 CC plus 10 NRPN events (59 MIDI messages), with sparse destination ordinals validated through Elektron Overbridge and unknown labels still failing closed.
- Added hash-verified `--batch-manifest --candidate N` loading so dry-run and confirmed armed sends use the exact committed sidecar, nested DNA, and send plan the operator auditioned.
- Extended passive A4 capture to reconstruct three-message NRPN observations with independent selector state on all four tracks.
- Added `analog-four-audio-patch-rank`, a passive local feedback command that verifies the original batch source and ranks recorded A4 candidates across 11 weighted envelope/timbre features.
- Routed saved-kit rendering through an optional capability on the registered `AnalogFourDevice`; guarded export and batching no longer import a concrete writer strategy.
- Split canonical batch JSON/hashing, stable payload/result contracts, immutable publication locks, and pure acoustic scoring from transaction orchestration.
- Hardened the manifest reader against fully rehashed malicious bundles by cross-checking every DNA/event field, transport status, path containment, and canonical A4 CC/NRPN address before output can open.
- Separated mock dry-run telemetry from real hardware-send counters and added structured manifest, rank, and capture outcome metrics.
- Hardened the armed live-plan boundary with complete pre-port validation, 20 ms per-message pacing, post-delivery metrics, exact partial-NRPN progress, and clean-Kit/project reload recovery.
- Added a hash-verified manifest-to-fake-port integration proof for the exact ordered 59-message candidate, plus tamper-before-port and interrupted-send recovery coverage.
- Added bounded aliases and construction-time validation for all canonical audio-inference feature/parameter keys, preventing misspelled DNA formulas from loading.
- Added operation-level inference, ranking, and armed-send RED summaries with typed error codes, taxonomy fingerprints, structured context, and Ctrl+C exit-130 recovery.
- Named the 20 ms hardware pacing policy and split armed port acquisition, delivery, accounting, recovery, and close behavior into focused helpers.

## Why this matters

The Analog Four can now receive exact generated saved-kit parameter values without depending on Synplant output or manual front-panel entry. The scope remains deliberately narrow: Filter2 Resonance is proven on all four tracks; every other captured parameter remains candidate-only and is blocked from operator-facing export.

Audio changes candidate DNA using measured local features; this is real
audio-dependent inference, not a trained-model or Synthplant-equivalent accuracy
claim. Each sidecar carries the complete DNA and CC/NRPN plan, and every
currently generated row is live-routable. Each `.syx` still applies only
hardware-write-validated Filter2 Resonance.

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
python -m pytest tests/cockpit/test_analog_four_patch_batch_reader.py tests/cockpit/test_analog_four_patch_render_rank.py tests/test_a4_soft_capture.py tests/test_app_validate_one_cc.py -n 0
python -m pytest tests/cockpit/test_analog_four_kit_cli.py tests/cockpit/test_analog_four_patch_batch.py tests/cockpit/test_analog_four_patch_batch_cli.py tests/cockpit/test_export_writer.py tests/test_analog_four_patch_genome.py tests/test_analog_four_patch_inference.py tests/test_analog_four_patch_learning.py tests/test_analog_four_patch_send_plan.py tests/test_devices_strategies_analog_four_saved_kit_writer.py tests/test_observability_metrics.py tests/test_style_analysis.py --cov=rytm_randomizer.cockpit.export.analog_four_export_contracts --cov=rytm_randomizer.cockpit.export.analog_four_cli --cov=rytm_randomizer.cockpit.export.analog_four_kit --cov=rytm_randomizer.cockpit.export.analog_four_patch_batch --cov=rytm_randomizer.cockpit.export.analog_four_patch_batch_cli --cov=rytm_randomizer.cockpit.export.writer --cov=rytm_randomizer.data.analog_four_patch_templates --cov=rytm_randomizer.observability.metrics --cov=rytm_randomizer.style_analysis.analog_four_patch_genome --cov=rytm_randomizer.style_analysis.analog_four_patch_inference --cov=rytm_randomizer.style_analysis.analog_four_patch_learning --cov=rytm_randomizer.style_analysis.analog_four_patch_send_plan --cov=rytm_randomizer.style_analysis.extractor --cov=rytm_randomizer.style_analysis.library --cov-branch --cov-report=term-missing -n 0 -q
python -m pytest tests/test_style_analysis.py tests/cockpit/test_analog_four_patch_batch.py tests/cockpit/test_analog_four_patch_batch_reader.py tests/cockpit/test_analog_four_patch_render_rank.py tests/test_analog_four_patch_inference.py tests/test_midi_sender_protocol.py -n 0 --cov=rytm_randomizer.cockpit.export.analog_four_patch_batch_codec --cov=rytm_randomizer.cockpit.export.analog_four_patch_batch_contracts --cov=rytm_randomizer.cockpit.export.analog_four_patch_batch_publication --cov=rytm_randomizer.cockpit.export.analog_four_patch_batch_reader --cov=rytm_randomizer.style_analysis.analog_four_patch_render_rank --cov=rytm_randomizer.style_analysis.extractor --cov-branch --cov-report=term-missing
python -m pytest --cov=rytm_randomizer --cov-branch --cov-report=term-missing
python -m pytest tests/architecture/ -q
python -m pytest tests/test_engines_pad1.py tests/test_engines_pad2.py tests/test_engines_pad3.py tests/test_engines_pad4.py tests/test_group_runner.py tests/test_scene_runner.py
python scripts/code_review_gate.py --mode cli
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
python -m vulture rytm_randomizer tests --min-confidence 80
$files = git diff --name-only origin/modularize-v1.34 -- 'rytm_randomizer/**/*.py' 'rytm_randomizer/*.py'; python -m pyright $files
git diff --check
```

- [x] Full repository suite: 6,508 passed, 3 skipped.
- [x] Architecture suite: 693 passed.
- [x] V1.34 frozen parity: 685 passed byte-for-byte.
- [x] Post-review codec/contracts/publication/reader/ranker/extractor slice: 100% statement and branch coverage (795 statements / 158 branches / 0 misses).
- [x] Complete project coverage: 99.04% across 42,450 statements and 9,622 branches; pure-branch coverage is 98.40%, and all 2,641 changed executable production lines plus every changed behavioral branch origin executed.
- [x] Existing saved-kit writer/export focused coverage remains green; the complete repository suite includes both writer and audio-batch paths.
- [x] Pyright across every production module changed by PR #214: 0 errors, 0 warnings.
- [x] Manifest reader rejects rehashed path escapes, transport drift, DNA/event drift, noncanonical CC/NRPN addresses, sequence drift, and coverage drift before output opens.
- [x] Lint trio and `git diff --check` clean.
- [x] Vulture at confidence 80 clean across `rytm_randomizer` and `tests`.
- [x] Mechanical code-review gate passed on the final tree.
- [x] Audio patch-batch CLI focused tests and command-help fixture passed locally.
- [x] Real librosa/CLI smoke: tonal and noise clips each produced 4 `.syx` files, 4 complete sidecars, and 1 manifest; their DNA and SysEx hashes differed, with candidate-1 Filter2 Resonance `36` versus `24`.
- [x] Audio genome, learning, send-plan, and batch surfaces agreed on the same source hash and inferred parameter values.
- [ ] CI matrix pending PR execution.

Hardware validation:

- [x] Generated T1 Filter2 Resonance `127` matched the hardware reference byte-for-byte and displayed `127`.
- [x] Generated novel T1 value `64` displayed `64`.
- [x] One generated kit displayed T1/T2/T3/T4 values `16`/`48`/`80`/`112` correctly.
- [x] All four tracks independently received the requested resonance values on the Analog Four MKII.
- [ ] Complete 39-row/59-message physical live-plan rehearsal remains pending in the disposable initialized project; exact software/fake-port delivery is verified.

## Plan-requirements conformance

Per [`docs/PLAN_REQUIREMENTS.md`](https://github.com/buzzijose-hub/RytmRandomizer/blob/modularize-v1.34/docs/PLAN_REQUIREMENTS.md), every non-trivial PR must satisfy all 18 gates.

- [x] **Gate 1** — 100% branch coverage on touched files; project ≥95% pure-branch.
- [x] **Gate 2** — V1.34 parity byte-identical (505 goldens / 685 pytest items).
- [x] **Gate 3** — lint clean (ruff + black `--target-version=py311` + isort `--profile black`).
- [x] **Gate 4** — no new dead code (vulture --min-confidence 80).
- [x] **Gate 5** — docs updated (`README.md`, `CONTRIBUTING.md`, `docs/STATUS.md`, relevant `docs/` reflect the change).
- [x] **Gate 6** — type-system hygiene (Protocol over ABC, `Final` constants, no bare `Any`).
- [x] **Gate 7** — observability adoption (hot paths call `get_metrics().record_*`).
- [x] **Gate 8** — test hygiene (`test_<unit>_<behavior>_when_<condition>` naming; shared fixtures in `tests/conftest.py`).
- [x] **Gate 9** — module-organization hygiene (subpackages over flat top-level).
- [x] **Gate 10** — string-literal dispatch hygiene (consume `data/modes.py` constants; allowlist drained).
- [x] **Gate 11** — shared fixtures (canonical definitions in `tests/conftest.py`).
- [x] **Gate 12** — `Final` constants on module-level constants.
- [x] **Gate 13** — env var docs (every read env var documented in `docs/LOCAL_DEV_TOOLING_NOTES.md` or a relevant doc).
- [x] **Gate 14** — maintainability review (timing tracked, complexity bounded).
- [x] **Gate 15** — learning capture (extract `.claude/skills/learned/` + `.claude/rules/` where applicable).
- [x] **Gate 16** — one comprehensive branch directly against `modularize-v1.34`; no stacked PR cascade, per the current repository anti-cascade rule.
- [x] **Gate 17** — abstraction reuse: every new module/class surveyed against the existing-abstraction catalog (`Device` Protocol, `senders/`, `snapshot/envelope`, `cli_registry`, `data/`, `observability/metrics`, ...); no reimplementation; net-new shapes justified.
- [x] **Gate 18** — architecture-doc + diagram freshness: `docs/ARCHITECTURE.md` + `docs/ARCHITECTURE_DIAGRAMS.md` updated for any architecture-surface change; quoted counts re-verified.

## Strict rules — non-negotiables

- [x] **No hardware in tests** — no test opens a real MIDI port; no test mutates a connected device.
- [x] **Lazy MIDI imports** — `mido` and `python-rtmidi` imported only inside `real_midi_adapter.py` / `mido_provider.py`.
- [x] **Hardware-pinned packages** — `mido==1.3.3` and `python-rtmidi==1.5.8` not bumped.
- [x] **Passive default** — `python -m rytm_randomizer.cli` does not open a real port.
- [x] **No stacked PRs** — this PR's base is `modularize-v1.34` (or the integration target), not another open PR's head.
- [x] **No `--no-verify`** — pre-commit hooks were not bypassed.

## Plan document

Plan doc: [`docs/superpowers/plans/2026-07-03-analog-four-audio-patch-genome.md`](https://github.com/buzzijose-hub/RytmRandomizer/blob/codex/a4-sysex-roundtrip-writer/docs/superpowers/plans/2026-07-03-analog-four-audio-patch-genome.md)

## Reviewer notes

The pure renderer can exercise candidate calibrations in tests, but the operator-facing exporter rejects every field not marked `hardware-write-validated`. Filter1 Frequency, Filter1 Resonance, and Filter2 Frequency remain intentionally blocked from saved-kit writing. Batch sidecars preserve the complete live-dial DNA without claiming those rows were encoded into SysEx. The current generated vocabulary is fully software-routable; unvalidated destination labels still fail closed. The complete 39-row/59-message live plan has not yet completed a supervised physical full-patch rehearsal and is documented as a pending hardware-validation step.

The atomic writer fsyncs file data. It does not fsync parent-directory metadata, so persistence of the final filename after sudden power loss remains filesystem-dependent. Under normal filesystem semantics, generation-addressed write-once candidates ensure the prior manifest never points at mixed bytes during a process-interrupted overwrite; the interruption may leave unreferenced generation files. A lock-cleanup failure does not relabel a committed batch as failed: the successful result carries a warning and the retained metadata path.

Gate 14 and 15 evidence is committed beside the plan: maintainability audit/report, append-only run log, run report, architecture before/after, replay playbook, state/schema, and the updated repository-scoped Elektron SysEx skill. Firmware and transfer-utility versions were not recorded during the hardware studio pass; the accepted file hashes, displayed values, and that evidence limitation are documented in `docs/hardware-validation/2026-07-16-a4-saved-kit-roundtrip-results.md`.

Consolidated review: [`docs/superpowers/plans/2026-07-17-a4-audio-patch-final-review.md`](https://github.com/buzzijose-hub/RytmRandomizer/blob/codex/a4-sysex-roundtrip-writer/docs/superpowers/plans/2026-07-17-a4-audio-patch-final-review.md)
