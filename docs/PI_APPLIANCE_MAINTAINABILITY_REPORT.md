# Pi appliance maintainability comparison

Date: 2026-09-30. Reviewed code checkpoint: `97fd6216`.
See the [retrospective baseline](PI_APPLIANCE_MAINTAINABILITY_AUDIT.md) for the
scoring method and the explicit chronology limitation.

This is the post-implementation comparison, formalized after independent
dimension reviews and repairs. Final aggregate acceptance and PR publication
were still in progress when this report was written. Existing checkpoint
results are recorded in the [run report](PI_APPLIANCE_RUN_REPORT.md); this
assessment does not turn them into results for a later source SHA.

| Gate 14 dimension | Baseline → reviewed | Evidence and disposition |
| --- | --- | --- |
| Onboarding curve | 3 → 4 | Operator, deployment, capability and architecture docs describe the same shared product. The plan links durable run artifacts and five tracked-only onboarding answers. No remaining software documentation gap identified in this dimension. |
| Naming hygiene | 4 → 4 | Distinct lane request, native projection, provenance, candidate, local history and exact action concepts retain their meanings. Scoped helper names were clarified during review. |
| Coupling / module boundaries | 4 → 4 | The appliance delegates to existing mutation, HistoryStore, ProfileRegistry, capture and device strategies. The narrowly reviewed `dual_machine → data` edge consumes canonical target facts; there is no file exemption or second output seam. |
| Magic numbers / strings | 3 → 4 | Validated `OPERATIONS`, protocol inventories, typed device IDs, immutable limits and canonical native domains replace scattered assumptions. Typed fixed-shape records and shared validators were repaired at `226aa0f0`; A4 projection uses the public iterator at `8067387e`. |
| Configuration vs convention | 4 → 4 | The four appliance environment settings are explicit and passive by default. The inherited Wayland/runtime variables are documented in both environment indexes. Pins require a selected board configuration; no GPIO default grants authority. |
| Test maintainability | 4 → 4 | Tests reuse shared capture/WS helpers and assert refusals before mutation/publication. Coverage thresholds and V1.34 fixtures remain unchanged. Component tests and real-browser checks cover different evidence; skipped physical/platform cases remain visible. |
| Build / dev loop friction | 3 → 4 | One launcher packages the production frontend and colocated Python source with source-bound receipts. Heavy work is serialized with Python four/browser one/frontend two workers. Cross-installed package and UTF-8 issues have focused regressions. ARM64 execution remains unverified. |
| Error messages | 3 → 4 | Capture, stale revision, corrupt profiles, unsupported native semantics and package failures have explicit blockers. Private bootstrap data stays out of normal logs and screenshots. Compact capture screenshots now show the actual refusal and recovery controls. |
| Versioning / release | 3 → 4 | The existing version/schema registry remains canonical. Fresh wheelhouse receipts, retained-file inventory and prior-release service templates are checked before activation; rollback retains user data and autostart choice. |
| Future-proofing | 3 → 4 | Catalog rows carry native/display/MIDI distinctions and independent send/restore blockers. A new readable field can extend facts, canonical strategy and projection tests without granting live authority or adding a device registry. |

No negative score delta remains in this qualitative software assessment.
The large orchestration files remain a maintenance cost: the launcher has 889
lines at the reviewed checkpoint, and the workspace keeps coupled revision,
scope and history transitions together. Bounded pure helpers, shared manifest
verification, typed records and focused tests make that cost explicit. Further
growth should extract a cohesive responsibility while preserving those seams;
file size alone is not a reason to introduce a parallel framework.

The late formalization is a process shortcoming, not a claim of timely Gate 14
execution. The [replay playbook](PI_APPLIANCE_REPLAY_PLAYBOOK.md) requires the
next run to write its baseline before implementation and append decisions as
they occur. Physical Pi, ARM64 dependency installation, unsaved working-state
readback and general live A4/restore authority remain external evidence gaps.
