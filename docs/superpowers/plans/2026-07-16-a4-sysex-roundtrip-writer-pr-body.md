# Summary

Turn the first hardware-validated Analog Four MKII saved-kit calibration into a guarded writer and connect it to real audio-dependent, four-candidate batch generation. The complete DNA remains available in sidecars while saved-kit SysEx stays honestly limited to Filter2 Resonance.

Closeout status: fresh focused, architecture, full-suite, touched-file
coverage, parity, lint, typing, dead-code, mechanical-review, and branch
publication state are recorded below. Fresh online CI and the fresh reviewer
verdict remain pending and are not inferred from an earlier tree.

## What changed

- Added `pack_elektron_7bit` beside the shared unpacker and pinned the bidirectional wire format with exact tests.
- Added canonical A4 saved-kit layout facts under `data/` and one shared codec used by both snapshot decoding and saved-kit rendering.
- Added a pure A4 renderer that validates framing, family, object type, packed/unpacked lengths, checksum, and trailer; preserves neighboring bits; and rebuilds the complete frame.
- Added a guarded exporter that permits only `hardware-write-validated` fields, refuses silent overwrite, classifies failures, records structured logs/metrics, and uses the hardened canonical atomic writer.
- Added `analog-four-saved-kit-export`, a passive operator command supporting repeated `track:value` assignments and text or JSON acknowledgements. It writes a `.syx` file and never opens a MIDI port.
- Added exact source/expected binary fixtures, hardware evidence, operator documentation, architecture diagrams, and an updated reusable Elektron SysEx skill.
- Hardened atomic publication for short writes, zero-progress writes, overwrite races, Windows FAT/exFAT removable media, and POSIX cleanup failures.
- Added deterministic measured-audio A4 inference and a manifest-backed batch service whose documented/default invocation writes exactly four candidate `.syx` files plus complete DNA/CC-NRPN sidecars.
- Added `analog-four-audio-patch-batch` with bounded track/candidate options, text/JSON artifact summaries, classified failures, and no MIDI behavior.
- Unified report and synthesis measurements behind one typed audio decode, with direct inference RED metrics and immutable provenance.
- Moved all 28 audio-to-parameter inference formulas into a canonical immutable data-layer model consumed by one generic evaluator.
- Made candidate publication interruption-safe: both inputs are snapshotted, every artifact is staged and closed before publication, candidate names carry a 128-bit identity covering every sidecar/SysEx input, a metadata-rich per-track lock serializes publishers, and the stable manifest switches last.
- Made generation artifacts write-once with exact-byte reuse, collision rejection, catchable process-interruption lock cleanup, explicit `publication_locked` classification, and committed-result lock-cleanup warnings with recovery metadata.
- Compiled the guarded closest-reference live-dial path into 27 sendable rows:
  22 CC plus 5 NRPN events (37 MIDI messages). Six enum rows disproved by the
  2026-07-29 physical rehearsal and six paired-MSB/LSB CC rows remain manual;
  unknown labels still fail closed.
- Added hash-verified `--batch-manifest --batch-manifest-sha256 "<reviewed digest>" --candidate N` loading so dry-run and confirmed armed sends use the exact reviewed manifest, committed sidecar, nested DNA, and send plan the operator auditioned.
- Revalidate every stored send event against current A4 transport policy before
  provider construction, so an older internally valid 33/53 manifest cannot
  replay an enum ordinal disproved by the physical rehearsal.
- Extended passive A4 capture to reconstruct three-message NRPN observations with independent selector state on all four tracks.
- Added `analog-four-audio-patch-rank`, a passive local feedback command that verifies the original batch source and ranks recorded A4 candidates across 11 weighted envelope/timbre features.
- Routed saved-kit rendering through an optional capability on the registered `AnalogFourDevice`; guarded export and batching no longer import a concrete writer strategy.
- Split canonical batch JSON/hashing, stable payload/result contracts, immutable publication locks, and pure acoustic scoring from transaction orchestration.
- Hardened the manifest reader against fully rehashed malicious bundles by cross-checking every DNA/event field, transport status, path containment, and canonical A4 CC/NRPN address before output can open.
- Bound armed delivery to the operator-supplied SHA-256 of the reviewed manifest so replacing the stable manifest cannot silently change the selected hardware plan.
- Separated mock dry-run telemetry from real hardware-send counters and added structured manifest, rank, and capture outcome metrics.
- Hardened the armed live-plan boundary with complete pre-port validation, 20 ms per-message pacing, post-delivery metrics, exact partial-NRPN progress, and clean-Kit/project reload recovery.
- Label successful partial-plan output as `transport_delivered`, retain
  sendable/manual counts plus the bounded live-dial status, and explicitly mark
  hardware semantic verification as required.
