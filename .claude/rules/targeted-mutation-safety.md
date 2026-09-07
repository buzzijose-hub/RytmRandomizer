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
6. An A4 field may produce offline captured-kit candidate bytes only after its
   exact offsets, encoding, per-track stride, fixture-backed byte isolation,
   checksum, and re-decode evidence are promoted. Promotion is field-specific:
   it grants no A4 SEND and no authority for neighboring parameters. Never
   infer saved-kit offsets from live CC facts.
7. Favorite recapture must be newer than its manual-save attestation, and a
   show-time capture must be newer than the recapture and prior preflight. A
   persisted readiness record is historical after restart. Imported packages
   are codec-verified catalog evidence and cannot lend their candidates to a
   hardware sender.
8. Paired Rytm/A4 evidence is published atomically; a manifest cannot claim a
   verified pair while only one capture is durable.
9. V1.34 fixtures are never regenerated for targeted Cockpit work, and ordinary
   CLI/Cockpit composition remains passive unless an explicit armed boundary is
   constructed.
10. A current-KIT dump cannot prove unsaved RAM restoration. Each live Show
    Forge audition requires an explicit manual source reload and a fresh exact
    source capture after any preceding send attempt or disconnect. Source
    removal invalidates every prepared candidate derived from that source.
11. Favorite destination slots cannot overwrite immutable source slots. A
    fully locked partner is an exact source clone; its verification compares
    the complete payload rather than an empty semantic subset.
12. Imported field labels and offsets are claims, not calibration authority.
    Derive comparison offsets from canonical calibration facts and use exact,
    context-independent fixed-point conversion.
13. Offline A4 preparation cannot confer output authority. Revalidate retained
    bytes and current context on every request, and revoke stale UI reports
    after capture, candidate, scope, cue or session changes. Live transport and
    recovery require their own evidence; saved-KIT encoding is not a substitute.

See `.claude/skills/learned/targeted-live-kit-mutation/SKILL.md` for the focused
implementation and verification workflow.
