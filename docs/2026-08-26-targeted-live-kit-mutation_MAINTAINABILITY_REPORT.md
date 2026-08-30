# Targeted live-kit mutation maintainability report

Date: 2026-08-26
Plan: `docs/superpowers/plans/2026-08-26-targeted-live-kit-mutation.md`

No category regressed relative to the plan's pre-implementation audit.

| Area | Result | Post-implementation evidence |
|---|---|---|
| Onboarding curve | Improved | Quickstart, architecture prose, diagrams, and a learned skill all state the same include-minus-deny equation and A4 blocker. |
| Naming hygiene | Stable | `MutationScope`, `MutationTargets`, `target_ids`, and `locked_ids` retain distinct meanings across Python, wire DTOs, and TypeScript. |
| Coupling / boundaries | Improved | Device-neutral scope lives in `snapshot/`; Cockpit wire fields live in `cockpit/`; both devices consume the public planner seam; input capture resolves the optional `devices.saved_kit_capture` capability instead of importing concrete family codecs. |
| Magic values / strings | Improved | Bounds and wire discriminators are `Final`/`Literal`; strict validation rejects boolean and coercible pseudo-integers. |
| Configuration | Stable | No environment variable or implicit hardware-mode switch was added. |
| Test maintainability | Improved | Existing fixtures are extended; focused tests cover one canonical scope model, capture bridge, adapters, WS, and UI. |
| Build / dev loop | Stable | Focused pytest/Vitest precede existing full lint, fast, architecture, build, and parity commands. |
| Error messages | Improved | Invalid scope and mapping-pending A4 paths fail categorically at their source boundary; target/lock transitions are logged. |
| Versioning / release | Stable | No format version, package version, or release path changed. |
| Future-proofing | Improved | A device adds domain validation around shared `MutationScope`; it does not need a parallel target equation or Cockpit sender. |

The post-review concurrency finding was corrected with request-generation and
current-state guards in both target and lock hooks. The architecture review's
stale scope, bootstrap, capture-authority, and anchor-adoption diagrams were
also corrected before handoff.

The integrated output design keeps the same assessment without retaining the
experimental Cockpit real-adapter composition. The packaged shell adds only
explicitly armed, input-only current-KIT capture. Real Rytm output remains
exclusively behind the existing `senders.armed_apply.ArmedApplySession`
boundary, which is already the repository's reviewed lazy-open authority.
Binding SEND to the exact current `send_plan_id` removes a stale-plan race.
The defect is fixed in implementation and regression tests: missing,
malformed, and stale ids are rejected before output opens. The operator dialog
and Quickstart make the port, packet scope, manual hardware reload procedure,
and A4 exclusion reviewable at the moment of action. Cockpit has no persistent
restore feature.

The dual-machine coordinator also improves failure locality: capture, target,
lock, candidate, plan, authority, failure, and recovery state advance
independently for Rytm and A4. Rytm connection state mirrors the armed-output
manager; A4 capture/session state does not claim continuous independent
physical hot-plug telemetry. A lane failure cannot grant authority to its
sibling. The A4 evidence manifest keeps future mapping work auditable without
turning partial byte observations into executable events.

Final targeted re-review found no remaining Critical or Important issue.
Capture resolves a registry-backed optional capability, mutable stage
coordination lives outside the data leaf, lane cardinality comes from shared
device policy, and exact port names are omitted even when an exception embeds
quoted, escaped, or control-character variants. The one retained Minor is an
observability-only process-interruption edge during an already-started burst;
the output boundary still closes and clears authority.
