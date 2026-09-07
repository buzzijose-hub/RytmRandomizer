# Show Kit Forge post-plan maintainability report

Date: 2026-09-07 (integration closeout of the September 4 plan)

Plan: [`2026-09-04-show-kit-forge.md`](2026-09-04-show-kit-forge.md)

Baseline:
[`2026-09-04-show-kit-forge_MAINTAINABILITY_AUDIT.md`](2026-09-04-show-kit-forge_MAINTAINABILITY_AUDIT.md)

Status: in-flight — maintainer-review repairs and final local verification are
complete for [PR #238](https://github.com/buzzijose-hub/RytmRandomizer/pull/238).
The identified studio build, hosted CI, and required maintainer review remain
pending. The [review reconciliation ledger](../../2026-09-07-show-kit-forge-review-reconciliation.md)
and [run report](2026-09-04-show-kit-forge_RUN_REPORT.md) record current local
evidence and distinguish it from the original integration history.

Final local verification passed 8,926 Python tests with five skips in 272.28s.
All 32 touched production modules cover 6,458 statements and 1,558 branches at
100%; whole-package pure-branch coverage is 99.3597%. Frontend verification
passed 809 tests in 62 files, with 3,269 statements, 2,455 branches, 1,125
functions and 2,943 lines all at 100%. Typecheck, lint and production build
passed. Playwright passed 21 tests with two existing skips in 50.2s using
disabled/fake MIDI, and the screenshots were inspected. Physical evidence
remains outside this software maintainability assessment.

| Gate 14 question | Pre-plan risk or requirement | Post-plan evidence | Disposition |
| --- | --- | --- | --- |
| Onboarding curve | The paired workflow needed one discoverable operator and contributor path. | The Cockpit panel, Quickstart, architecture section, dated run artifacts, and blank studio checklist describe the same lifecycle and authority boundary. `docs/README.md` and `CLAUDE.md` link the handoff directly. | Addressed in software/docs; fresh-clone answers are recorded in the run report. |
| Naming hygiene | Candidate, live-unsaved, favorite, save attestation, semantic verification, and show readiness could be conflated. | The domain records and UI use distinct names for selection, Rytm live audition, favorite, per-device save attestation, recapture, and show-time preflight. Favorite replacement is explicit. | No observed naming regression. |
| Coupling / module boundaries | A second sender, registry, package-root hierarchy, or codec fork would create drift. | `cockpit.show_bank` composes existing capture, mutation, export, codec/strategy, and ArmedApply seams. Shared input primitives live in `guardrails/input_validation.py`; the thin Filter 1 Frequency adapter delegates to the schema-driven saved-KIT candidate renderer. Device scopes use the canonical registry domain. | All 801 architecture cases passed in final local verification; hosted CI and required review remain pending. |
| Magic numbers / strings | A4 offsets, stride, Q8.8 bounds, lifecycle labels, and wire actions needed canonical ownership. | The calibration record owns verified native offsets, width, encoding, range, and scale and resolves field offsets through the saved-KIT schema. Shared exact fixed-point parsing/formatting avoids ambient Decimal rounding. Show device IDs alias stage vocabulary; readiness emits closed tokens with UI display text. | Maintainer findings addressed; final local aggregate verification passed. |
| Configuration vs convention | Local paths and hardware choices could become client-controlled or implicit. | Filename-safe bank/entity IDs retain a 64-character bound and package IDs a distinct 96-character bound beneath server-owned roots. Rytm SEND retains exact plan/output confirmation. A4 review accepts bounded output-port intent without discovering or opening a port. No new runtime environment variable was added; build-only variables are documented in both required indexes. | Boundary contracts are explicit; focused maximum-ID roundtrips passed. |
| Test maintainability | Paired fixtures and lifecycle boundaries needed intent-named, reusable coverage. | Show Bank tests reuse canonical DTO and workspace helpers plus valid synthetic KIT headers. The nine previously bare `ValueError` sites now assert per-case refusal reasons; categorized `DataError` tests retain stable context assertions. The final full suite covers the changed validation boundaries. | Focused and final local aggregate results are recorded separately in the reconciliation ledger and run report. |
| Build / dev loop friction | Heavy Python/frontend closeout needed serialization and bounded inner loops. | Heavy checks remain serialized and focused checks use the repository commands. The requested studio handoff must identify the executable, source revision, build manifest/hashes, self-contained sidecar, and smoke result. | Local verification passed; identified studio build, its smoke test and hosted CI remain pending. |
| Error messages | Stale capture, corrupt package, unsupported A4 field, or unconfirmed SEND failures needed source-local recovery text. | Validation now distinguishes malformed/corrupt retained evidence, stale recapture/preflight provenance, catalog-only imports, explicit favorite replacement, unsupported A4 fields, and exact-plan Rytm refusal. The operator UI/checklist states the corresponding recovery action. | Addressed in reviewed boundaries. |
| Versioning / release | New persisted shapes must not alter the package release, hardware pins, or V1.34 output. | Show-bank/show-pack schema versions and the 64/96 ID contracts remain explicit. A verified package starts a new local catalog at revision 0, preserving the source manifest and historical evidence while clearing transient authority. Maximum source revision therefore remains importable. Hardware pins and frozen parity artifacts are unchanged. | All 685 frozen parity cases passed in final local verification; no release or hardware-validation claim. |
| Future-proofing | Another verified A4 field must not implicitly widen output authority. | Filter 1 Frequency uses a thin field adapter over shared calibration, saved-KIT schema, and renderer behavior. A separate inert A4 preparation report checks selected-candidate provenance, exact source/candidate bytes, current capture freshness, scope, and recovery metadata. It always reports `ready = false`, `hardware_send_validated = false`, and permanent transport blockers. | Reuse improved; no A4 output or persistent-save authority granted. |

## Regression and residual-risk decision

The review refactor addresses the identified validation, calibration, device
vocabulary, and blocker-reporting defects. The reconciliation ledger separates
completed focused and final local checks from identified-build work, hosted CI,
and required maintainer review. Those remaining external steps are not marked
complete by this report.

Panel size remains a Minor readability risk under the handbook's 500-line split
signal. Exact SEND state/confirmation lives in `ExactRytmSend`, pure view
derivation in `showKitForgeModel`, and the new inert review in
`A4PreparationPanel`. Bank/cue drafts and acknowledgment/revision handling stay
together so ownership of coordinated transitions remains explicit. A later
section/hook extraction must preserve the complete journey and stale-response
tests. This report does not present the remaining main-panel size as ideal.

Validation complexity was reduced through shared strict primitives and one
canonical JSON encoder for store, package, and review serialization. The renamed
validator definitions and short-alias blocks were removed; legacy recipe APIs
re-export the shared implementations. Manifest decoding, required retention,
device claims, and exact file-set verification retain focused helpers.

File-opening and directory-identity checks retain boundary-specific bounds,
error categories, publication checks, and cleanup behavior. A shared public
regular-file opener remains a reviewed extraction opportunity; the existing
private streaming opener cannot replace the bounded store reader without
preserving its post-read identity checks. This minor is not marked fully fixed.
Final local lint/type, full-suite and coverage checks passed. The reconciliation
ledger retains the pending identified-build, hosted-CI and required-review steps.

The remaining hardware risk is intentionally blocking, not scored away:

- the generated A4 Filter 1 Frequency scratch KIT has not been manually
  transferred, inspected, saved on the instrument, and recaptured;
- Show Kit Forge has no A4 SEND authority;
- the Rytm one-pad ArmedApply audition, untouched-pad observation, manual
  source reload, and fingerprint restoration proof remain unperformed; and
- favorite save/recapture plus fresh full-fingerprint preflight remain
  operator-present steps for every show cue.

Until those observations are entered in the dated studio checklist, this
report supports software maintainability only and must not be read as physical
hardware validation.
