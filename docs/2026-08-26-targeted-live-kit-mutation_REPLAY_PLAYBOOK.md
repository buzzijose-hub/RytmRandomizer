# Replay playbook: targeted live-kit mutation

For the next targeted device-mutation slice:

1. Establish the exact device item domain and use `MutationScope` for targets
   minus locks; keep device-specific wire names outside `snapshot/`.
2. Invalidate candidate/send-plan state whenever scope changes, then enforce
   scope again when constructing/deserializing the inert send plan.
3. For captured state, separate codec round-trip proof, semantic mapping proof,
   and hardware proof. Promote only the layers already proven.
4. Test default scope, explicit scope, target-plus-lock intersection, malformed
   identifiers, stale-plan contradictions, and untargeted state preservation.
5. Run frontend protocol/state tests, focused 100% branch coverage, passive
   safety tests, architecture gates, and frozen parity without capture mode.
6. Update the protocol table and diagrams showing planner scope, bootstrap
   events, real hardware authority, decode ownership, and anchor adoption.

Stop immediately on a V1.34 fixture diff or any path that would make an
unproven captured field sendable.
