# Analog Four Audio Patch Genome Maintainability Report

> Status: in-flight

Date: 2026-07-16
Scope: post-implementation re-audit against the paired baseline.

| Question | Before | After | Evidence |
|---|---:|---:|---|
| 1. Onboarding curve | 3 | 5 | Plan, operator help, hardware-validation notes, replay playbook, and architecture lifecycle are linked. |
| 2. Naming hygiene | 4 | 5 | A4 frame, calibration, genome, inference, export, and publication concepts have explicit module ownership. |
| 3. Coupling and boundaries | 3 | 5 | Generic Elektron packing is shared; one A4 codec serves decode/render; batch uses the pure renderer. |
| 4. Magic numbers and strings | 2 | 5 | Frame facts and writable calibration live in typed data modules; failure categories use one bounded contract. |
| 5. Configuration vs convention | 4 | 5 | Track, candidate count, paths, and overwrite are explicit; no environment variable was added. |
| 6. Test maintainability | 3 | 5 | Exact frame fixtures, deterministic goldens, interruption tests, and real tone/noise integration tests are isolated by responsibility. |
| 7. Build and dev loop friction | 4 | 5 | Focused tests finish in seconds; the canonical full, architecture, parity, lint, type, coverage, and review commands are recorded. |
| 8. Error messages | 3 | 5 | Saved-kit and batch CLIs return bounded codes, actionable text, manifest identity, and retained-lock recovery details. |
| 9. Versioning and release | 4 | 4 | No package version, dependency, installer, or release path changed. |
| 10. Future-proofing | 2 | 5 | New hardware-proven fields extend calibration/render data without forking batch orchestration; unsupported fields remain explicit sidecar rows. |

Post-plan average: 4.9/5, a +1.7 improvement. No item regressed and no corrective workstream is required before learning capture.

The largest residual constraint is intentional: generated saved-kit SysEx writes only Filter2 Resonance until additional A4 parameters complete the same reference, novel-value, and cross-track hardware validation sequence.