- Added a hash-verified manifest-to-fake-port integration proof for the exact ordered 37-message candidate, plus tamper-before-port and interrupted-send recovery coverage.
- Added bounded aliases and construction-time validation for all canonical audio-inference feature/parameter keys, preventing misspelled DNA formulas from loading.
- Added operation-level inference, batch, publication/lock, ranking, and armed-send RED summaries with typed error codes, taxonomy fingerprints, structured context, and Ctrl+C exit-130 recovery.
- Named the 20 ms hardware pacing policy and split armed port acquisition, delivery, accounting, recovery, and close behavior into focused helpers.
- Preserved class-level device metadata while keeping strategy capabilities read-only, and reject booleans/non-integral selectors before inference or batch reads.
- Kept saved-kit staging render-only until immutable publication returns real write results, and resolve the registered A4 renderer once per batch operation.
- Isolated native audio decoding in a spawned child. An abnormal exit becomes a controlled `inference_failed` result; the parent survives and removes its private audio/SysEx staging. Windows decoder reliability is not claimed.
- Reused the neutral real-output provider protocol and canonical MIDI event-kind vocabulary across app, reader, and sender while keeping provider construction behind `app --arm`.
- Split high-complexity batch/app control flow into focused staging, publication, port, delivery, and recovery helpers; added schema enforcement for the run-state file.

## Why this matters

The Analog Four can now receive exact generated saved-kit parameter values without depending on Synplant output or manual front-panel entry. The scope remains deliberately narrow: Filter2 Resonance is proven on all four tracks; every other captured parameter remains candidate-only and is blocked from operator-facing export.

