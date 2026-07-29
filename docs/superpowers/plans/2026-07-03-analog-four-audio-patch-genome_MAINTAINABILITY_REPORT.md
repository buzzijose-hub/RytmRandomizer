# Analog Four Audio Patch Genome Maintainability Report

> Status: in-flight

Date: 2026-07-29
Scope: current post-correction re-audit against the paired baseline.

| Question | Before | After | Evidence |
|---|---:|---:|---|
| 1. Onboarding curve | 3 | 5 | Plan, operator help, hardware-validation notes, replay playbook, and architecture lifecycle are linked. |
| 2. Naming hygiene | 4 | 5 | A4 frame, calibration, genome, inference, export, and publication concepts have explicit module ownership. |
| 3. Coupling and boundaries | 3 | 5 | Generic Elektron packing is shared; one A4 codec serves decode/render; guarded exporters resolve the registered A4 capability; the reader/sender/app reuse canonical MIDI provider/event-kind contracts; `app --arm` remains the only real-port boundary. |
| 4. Magic numbers and strings | 2 | 5 | Frame facts and writable calibration live in typed data modules; failure categories use one bounded contract. |
| 5. Configuration vs convention | 4 | 5 | Track, candidate count, paths, and overwrite are explicit. The developer-only `TYPECHECK_BASE_REF` and CI-provided `GITHUB_BASE_REF` inputs are documented, optional, and safely default to `origin/modularize-v1.34`. |
| 6. Test maintainability | 3 | 5 | Exact frame fixtures, deterministic goldens, interruption tests, child-crash containment/cleanup, real tone/noise integration, and rehashed malicious-bundle tests are isolated by responsibility. |
| 7. Build and dev loop friction | 4 | 5 | Focused tests finish in seconds; the canonical full, architecture, parity, lint, type, coverage, and review commands are recorded. |
| 8. Error messages | 3 | 5 | Saved-kit and batch CLIs return bounded codes, actionable text, manifest identity, retained-lock recovery details, and controlled `inference_failed` output for abnormal native exits. |
| 9. Versioning and release | 4 | 4 | No package version, dependency, installer, or release path changed. |
| 10. Future-proofing | 2 | 5 | New hardware-proven fields extend calibration/render data without forking batch orchestration; unsupported fields remain explicit sidecar rows. |

Post-plan average: 4.9/5, a +1.7 improvement. The latest corrective review
also found native-process containment, duplicated MIDI contracts, incomplete
publication/ranking/send observability, large orchestration functions, invalid
run-state status values, and stale closeout claims. Native work now runs in a
child owned by a cleanup-capable parent; transport contracts are shared; batch
staging/publication and app send responsibilities are split into focused
helpers; and the state file has schema enforcement.

The fresh focused A4/operator suite passed 912 tests, along with 705
architecture tests and 685 V1.34 parity items. The exact corrected-tree
full-suite run passed 6,825 tests / 3 skipped. The Ruff/Black/isort/Vulture/
strict-production-Pyright/mechanical-review set is clean. Dynamic test-harness typing
remains the accepted scoped Gate 3 debt; all 63 touched production modules pass
strict Pyright.
Touched production files reached 100% statement and branch coverage across
7,896 statements and 1,892 branches. Follow-up publication, online checks, and
the fresh reviewer verdict are tracked on PR #214.

The largest residual constraints are explicit: generated saved-kit SysEx writes
only Filter2 Resonance until additional A4 parameters complete the same
hardware-validation sequence, Windows native-decoding success remains
environment-dependent and unestablished, and the corrected 27-row/37-message
physical rehearsal remains pending after the first pass disproved six enum
values. Batch orchestration and verified-reader
modules also remain large;
their post-review splits isolate contracts, codec, publication, and ranking,
but a future narrow refactor can reduce the remaining coordination surfaces
without changing behavior.
