# Analog Four Audio Patch Genome Run Report

> Status: in-flight
>
> Closeout corrections, mechanical gates, and strict production typing are
> verified. Gates 3, 14, and 16 still require explicit CODEOWNER acceptance.
> Push, fresh online CI, and the fresh reviewer verdict are pending.

## Outcome

The run produced one bundled, non-stacked PR containing a passive audio-to-A4
candidate pipeline whose canonical/default invocation deterministically
publishes exactly four candidates, complete patch-DNA sidecars, CC/NRPN
live-dial plans, and hardware-safe saved-kit files limited to the proven
Filter2 Resonance field. Native audio work is isolated in a child process; the
parent owns and cleans private staging. Verified stored plans can reach real
hardware only through confirmed `python -m rytm_randomizer.app --arm`.

## Timeline

| Date | Milestone |
|---|---|
| 2026-07-03 | Audio-to-patch genome plan and deterministic inference work began. |
| 2026-07-16 | A4 saved-kit packing, codec, renderer, guarded export, and exact binary fixtures completed. |
| 2026-07-16 | Hardware accepted reference value 127, novel value 64, and four-track values 16/48/80/112. |
| 2026-07-16 | Real audio batch path, immutable generation publication, interruption recovery, observability, and CLI contracts completed. |
| 2026-07-16 | Parallel architecture, safety, test, and documentation reviews were resolved before final gates. |
| 2026-07-17 | The required post-push eight-dimension review opened a final correction set covering compatibility, boundary validation, staging truthfulness, capability resolution, proof strength, maintainability, and docs. |
| 2026-07-17 | Earlier post-push correction convergence produced a provisional merge-ready verdict. |
| 2026-07-18 | Earlier feature-code CI passed, but its counts and SHA are historical and are not reused as final closeout evidence. |
| 2026-07-27 | Fresh review reopened closeout for native crash containment, transport abstraction reuse, observability, maintainability, state-schema validity, and stale docs. |
| 2026-07-27 | Corrections passed the focused A4/operator suite (1,577 passed / 1 skipped), architecture (702 passed), full suite (6,773 passed / 3 skipped), 685 parity checks, 100% touched-file statement/branch coverage, lint, strict production typing, Vulture, and mechanical review. |

## Escalations Resolved

- A short generation identifier omitted output naming and render inputs. It was replaced with a 128-bit identity over audio, source kit, inference, genome, sidecar, send-plan, renderer, and filename inputs.
- Candidate overwrite could expose mixed-generation output. Candidate files are now immutable, exact bytes may be reused after interruption, and the stable manifest commits last.
- A catchable process interruption could leave an owned publication lock or temporary file. Acquisition and atomic-write cleanup now run in `finally` paths, and a per-acquisition nonce prevents same-process publishers from releasing each other's locks. Hard termination can still retain recovery artifacts.
- Saved-kit and batch services classified similar failures differently. A shared bounded A4 export contract now propagates one code to metrics and CLI output.
- A recomputed sidecar could previously carry internally consistent but redirected transport metadata. The reader now cross-checks every event against its DNA row and the canonical A4 CC/NRPN map.
- Batch orchestration mixed schemas, locking, JSON hashing, and acoustic scoring. Contracts, canonical codec, publication, and pure scoring now have separate modules while the public API remains compatible.
- Dry-run messages previously inflated real-send telemetry. Mock and hardware send counters now remain distinct.
- Post-push review found class-level compatibility, permissive integer boundaries, fabricated staging write state, cached capability resolution, under-constrained native-audio proof, circular pacing proof, sparse diagnostic logging, and stale operator docs. Each issue now has a focused regression test or corrected artifact.
- Native Windows decoder failure could terminate the calling process before
  private staging cleanup. Native work now runs in a spawned child. The parent
  converts abnormal exit into `inference_failed`, survives, and removes its
  audio/SysEx staging. This proves containment and cleanup, not reliable Windows
  decoding.
- The reader, sender, and app had overlapping provider/event-kind contracts.
  They now share the neutral real-output provider protocol and canonical MIDI
  event-kind vocabulary while preserving `app --arm` as the only real port
  boundary.
- Publication and ranking telemetry was incomplete, and some guarded-send
  failures could finish a trace as success. Inference, batch, publication/lock,
  ranking, and armed-send terminal outcomes now have bounded operations,
  metrics, and failure records.
- Large orchestration functions and an invalid run-state vocabulary weakened
  closeout evidence. Batch stages were split into focused helpers, app
  complexity was reduced, and the run-state JSON now has a schema-validation
  test.
- Final review found a cooperative lock release race, incomplete real-port
  cleanup contracts, interrupt reporting gaps, and missing terminal telemetry.
  Acquire/release now share an atomic sibling operation gate; real input/output
  ports require `close`; CLI interrupts return code 130; and saved-kit, reader,
  inference, ranking, and armed-send failures carry stable terminal records.

## Lessons

- Treat generated artifacts as a content-addressed publication set, not unrelated files.
- Keep hardware validation separate from inference confidence: complete DNA may be useful while SysEx write coverage remains deliberately narrow.
- Batch orchestration should call the pure renderer, so one batch records one export operation rather than nested per-candidate operations.
- Real differential audio tests are necessary; deterministic mocks alone cannot prove the upload changes the patch.
- Native-library success and process safety are different claims. Windows can
  safely return `inference_failed` while decoder reliability remains pending.
- Local saved-kit SysEx writing is not MIDI SysEx transfer. The passive writer
  writes verified bytes to disk; only an operator transfers that file.

## Fresh Verification

- Focused A4/operator regression suite: **1,577 passed, 1 skipped**.
- Architecture: **702 passed**.
- Full suite: **6,773 passed, 3 skipped**.
- Ruff, Black, isort: **clean**.
- Touched-file statement/branch coverage: **100%** across **7,573 statements**
  and **1,762 branches**, zero misses.
- V1.34 parity: **685 passed** byte-for-byte.
- Vulture, strict Pyright across all 60 touched production modules,
  `git diff --check`, and mechanical review: **passed**.
- Literal strict Pyright across all 109 touched Python paths reports **4,204
  dynamic test-harness typing errors** and remains an explicit Gate 3 reviewer
  exception.
- The pushed SHA, fresh online CI, and reviewer verdict remain pending and will
  be recorded on PR #214 after publication.

The final `git diff --stat` remains the authoritative merge total. No V1.34
parity fixture or hardware-pinned dependency is documented as changed by this
closeout.
