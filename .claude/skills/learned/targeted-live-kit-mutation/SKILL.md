---
name: targeted-live-kit-mutation
description: Implement or review live Elektron mutation targeting, lock intersection, captured-kit anchor promotion, and fail-closed send planning in RytmRandomizer.
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

## Verification

- Test empty/default scope, explicit targets, targets plus locks, invalid
  identifiers, stale-plan rejection, and contradictory packet rejection.
- Exercise captured-anchor SEND and prove every untargeted item stays unchanged.
- Run passive-boundary tests and the frozen V1.34 parity tests without capture
  mode; the parity fixtures must remain untouched.
- Update the Cockpit protocol table and diagrams whenever target events or
  capture/adoption boundaries change.

The mandatory project rule is
`.claude/rules/targeted-mutation-safety.md`. The canonical code surfaces are
`rytm_randomizer/snapshot/mutation_scope.py`,
`rytm_randomizer/cockpit/mutation_targets.py`, and
`rytm_randomizer/cockpit/data/send_plan.py`.
