# RytmRandomizer Modularization Rules — superseded

> **Status as of 2026-05-19:** The modularization is complete. The V1.34 monolith
> (`rytm_hybrid_randomizer_v134.py`) was retired in PR #29 — its byte-for-byte
> reference behavior is now captured as 685 JSON goldens under
> `tests/fixtures/v134_parity/` and asserted by the parity tests. The
> "split the monolith" rules below no longer apply because there is no monolith.

For current contributor rules, see:

- **[`CONTRIBUTING.md`](../CONTRIBUTING.md)** — the developer handbook covering all rules: 15 strict non-negotiables, the 16 plan-requirement gates, the V1.34-parity rules, PR sizing and bundling, lint specifics, hardware-safety boundaries, etc.
- **[`docs/ARCHITECTURE.md` §5 (Parity discipline)](ARCHITECTURE.md#5-parity-discipline-v134)** — the V1.34 parity contract.
- **[`docs/PLAN_REQUIREMENTS.md`](PLAN_REQUIREMENTS.md)** — the 16 gates every PR must satisfy.
- **`.claude/rules/parity-fixture-discipline.md`** — when and how to regenerate parity fixtures.

The current "V1.34 parity" rule (every PR must keep 685/685 parity fixtures
byte-identical) is enforced by `tests/test_engines_pad*.py`,
`tests/test_group_runner.py`, and `tests/test_scene_runner.py` — captured fixtures
are at `tests/fixtures/v134_parity/`.

Historical note: This file's original rules ("split the monolithic script into
modules", "keep `rytm_hybrid_randomizer_v134.py` as the reference") drove the
Wave 1-4 modularization work that is now complete. It is kept here only as a
trail marker. Do not use it to plan new work.

## Open modularization targets (post-Wave-4)

Three known structural-debt items remain that aren't full monolith splits but follow the same "reuse the canonical surface, don't duplicate" discipline. Tracked here so they don't get lost between PRs:

- **`handlers.py` / `wizard_handlers.py` unification (IH4).** The cockpit WS dispatcher uses two `_HANDLERS` / `WIZARD_HANDLERS` dicts plus a string-prefix branch in `handlers.handle_command`. The CODE_REVIEW.md sweep scoped PR 8 to the CLI registry; the wizard-handler dispatch unification (a single registry pattern matching the `cli_registry` shape) is a follow-up. Target shape: one `WS_COMMANDS: Final[Mapping[str, Handler]]` registry, no string-prefix branch, both Phase 1 and Phase 2 commands registered through the same factory.
- **Single canonical `atomic_write` surface (C3-class).** `cockpit/export/writer.py:atomic_write` is the package's only sanctioned "durably write bytes to disk" primitive. The previous fallback in `cli.py` was deleted (PR 3); `ProfileRegistry.save` now routes through it (PR 7). The `tests/architecture/test_abstraction_reuse.py` arch test will flag any second canonical surface for `atomic_write` / `pack_signed` / similar primitives. Adding a new primitive that does its own write-temp-fsync-rename dance is a Gate 17 violation.
- **`pending_events` as a real session field, not `setattr` (H1-class).** Wire handlers that need to queue events between ack and drain MUST declare the queue as a field on the dataclass (`pending_events: list[dict] = field(default_factory=list)` on `CockpitSession`). Smuggling state via `setattr(session, "_pending_events", ...)` is forbidden by `tests/architecture/test_no_side_channel_session_attrs.py`.

When in doubt, the post-2026-05-25 architecture is: one canonical primitive per concern, frozen dataclasses everywhere on the wire boundary, narrowed Literals at every `from_dict`, and a policy-object pattern (e.g. `WizardPathPolicy`) for any wire-bound validation. See [`CONTRIBUTING.md` § Patterns introduced by the CODE_REVIEW.md sweep](../CONTRIBUTING.md#patterns-introduced-by-the-code_reviewmd-sweep-2026-05-25) for the full pattern catalogue.
