# Captured Rytm mapping maintainability baseline

> Status: in-flight — retrospectively reconstructed baseline, not a timely
> pre-plan audit.

Per [PLAN_REQUIREMENTS.md](../../PLAN_REQUIREMENTS.md), Gate14. Recorded after
implementation began from source `8cfa6f7b` and the observed capture defects.
No timed onboarding exercise or original preflight receipt exists. Scores are
inspection judgments: 1 blocker, 2 material gap, 3 workable, 4 clear tested
boundary, 5 fully evidenced delivery. They do not certify gate completion.

| Required question | Baseline assessment | Required outcome |
| --- | --- | --- |
| Onboarding: can a contributor find where to add X in <30 minutes? | 3 — architecture and contribution guides locate existing strategy/data/Cockpit seams; no timed exercise. | Link the exact defect, facts, remaining gaps and correction without claiming the timing target measured. |
| Naming: are modules and abbreviations clear? | 3 — machine keys and generic SRC are both established, but their relationship was undocumented at the consumer. | Document exact owning-section normalization and preserve compact keys. |
| Coupling: do boundaries and diagrams match? | 2 — producer emitted machine-key sections the consumer silently omitted; decoder tests alone missed composition. | Exercise real retained frames through the actual anchor, bridge and planner; retain matching machine-fact gating. |
| Magic values: are dispatch strings enumerated and constants `Final`? | 4 — existing source token is typed; machine IDs live in canonical data. | Reuse `RenderedStyleSource` vocabulary and derive the XT identity from the catalog. |
| Configuration: are runtime choices configurable? | 3 — channels and transport belong to existing runtime seams. | Add no environment variable, channel assumption or output configuration. |
| Tests: are helpers shared and tests maintainable? | 2 — existing per-layer tests were green while machine SRC projection was empty. | Retained-frame composition and unsupported-ID/paired-refusal regressions; reusable helpers in `tests/conftest.py`. |
| Build/dev friction: are install/verification and timing known? | 3 — existing virtualenv and repository check commands available; no new clean-install timing receipt. | Record actual runner summaries and source; use focused `-n 0` and coordinator-capped full runs. |
| Errors: do failures identify the authoritative source? | 2 — mapping-pending status and omission counts did not reveal the owning-section mismatch. | Correct fixture-proven XT status and document unverified aliases/precision rather than masking gaps. |
| Version/release: is the source of truth clear? | 3 — existing package version and PR delivery paths available. | Deliver one correction through existing direct-base PR254; make no release or installed-app claim. |
| Future extension: how many files does the next extension touch? | 3 — facts and compact aliases have established homes, but readiness differs by layer. | Use the existing catalogs, lookup and bridge; expose remaining families/semantic disputes explicitly. |

PR254 already records the formal-audit timing deviation. Gate14 remains
unchecked; maintainer acknowledgment is not inferred from this reconstructed
baseline. The [current report](2026-10-01-rytm-captured-machine-mapping_MAINTAINABILITY_REPORT.md)
is a local reassessment; the actual post-merge ten-row audit is still required.
