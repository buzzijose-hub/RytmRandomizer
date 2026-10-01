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
15. Refuse the entire Cockpit plan when any effective candidate row needs
    unverified paired-control precision (`paired_control_precision_unverified`).
    Do not silently drop that row, send the safe subset, round a fractional
    value or keep only its MSB. Retain the blocked plan/reasons for inspection;
    saved-file precision and manual CC addresses are not live-conversion proof.
16. At input open, require exactly one occurrence of the selected exact port
    name in a fresh backend listing. Reject duplicates before opening instead
    of selecting the first. Bind capture work to cancellation and the current
    session generation; teardown stops polling, and a late cancelled/stale
    result cannot adopt a source. Keep the previous verified source intact.
17. Separate output revocation from offline evidence destruction. Armed
    disconnect must revoke live authority and require fresh reload/capture/
    preparation before a later send. Passive browser disconnect and rejected
    DISARM must preserve offline candidate, plan and source identity within the
    same running sidecar session. This is not durable local retention. Neither
    path may auto-re-arm or treat retained work as a hardware-write grant.
18. Keep studio handoffs bounded and evidence-specific. The first Show Kit
    Forge physical gate is one scoped Rytm RAM audition followed by manual
    source reload, physical recovery observation and fresh baseline capture.
    A separately approved legacy `--arm --a4-send-param` probe is one integer,
    non-paired CC on one configured spare-kit track, not general A4/BOTH SEND
    or a bypass for blocked candidates. The existing A4 four-track scratch
    return tests offline bytes after manual hardware save; do not repeat a
    completed offset/stride matrix or generalize a pass to fractional MIDI.
    Local candidate/bank save is not hardware save or reload. Passive support
    inventory reports describe canonical evidence, never unlock authority.

## Verification

- Test empty/default scope, explicit targets, targets plus locks, invalid
  identifiers, stale-plan rejection, and contradictory packet rejection.
- Exercise captured-anchor SEND and prove every untargeted item stays unchanged.
- Exercise stale source/recapture/preflight reuse, restart/import authority
  revocation, paired-retention failure rollback, and family-codec import
  rejection.
- Cover mixed safe/paired whole-plan refusal, duplicate exact input names,
  cooperative capture cancellation, late-result rejection, blocked-plan
  retention, passive-disconnect retention and rejected-DISARM identity.
- Run passive-boundary tests and the frozen V1.34 parity tests without capture
  mode; the parity fixtures must remain untouched.
- Update the Cockpit protocol table and diagrams whenever target events or
  capture/adoption boundaries change.

Keep software verification and physical observations separate. A handoff that
prohibits tests/builds or hardware access must report them as not run, leave
unobserved results blank, and stay within its assigned files. Shared Studio
safety work does not validate Pi #252 touch/display UI or packaging; that PR is
groundwork with non-simulation APPLY refused and deployment on hold pending
focused work. Use
`docs/COCKPIT_QUICKSTART.md` section 6a and the existing
`docs/hardware-validation/2026-09-04-show-kit-forge-studio-checklist.md` for the
ordered operator-present gates and evidence-specific unlock limits.

The mandatory project rule is
`.claude/rules/targeted-mutation-safety.md`. The canonical code surfaces are
`rytm_randomizer/snapshot/mutation_scope.py`,
`rytm_randomizer/cockpit/mutation_targets.py`, and
`rytm_randomizer/cockpit/data/send_plan.py`.
