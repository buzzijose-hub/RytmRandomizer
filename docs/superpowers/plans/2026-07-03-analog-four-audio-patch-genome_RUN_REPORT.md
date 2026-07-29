# Analog Four Audio Patch Genome Run Report

> Status: in-flight
>
> Closeout corrections, mechanical gates, and strict production typing are
> verified, and the Gate 3/14/16 policy decisions are accepted. Follow-up
> publication and online state are tracked on PR #214; fresh approval and the
> supervised physical rehearsal remain pending.

## Outcome

The run produced one bundled, non-stacked PR containing a passive audio-to-A4
candidate pipeline whose canonical/default invocation deterministically
publishes exactly four candidates, complete patch-DNA sidecars, CC/NRPN
live-dial plans, and hardware-safe saved-kit files limited to the proven
Filter2 Resonance field. Native audio work is isolated in a child process; the
parent owns and cleans private staging. Verified stored plans can reach real
hardware only through confirmed `python -m rytm_randomizer.app --arm`, and
every stored event is revalidated against current transport policy first.

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
| 2026-07-28 | CODEOWNER review repair passed the focused A4/operator suite (1,581 passed / 1 skipped), architecture (702 passed), full suite (6,777 passed / 3 skipped), 685 parity checks, and 100% touched-production coverage across 7,506 statements / 1,764 branches. |
| 2026-07-28 | Follow-up repair passed the focused A4/operator suite (1,589 passed / 1 skipped), architecture (703 passed), full suite (6,792 passed / 3 skipped), 685 parity checks, and 100% touched-production coverage across 7,557 statements / 1,788 branches. |
| 2026-07-29 | Final post-push repair passed the focused touched-file A4/operator suite (1,689 passed / 1 skipped), architecture (704 passed), full suite (6,804 passed / 3 skipped), 685 parity checks, and 100% touched-production coverage across 7,887 statements / 1,878 branches. |
| 2026-07-29 | Exact-head review repair passed the focused touched-file A4/operator suite (1,717 passed / 1 skipped), architecture (705 passed), 685 parity checks, strict Pyright across 63 production modules, and 100% touched-production coverage across 7,952 statements / 1,884 branches. The last uninterrupted production-equivalent full suite passed 6,811 tests / 3 skipped; the exact tree collects 6,824 tests and online CI is authoritative for its full-suite result. |
| 2026-07-29 | The supervised former 33-row / 53-message plan completed transport but disproved six enum ordinals; the initialized kit was reloaded without saving and those rows were demoted, leaving 27 rows / 37 messages. |
| 2026-07-29 | Post-rehearsal review added current-policy validation for stored manifests, explicit partial-transport telemetry, raw enum-label regression pins, and synchronized learning/recovery artifacts. The exact tree passed 461 repair-focused tests, 6,838 full-suite tests / 3 skipped, and 100% coverage across 7,911 statements / 1,898 branches. |

## Escalations Resolved

- A short generation identifier omitted output naming and render inputs. It was replaced with a 128-bit identity over audio, source kit, inference, genome, sidecar, send-plan, renderer, and filename inputs.
- Candidate overwrite could expose mixed-generation output. Candidate files are now immutable, exact bytes may be reused after interruption, and the stable manifest commits last.
- A catchable process interruption could leave an owned publication lock or temporary file. Acquisition and atomic-write cleanup now run in `finally` paths, and a per-acquisition nonce prevents same-process publishers from releasing each other's locks. Hard termination can still retain recovery artifacts.
- Saved-kit and batch services classified similar failures differently. A shared bounded A4 export contract now propagates one code to metrics and CLI output.
- A recomputed sidecar could previously carry internally consistent but redirected transport metadata. The reader now cross-checks every event against its DNA row and the canonical A4 CC/NRPN map.
- An older internally valid sidecar could still carry enum values disproved by
  a later rehearsal. The reader now also recompiles each stored value against
  current A4 transport policy before provider construction.
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
- Partial live-dial delivery could be logged as undifferentiated success.
  Completion telemetry now says `transport_delivered`, preserves sendable and
  manual counts plus the bounded live-dial status, and marks hardware semantic
  verification as required.
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

- Repair-focused A4/operator regression suite: **461 passed**.
- Architecture: **705 passed**.
- Exact corrected-tree full-suite run: **6,838 passed, 3 skipped**.
- Ruff, Black, isort: **clean**.
- Touched-file statement/branch coverage: **100%** across **7,911 statements**
  and **1,898 branches**, zero misses.
- V1.34 parity: **685 passed** byte-for-byte.
- Vulture, strict Pyright across all 63 touched production modules,
  `git diff --check`, and mechanical review: **passed**.
- Dynamic test-harness typing remains covered by the accepted scoped Gate 3
  decision; production typing is not waived.
- Follow-up publication, fresh online CI, and reviewer status are tracked on
  PR #214.

The final `git diff --stat` remains the authoritative merge total. No V1.34
parity fixture or hardware-pinned dependency is documented as changed by this
closeout.
