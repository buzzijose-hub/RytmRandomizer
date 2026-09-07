# Show Kit Forge post-plan maintainability report

Date: 2026-09-07 (integration closeout of the September 4 plan)

Plan: [`2026-09-04-show-kit-forge.md`](2026-09-04-show-kit-forge.md)

Baseline:
[`2026-09-04-show-kit-forge_MAINTAINABILITY_AUDIT.md`](2026-09-04-show-kit-forge_MAINTAINABILITY_AUDIT.md)

Status: in-flight — software re-audit recorded; final aggregate gates, hosted
PR/CI, and operator-present studio validation remain pending.

This comparison uses qualitative dispositions backed by paths, completed
automated checks, and the targeted review findings below. Physical evidence
remains outside the software maintainability assessment.

| Gate 14 question | Pre-plan risk or requirement | Post-plan evidence | Disposition |
| --- | --- | --- | --- |
| Onboarding curve | The paired workflow needed one discoverable operator and contributor path. | The Cockpit panel, Quickstart, architecture section, dated run artifacts, and blank studio checklist describe the same lifecycle and authority boundary. `docs/README.md` and `CLAUDE.md` link the handoff directly. | Addressed in software/docs; fresh-clone answers are recorded in the run report. |
| Naming hygiene | Candidate, live-unsaved, favorite, save attestation, semantic verification, and show readiness could be conflated. | The domain records and UI use distinct names for selection, Rytm live audition, favorite, per-device save attestation, recapture, and show-time preflight. Favorite replacement is explicit. | No observed naming regression. |
| Coupling / module boundaries | A second sender, registry, package-root hierarchy, or codec fork would create drift. | `cockpit.show_bank` composes existing capture, mutation, export, codec/strategy, and ArmedApply seams. The nested-package dependency row is explicit and its focused import-matrix test passed. A4 offline rendering remains separate from hardware-send authority. | Addressed; 801 architecture cases passed in the full run. |
| Magic numbers / strings | A4 offsets, stride, Q8.8 bounds, lifecycle labels, and wire actions needed canonical ownership. | Hash-pinned evidence fixes Track 1 offset 128, track stride 350, and unsigned Q8.8 `0x0000..0x7F00`. Typed DTOs and canonical calibration/strategy facts own the lifecycle and evidence vocabulary. | No observed regression in reviewed paths. |
| Configuration vs convention | Local paths and hardware choices could become client-controlled or implicit. | Store/package identifiers are filename-safe and resolved beneath server-owned roots. Rytm SEND still requires the existing exact plan and output confirmation; A4 has no SEND action. No new environment variable or dependency pin was introduced. | Stable. |
| Test maintainability | Paired fixtures and lifecycle boundaries needed intent-named, reusable coverage. | Focused Show Bank tests share `tests/cockpit/show_bank/_support.py`; codec, domain, persistence, workspace, WebSocket, and frontend concerns remain separated. The domain/readiness slice reached 100% statement and branch coverage in its recorded focused run. | Addressed; final counts are recorded in the run report. |
| Build / dev loop friction | Heavy Python/frontend closeout needed serialization and bounded inner loops. | The run log records focused serial checks, while the existing `just check`/`just review` and repository commands remain canonical. No alternate build entry point was added. | Stable; serialized timings are recorded in the run report. |
| Error messages | Stale capture, corrupt package, unsupported A4 field, or unconfirmed SEND failures needed source-local recovery text. | Validation now distinguishes malformed/corrupt retained evidence, stale recapture/preflight provenance, catalog-only imports, explicit favorite replacement, unsupported A4 fields, and exact-plan Rytm refusal. The operator UI/checklist states the corresponding recovery action. | Addressed in reviewed boundaries. |
| Versioning / release | New persisted shapes must not alter the package release, hardware pins, or V1.34 output. | Show-bank/show-pack records carry explicit schema versions. `pyproject.toml`, hardware dependency pins, and `tests/fixtures/v134_parity/` are outside the working-tree change set. | Stable; all 685 frozen parity cases passed in the full run. |
| Future-proofing | Another verified A4 field must not implicitly widen output authority. | Filter 1 Frequency has a distinct offline captured-KIT renderer and evidence status; its result always reports `hardware_send_validated = false`. The existing targeted-mutation skill/rule now require field-specific evidence, fresh provenance, atomic paired retention, and catalog-import isolation. | Addressed without granting broader authority. |

## Regression and residual-risk decision

The implemented safety and persistence boundaries satisfy the reviewed
software requirements. The run report records test, coverage, lint, type,
build, parity, review, hosted-CI, and PR results. The residual readability
tradeoff below is retained explicitly rather than hidden by aggregate counts.

The remaining software concern is panel size: `ShowKitForgePanel.tsx` contains
roughly 1,380 lines in its principal component, with 33 state hooks and seven
effects. This is a Minor readability risk under the handbook's 500-line split
signal. Exact SEND state/confirmation already lives in `ExactRytmSend`, and
pure view derivation lives in `showKitForgeModel`. Bank/cue drafts and
acknowledgment/revision handling stay together for this release so ownership
of those coordinated transitions remains explicit. A later section/hook
extraction should preserve the complete journey and stale-state tests. The
report does not present the remaining component size as an ideal design.

Validation complexity in the persistence layer was reduced during review:
manifest decoding, required retention, device claims, and exact file-set
verification now have separate helpers. New production modules pass the
additional PLR/ERA/ARG lint rules; the narrowly retained keyword-rich public
action signatures document their explicit paired-evidence contracts.

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
