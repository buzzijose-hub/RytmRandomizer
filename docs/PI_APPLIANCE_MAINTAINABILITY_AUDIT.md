# Pi appliance maintainability baseline

## Computer-first continuation baseline (2026-09-30)

Continuation preflight used delivered source `b613fb3b`; the written plan and
device audits preceded the two implementation assignments. This paragraph
formalizes that preflight while their isolated work is in progress. Existing
ownership, naming, release, environment and test conventions remain the
baseline below. Two traced defects affect identity and exact transport: input
capture picks the first duplicate endpoint name, and Studio plan preparation
can use only the MSB of a canonical paired Rytm control.

Repair in the owning provider and existing send-plan builder; do not introduce
another adapter, renderer, registry or capture service. Preserve the unknown
input refusal and passive/lazy defaults. Reuse provider/capture/armed-send fakes
and mirror the typed readiness vocabulary in TypeScript. Explain refusals in
the existing rail and operator docs. These repairs improve the baseline's
error-message and future-extension dimensions without changing configuration,
versioning, frozen output or physical authority. Independent post-integration
review and actual integrated tests remain required.

Date of formalization: 2026-09-30. Baseline source: `892aaffca2484d1939ba3e133263aaadde2f22de`.

This is a **retrospective** Gate 14 baseline, reconstructed during final review
from the starting source and the [implementation plan](superpowers/plans/2026-09-30-pi-performance-appliance.md).
The implementation had already begun; this file does not assert that a scored
audit existed before it. The plan's abstraction survey and execution ledger
preserve the earlier decisions. The missing formal audit was an Important
review finding, repaired together with the [comparison report](PI_APPLIANCE_MAINTAINABILITY_REPORT.md).

Scores are the present reviewer's qualitative assessment of the starting
architecture's suitability for the Pi extension: 1 means high maintenance risk,
5 means low risk. They are not historical measurements or hardware results.

| Gate 14 dimension | Baseline score | Evidence at the starting source and required response |
| --- | ---: | --- |
| Onboarding curve | 3 | Cockpit and Device/Strategy guidance existed, but there was no Pi route/deployment handoff. Give operators and contributors one linked entry path. |
| Naming hygiene | 4 | Snapshot, capture, stage and ArmedApply already distinguished important concepts. Preserve those names and distinguish simulation, saved-KIT projection and unsaved working state. |
| Coupling / module boundaries | 4 | Registered devices, the pure Cockpit engine, capture service and guarded output seam existed. Compose them without another sender, registry, per-family root package or desktop shell. |
| Magic numbers / strings | 3 | Device catalogs and native field facts existed; appliance actions, scope limits and display bindings needed explicit ownership. Reuse canonical facts and validate closed action vocabularies. |
| Configuration vs convention | 4 | Existing paths, authentication and MIDI opt-in could support a local presentation. Document all added environment reads and require explicit hardware/board configuration. |
| Test maintainability | 4 | Shared fake MIDI, capture, snapshot and WebSocket helpers already existed. Add behavioral refusal tests without cloning those fixtures or relaxing frozen parity. |
| Build / dev loop friction | 3 | Desktop/frontend/backend tools existed; a Pi deployment and reproducible source identity did not. Keep one dependency graph and bound expensive workers. |
| Error messages | 3 | Existing structured refusals and diagnostics were reusable. New UI and package failures needed actionable reasons without credential or saved-content disclosure. |
| Versioning / release | 3 | Package version and persisted-state registry were canonical; there was no Pi release lifecycle. Bind package/wheel evidence to source and preserve user data during rollback. |
| Future-proofing | 3 | The existing Device/Strategy boundary supported another family, but extending readable A4 fields could accidentally imply output authority. Keep per-field evidence and separate preview/send/restore claims. |

The highest risks were authority leakage from a simulated launch, native-value
loss, stale confirmation/capture results, source ambiguity across editable
worktrees, and partial release recovery. Those risks became concrete repairs
recorded in the [run log](PI_APPLIANCE_RUN_LOG.md), not accepted exceptions.
