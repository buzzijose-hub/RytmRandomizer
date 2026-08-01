# Analog Four Audio Patch Genome Maintainability Audit

> Status: in-flight

Historical baseline date: 2026-07-03
Recorded: 2026-07-16
Scope: baseline reconstructed from the 2026-07-03 repository state after implementation had already begun, then reused for the 2026-07-27 corrective review of the audio-to-A4 genome, saved-kit writer, passive batch exporter, verified reader, and app-owned armed sender. This timing deviation is explicit; the document is not represented as a contemporaneous pre-implementation artifact.

Scores use 1 (fragile) through 5 (clear and easy to extend).

| Question | Baseline | Finding | Required response |
|---|---:|---|---|
| 1. Onboarding curve | 3 | The repository explains device strategies and passive MIDI safety, but no A4 saved-kit write path exists. | Keep operator flow in one plan and document the exact source-to-artifact lifecycle. |
| 2. Naming hygiene | 4 | Existing `analog_four_*` names are consistent; SysEx frame fields are not yet named centrally. | Add canonical A4 layout and calibration names under `data/`. |
| 3. Coupling and boundaries | 3 | Generic Elektron unpacking exists, but decode and future encode behavior could diverge. | Add one shared A4 codec and keep orchestration in `cockpit/export/`. |
| 4. Magic numbers and strings | 2 | Observed frame lengths, offsets, and parameter ranges are capture notes rather than typed facts. | Promote only proven values into `Final` data constants and bounded literals. |
| 5. Configuration vs convention | 4 | Track, candidate count, paths, and overwrite policy can be explicit CLI inputs. | Preserve explicit inputs and avoid environment variables. |
| 6. Test maintainability | 3 | Existing SysEx readers have tests, but there is no round-trip fixture or real-audio differential proof. | Add exact binary fixtures, deterministic inference fixtures, and tone-versus-noise integration coverage. |
| 7. Build and dev loop friction | 4 | `just check`, xdist, focused pytest, lint, Pyright, and review scripts already exist. | Document focused commands and preserve the full canonical gate. |
| 8. Error messages | 3 | File errors are human-readable but lack one bounded A4 export vocabulary. | Define a shared typed error-code contract and expose it in JSON and text output. |
| 9. Versioning and release | 4 | Package and release process remain unchanged by a passive feature. | Avoid new version sources or dependency changes. |
| 10. Future-proofing | 2 | Each newly discovered writable parameter could tempt a bespoke mutation path. | Use calibration data plus one generic renderer; keep unvalidated parameters in sidecars only. |

Baseline average: 3.2/5. The post-plan report records both the first implementation result and the corrective post-push review.

## 2026-07-27 Re-audit Triggers

- Native decoder crashes could terminate the caller before private staging
  cleanup; process isolation and parent-owned cleanup were required.
- The reader/sender/app surfaces duplicated MIDI provider and event-kind
  contracts; the canonical transport abstractions needed reuse.
- Publication locks, artifact reuse, ranking, and some guarded-send failure
  exits lacked complete operation-level observability.
- Large batch/app functions obscured cleanup and recovery behavior.
- The run-state file used status words outside its schema.
- Closeout docs reused stale coverage, SHA, and Windows reliability claims.

The paired report records the corrections and fresh exact-tree coverage. The
pushed SHA and online review state remain PR metadata rather than being inferred
from an earlier tree.