Audio changes candidate DNA using measured local features; this is real
audio-dependent inference, not a trained-model or Synthplant-equivalent accuracy
claim. Each sidecar carries the complete DNA and CC/NRPN plan, and every
currently sendable row has verified 7-bit or NRPN transport semantics. Six
disproved enum rows and six paired-CC rows remain explicit manual work. Each
`.syx` still applies only hardware-write-validated Filter2 Resonance.

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
python scripts/typecheck_touched.py
git diff --check
```

- [x] Repair-focused A4/operator regression suite: 461 passed.
- [x] Exact corrected-tree full repository suite: 6,838 passed, 3 skipped.
- [x] Architecture suite: 705 passed.
- [x] Touched-file statement/branch coverage: 100% across 7,911 statements and 1,898 branches, zero misses.
- [x] Fresh final-tree V1.34 parity: 685 passed byte-for-byte.
- [x] Vulture confidence 80, the pinned reproducible `just typecheck` strict-production gate across all 63 touched production modules, and the mechanical review gate passed.
- [x] CODEOWNER decision: dynamic test-harness typing remains accepted as scoped cleanup debt for PR #214; production typing is not waived.
- [x] Manifest reader rejects rehashed path escapes, transport drift, DNA/event drift, noncanonical CC/NRPN addresses, current-policy drift, sequence drift, and coverage drift before output opens.
- [x] Lint trio and `git diff --check` clean.
- [x] Audio patch-batch CLI focused tests and command-help fixture passed locally.
- [x] Native decoder abnormal-exit path is process-contained and parent-owned private staging is removed.
- [x] Audio genome, learning, send-plan, and batch surfaces retain deterministic source/parameter identity when native analysis succeeds.
- [x] Corrected batch generation matched twice: fixture generation `562b0248a0159abef78932dc643c870e`, manifest SHA-256 `348ea6dc2619cfa6f908af7450fd0a862d6fb360f2f334a5a5205eb7a57e57b7`, and 37-message transport SHA-256 `6998c9d7cc9d8d69dfd7d2e039512bc29ef82f2bba776cf9d35a2857122b3619`.
- [x] This follow-up tree carries fresh local evidence; publication and online state are tracked on PR #214.
- [ ] Fresh online CI and fresh reviewer verdict: pending.

Hardware validation:

- [x] Saved-kit Filter2 Resonance evidence is limited to the committed sanitized reference, novel, and four-track fixture records.
- [x] The 2026-07-29 hash-verified single-track rehearsal completed 33-row /
  53-message delivery, exposed six incorrect enum values, and ended with a
  confirmed clean-kit reload without saving.
- [ ] Four-track live-plan routing remains unverified.
- [ ] The corrected 27-row/37-message physical rehearsal remains a pre-merge
  requirement; 12 rows remain manual.

## Plan-requirements conformance

Per [`docs/PLAN_REQUIREMENTS.md`](https://github.com/buzzijose-hub/RytmRandomizer/blob/modularize-v1.34/docs/PLAN_REQUIREMENTS.md), every non-trivial PR must satisfy all 18 gates.

- [x] **Gate 1** — touched production files have 100% statement/branch coverage (7,911 statements / 1,898 branches).
- [x] **Gate 2** — 685 V1.34 parity items passed byte-for-byte.
- [x] **Gate 3** — Ruff, Black, and isort pass. Pinned strict Pyright 1.1.407 passes reproducibly across all 63 touched production modules via `just typecheck`. The CODEOWNER accepts dynamic test-harness typing as scoped cleanup debt for PR #214; production typing is not waived.
- [x] **Gate 4** — Vulture confidence 80 passed across production and tests.
- [x] **Gate 5** — docs updated (`README.md`, `CONTRIBUTING.md`, `docs/STATUS.md`, relevant `docs/` reflect the change).
- [x] **Gate 6** — type-system hygiene (Protocol over ABC, `Final` constants, no bare `Any`).
- [x] **Gate 7** — inference, batch, publication/lock, ranking, and armed-send hot paths use bounded metrics/tracing.
- [x] **Gate 8** — tests are intent-named, mirror their source structure, and reuse shared factories/fixtures from `tests/conftest.py`.
- [x] **Gate 9** — module-organization hygiene (subpackages over flat top-level).
- [x] **Gate 10** — string-literal dispatch hygiene (consume `data/modes.py` constants; allowlist drained).
- [x] **Gate 11** — shared fixtures (canonical definitions in `tests/conftest.py`).
- [x] **Gate 12** — `Final` constants on module-level constants.
- [x] **Gate 13** — env var docs (every read env var documented in `docs/LOCAL_DEV_TOOLING_NOTES.md` or a relevant doc).
- [x] **Gate 14** — CODEOWNER-accepted timing exception: the ten-dimension baseline was reconstructed after implementation began, so it is useful review evidence but not a contemporaneous pre-implementation audit.
- [x] **Gate 15** — learning capture (extract `.claude/skills/learned/` + `.claude/rules/` where applicable).
- [x] **Gate 16** — CODEOWNER-accepted historical evidence exception: PR #214 is one non-stacked branch directly against `modularize-v1.34`, but a distinct worktree/branch assignment was not retained for every listed workstream.
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

The pure renderer can exercise candidate calibrations in tests, but the
operator-facing exporter rejects every field not marked
`hardware-write-validated`. Filter1 Frequency, Filter1 Resonance, and Filter2
Frequency remain intentionally blocked from saved-kit writing. Batch sidecars
preserve the complete live-dial DNA without claiming those rows were encoded
into SysEx. The guarded vocabulary routes 27 rows / 37 messages; six physically
disproved enum rows, six paired-CC rows, and unknown destination labels fail
closed into manual work. Armed delivery requires a committed hash-verified
manifest; direct description/audio inference is dry-run-only. The corrected
guarded transport plan must complete a fresh supervised physical rehearsal
before merge.

The atomic writer fsyncs file data. It does not fsync parent-directory metadata, so persistence of the final filename after sudden power loss remains filesystem-dependent. Under normal filesystem semantics, generation-addressed write-once candidates ensure the prior manifest never points at mixed bytes during a process-interrupted overwrite; the interruption may leave unreferenced generation files. A lock-cleanup failure does not relabel a committed batch as failed: the successful result carries a warning and the retained metadata path.

The CODEOWNER accepts the Gate 3 dynamic test-harness typing debt, Gate 14
timing exception, and Gate 16 historical-ledger exception for this PR. The
RAM-only live-dial path is exempt from automatic pre-send SysEx backup because
it sends no persistent save/write command; a disposable project and saved clean
baseline remain mandatory. The failed 2026-07-29 rehearsal records A4 OS 1.55,
Elektron Transfer 1.9.5, and Overbridge 2.25.7; the reduced-plan replay must
record its own result before merge.

Consolidated review: [`docs/superpowers/plans/2026-07-17-a4-audio-patch-final-review.md`](https://github.com/buzzijose-hub/RytmRandomizer/blob/codex/a4-sysex-roundtrip-writer/docs/superpowers/plans/2026-07-17-a4-audio-patch-final-review.md)
