# Targeted mutation safety

**Authority:** `docs/ARCHITECTURE.md` §6.2 and
`docs/COCKPIT_QUICKSTART.md`.

Apply this rule to mutation targets, pad/track locks, captured-kit promotion,
planner scope, and hardware send plans.

1. The canonical scope is `(explicit targets or all available items) - locks`.
   Targets include; locks deny. Empty targets preserve legacy all-scope
   behavior.
2. Device ids must be strict, non-boolean integers in the declared Rytm
   (`1..12`) or A4 (`1..4`) domain. Invalid input fails without changing the
   previous state.
3. Scope travels through `MutationScope`, `MutationPlanner`, and `Device`.
   Cockpit may expose device-specific wire fields, but snapshot/device layers
   must not depend on Cockpit DTOs.
4. A prepared plan is inert and explicit. It must reject packets for locked
   items or outside a non-empty target set before any real output port can be
   opened.
5. Captured Rytm state may become an anchor only after exact codec round-trip
   validation and projection through promoted semantic mappings. Adoption is
   in-memory and performs no MIDI I/O.
6. Captured A4 mutation stays zero-event and not ready until saved-kit offsets,
   encodings, per-track stride, fixture-backed byte-diff isolation, and exact
   re-encode evidence are promoted. Never infer offsets from live CC facts.
7. V1.34 fixtures are never regenerated for targeted Cockpit work, and ordinary
   CLI/Cockpit composition remains passive unless an explicit armed boundary is
   constructed.

See `.claude/skills/learned/targeted-live-kit-mutation/SKILL.md` for the focused
implementation and verification workflow.
