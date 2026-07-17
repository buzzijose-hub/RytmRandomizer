# Analog Four Audio Patch Genome Run Report

> Status: in-flight

## Outcome

The run produced one bundled, non-stacked PR containing a passive audio-to-A4 candidate pipeline, complete patch-DNA sidecars, CC/NRPN live-dial plans, and hardware-safe saved-kit files limited to the proven Filter2 Resonance field.

## Timeline

| Date | Milestone |
|---|---|
| 2026-07-03 | Audio-to-patch genome plan and deterministic inference work began. |
| 2026-07-16 | A4 saved-kit packing, codec, renderer, guarded export, and exact binary fixtures completed. |
| 2026-07-16 | Hardware accepted reference value 127, novel value 64, and four-track values 16/48/80/112. |
| 2026-07-16 | Real audio batch path, immutable generation publication, interruption recovery, observability, and CLI contracts completed. |
| 2026-07-16 | Parallel architecture, safety, test, and documentation reviews were resolved before final gates. |
| 2026-07-17 | The required post-push eight-dimension review found and resolved device-boundary, trust, observability, abstraction, coverage, maintainability, and docs issues. |
| 2026-07-17 | Final local convergence passed: 6,472 tests, 690 architecture items, 685 byte-frozen parity items, 98.97% project coverage, focused 100% branch coverage, lint, Vulture, and Pyright. |

## Escalations Resolved

- A short generation identifier omitted output naming and render inputs. It was replaced with a 128-bit identity over audio, source kit, inference, genome, sidecar, send-plan, renderer, and filename inputs.
- Candidate overwrite could expose mixed-generation output. Candidate files are now immutable, exact bytes may be reused after interruption, and the stable manifest commits last.
- A catchable process interruption could leave an owned publication lock or temporary file. Acquisition and atomic-write cleanup now run in `finally` paths, and a per-acquisition nonce prevents same-process publishers from releasing each other's locks. Hard termination can still retain recovery artifacts.
- Saved-kit and batch services classified similar failures differently. A shared bounded A4 export contract now propagates one code to metrics and CLI output.
- A recomputed sidecar could previously carry internally consistent but redirected transport metadata. The reader now cross-checks every event against its DNA row and the canonical A4 CC/NRPN map.
- Batch orchestration mixed schemas, locking, JSON hashing, and acoustic scoring. Contracts, canonical codec, publication, and pure scoring now have separate modules while the public API remains compatible.
- Dry-run messages previously inflated real-send telemetry. Mock and hardware send counters now remain distinct.

## Lessons

- Treat generated artifacts as a content-addressed publication set, not unrelated files.
- Keep hardware validation separate from inference confidence: complete DNA may be useful while SysEx write coverage remains deliberately narrow.
- Batch orchestration should call the pure renderer, so one batch records one export operation rather than nested per-candidate operations.
- Real differential audio tests are necessary; deterministic mocks alone cannot prove the upload changes the patch.

## LOC Impact

The bundled PR spans the A4 data, style-analysis, strategy, export, test, and documentation surfaces. Local closeout passed 6,472 tests with 3 platform/dependency skips and 98.97% project coverage. The final `git diff --stat` and CI matrix remain the authoritative merge totals; no V1.34 parity fixture or hardware-pinned dependency changed.
