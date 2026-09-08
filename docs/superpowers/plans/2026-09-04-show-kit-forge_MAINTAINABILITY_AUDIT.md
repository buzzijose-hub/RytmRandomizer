# Show Kit Forge maintainability audit

> Status: in-flight — baseline recorded before comprehensive closeout

Scores use 1 (high risk) through 5 (low risk). This is the Gate 14 starting
point for `2026-09-04-show-kit-forge.md`; its paired report records the final
comparison after code and review gates finish.

| Gate 14 question | Score | Required response |
| --- | ---: | --- |
| Onboarding curve | 3 | Put the complete paired workflow in one Cockpit panel, Quickstart section, architecture section, and exact studio checklist. |
| Naming hygiene | 3 | Keep candidate, live-unsaved, favorite, save attestation, verified recapture, and current show-ready authority distinct in code and copy. |
| Coupling / module boundaries | 3 | Compose capture, `MutationScope`, history, stage, send-plan, ArmedApply, device codecs, and atomic writers; add no sender, device registry, or package-root hierarchy. |
| Magic numbers / strings | 3 | Pin the A4 offset/stride/Q8.8 evidence in the device strategy and expose lifecycle/preset/wire values as `Final` or `Literal` contracts. |
| Configuration vs convention | 4 | Resolve local roots through existing bootstrap configuration; accept only bounded filename-safe ids over WebSocket and no client paths. |
| Test maintainability | 3 | Share paired capture/model fixtures, use intent-named boundary tests, and serialize resource-heavy suites. |
| Build / dev loop friction | 4 | Preserve `just check`/`just review`; use focused Python and frontend loops before the serialized full gates. |
| Error messages | 3 | Refuse stale captures, unsafe imports, corrupt packs, unsupported A4 fields, and unconfirmed Rytm sends at the authority boundary with recovery text. |
| Versioning / release | 4 | Version show-bank/show-pack schemas without changing package version, hardware-pinned dependencies, or V1.34 output. |
| Future-proofing | 3 | Keep device-specific semantics behind registered codecs/strategies so another verified field does not widen A4 authority implicitly. |

The highest starting risks are truth persistence across restart/import, atomic
paired evidence publication, fresh-capture identity, and a second SEND UI that
could drift from the reviewed `ActionBar` contract. They are blocking inputs to
the implementation and multidimensional review, not deferred enhancements.
