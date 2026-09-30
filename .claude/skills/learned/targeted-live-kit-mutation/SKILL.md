---
name: targeted-live-kit-mutation
description: Implement or review live Elektron mutation targeting, lock intersection, captured-kit anchor/favorite workflows, local kit-package import, and fail-closed send planning in RytmRandomizer.
metadata:
  origin: auto-extracted-2026-08-26
---

# Targeted live-kit mutation

Use this skill when changing mutation scope, Cockpit target/lock state, captured
kit adoption, or a send plan that could reach an Elektron device.

## Invariants

1. Model targets as an include-list and locks/protection as a deny-list. Resolve
   `(explicit targets or the complete device domain) - locks` through
   `snapshot.mutation_scope.MutationScope`; do not reimplement the equation in
   each device.
2. Treat an empty target list as the backward-compatible all-scope default.
   Validate identifiers as actual non-boolean integers inside the registered
   device domain before changing session state.
   The appliance intentionally defines empty targets as none and must resolve
   that presentation rule before invoking the legacy scope default.
3. Carry scope through the public `MutationPlanner` and `Device` seams. Repeat
   the invariant at the inert send-plan boundary so a stale or externally
   constructed candidate cannot address a locked or untargeted item.
4. A target/lock change invalidates any prepared plan. UI optimistic updates
   need a per-request generation guard so an old rejection cannot overwrite a
   newer authoritative selection.
5. Promote a captured kit only after the canonical codec proves exact
   decode/re-encode round-trip stability. Project only fields already backed by
   the semantic map; retain but never guess unknown fields.
6. If saved-kit offsets, typed encodings, track stride, and fixture evidence are
   incomplete, return a blocked zero-event plan. A manual-backed live CC map is
   not evidence for saved-kit byte offsets.
7. A capture is fresh evidence only when its unique capture identity and
   timestamp follow the action it is meant to prove. Favorite recaptures must
   follow the manual-save attestation; show-time captures must follow the
   favorite recapture and any previous preflight. A persisted `show-ready`
   record is historical after process restart until a new current-session
   preflight succeeds.
8. Treat an imported kit package as catalog evidence, not executable
   authority. Verify canonical bytes, the complete required artifact set,
   family-specific codec round trips, and claimed fingerprints, then revoke
   transient selection/live/readiness grants. Never route an imported mutation
   candidate to ArmedApply unless it has been independently reconstructed from
   locally trusted source/profile inputs.
9. Publish evidence that becomes true as a pair—such as Rytm plus A4 source or
   recapture retention—in one atomic write set with one final manifest. A
   manifest must never expose a verified pair while only one exact frame is
   durable.
10. Current-KIT dumps reflect saved instrument state, not necessarily unsaved
    front-panel edits. When validating an A4 saved-KIT mapping or candidate,
    explicitly save the scratch KIT on the instrument before requesting the
    dump; keep unperformed observations blank.
11. When an audition transmits only deltas from an immutable source, require
    a manual source reload before every new live candidate; software reset
    alone leaves previous hardware deltas behind. Track the source provenance
    across ordinary candidate regeneration and invalidate derived plans when
    the source cue is removed. Require fresh source capture plus explicit
    reload acknowledgment; a saved-state dump alone is insufficient.
12. Protect every source hardware slot against favorite save destinations.
    For a fully locked partner, preserve all source bytes and compare the full
    payload; never treat an empty semantic comparison as universal success.
13. Derive imported semantic offsets from trusted calibration facts. Fixed
    point parsing and formatting must remain exact under ambient Decimal
    precision changes and reject nonrepresentable input without rounding.
14. An offline preparation report is evidence for review, never an ArmedApply
    grant. Reconstruct candidate bytes from retained source facts and bind the
    report to current capture, candidate, scope, cue and session. Invalidate
    both displayed and pending results when any context changes. Saved-KIT
    Q8.8 evidence cannot establish live paired-CC or NRPN conversion, output
    destination semantics, or a physical restore contract.
15. Inspect canonical transport metadata before forming a Rytm send plan. If
    any changed, in-scope, unlocked control needs unverified paired precision,
    mark the entire plan unready with `paired_control_precision_unverified`.
    Retain supported packets for inspection, but transmit zero packets: never
    send only the paired field's MSB or quietly apply a supported subset. An
    unchanged, locked or untargeted paired field is not a blocker.
16. Enforce exactly one selected raw input-name match at the real provider's
    freshly enumerated backend list before open. Missing or duplicate names
    refuse; opening the first duplicate can bind evidence to another same-family
    instrument. The capture service delegates this identity check; its request,
    cancellation and frame validation do not independently prove uniqueness.
    Keep cancellation and input-only ownership intact.
17. Discovery is an endpoint receipt, not physical acceptance. PnP/model names
    do not prove firmware, track-channel configuration, current control values
    or a recoverable source. First supervised Rytm trials use the guarded Show
    Kit source-reload/fresh-capture flow; a standalone Studio candidate does not
    inherit that source attestation. A separately supervised legacy app A4
    single-CC probe cannot authorize Cockpit A4/BOTH or scoped appliance APPLY.
    Separate host-send completion from observed mutation and manual recovery;
    after a partial or uncertain send, recover before preparing a new attempt.

## Verification

- Test empty/default scope, explicit targets, targets plus locks, invalid
  identifiers, stale-plan rejection, and contradictory packet rejection.
- Exercise captured-anchor SEND and prove every untargeted item stays unchanged.
- Cover mixed supported/paired changes, paired-only changes, and unchanged,
  locked and untargeted paired controls. A paired refusal keeps the whole plan
  unready and actual sends at zero even when supported inspection packets remain;
  verify it at the actual prepare/send boundary, not only a metadata helper.
- Inject zero, one and duplicate exact raw input-name matches; prove refusal
  happens before any input open, including a list change at the provider seam.
- Exercise stale source/recapture/preflight reuse, restart/import authority
  revocation, paired-retention failure rollback, and family-codec import
  rejection.
- Run passive-boundary tests and the frozen V1.34 parity tests without capture
  mode; the parity fixtures must remain untouched.
- Update the Cockpit protocol table and diagrams whenever target events or
  capture/adoption boundaries change.

The mandatory project rule is
`.claude/rules/targeted-mutation-safety.md`. The canonical code surfaces are
`rytm_randomizer/snapshot/mutation_scope.py`,
`rytm_randomizer/cockpit/mutation_targets.py`, and
`rytm_randomizer/cockpit/data/send_plan.py`.
