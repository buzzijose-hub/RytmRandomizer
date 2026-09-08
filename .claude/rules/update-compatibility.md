# Update compatibility — persisted operator state (mandatory rule)

**Authority:** This file + [`docs/superpowers/plans/2026-08-03-autoupdate-distribution.md`](../../docs/superpowers/plans/2026-08-03-autoupdate-distribution.md) §11 Contract A (the design source) + §5.1 (the error taxonomy) + `tests/architecture/test_persisted_state_registry.py` (mechanical enforcement) + [`rytm_randomizer/data/persisted_state.py`](../../rytm_randomizer/data/persisted_state.py) (the fact table).
**Scope:** Any PR that adds, moves, or changes the on-disk shape of **operator state written under the platform config dir** — a session, a bank, a favorites list, a captured-kit record, a profile, a show bank. Not export artifacts written to an operator-supplied `--output` path.

## The rule

The app auto-updates. That means the binary will be swapped out from
under the operator's saved state, repeatedly, without warning, on a
machine that may be on stage. **An operator's show bank outliving an
update is a product promise, not a nicety.**

The design rule that makes this survivable is deliberately inverted:
**features integrate with updating by not integrating.** The update
system has zero in-app extension points — no hooks, no per-feature
update APIs, nothing a feature can couple to or break. The entire
interface between "a new feature that saves something" and "updating" is
one declaration:

> Register your store in
> `rytm_randomizer/data/persisted_state.py` with a `schema_version`.
> The update system does the rest.

You write no migration plumbing, no version-detection code, no
compatibility shims. You declare a version and route your loader through
`classify_payload()`. That is the whole contract.

Four fail-closed rules follow from it, all implemented once in
`data/persisted_state.py` and all enforced by tests rather than by
review vigilance:

1. **Never silently reset.** An unreadable file, an unknown shape, or a
   failed migration is a *refusal* — the operator is told, and the bytes
   on disk are left exactly as found. Resetting to defaults is the one
   outcome this contract exists to forbid.
2. **Downgrade refusal.** State whose `schema_version` is **newer** than
   this build's is refused with `persisted_state.schema_newer_than_app`.
   An operator who tried a newer build and rolled back must not have
   their state truncated to whatever the older app happens to understand.
3. **A missing version field is version 1, not corruption.** Files
   written before a store adopted the envelope are legitimate v1 state.
   Treating them as corrupt would destroy exactly the state this contract
   protects.
4. **Migrations are explicit and ordered.** One `PersistedStateMigration`
   per `N -> N+1` step, no implicit or skipped steps. The chain's
   contiguity is validated at import time, so a version bump without its
   migration fails at startup rather than at an operator's first load.

## What you MUST do

1. **Add a row to `PERSISTED_STATE_STORES`** in
   `rytm_randomizer/data/persisted_state.py` naming your `store_id`,
   `schema_version`, `owner_module`, and a one-line `description`. Pick a
   bare snake_case `store_id` — it becomes a metric label and a journal
   field, so it must never be or contain a path.
2. **Source your version from the registry, never re-type it.** In your
   store module:
   ```python
   MY_STORE_ID: Final[str] = "my_store"
   MY_STORE_SCHEMA_VERSION: Final[int] = require_schema_version(MY_STORE_ID)
   ```
   `require_schema_version` raises at import time if you forgot the
   registry row — the "compile error until you register" half of the
   contract. One declaration means a bump lands in exactly one place.
3. **Stamp the envelope on every write.** Write
   `payload[PERSISTED_STATE_VERSION_FIELD] = MY_STORE_SCHEMA_VERSION`
   onto the **disk** payload. If your DTO's `to_dict()` also feeds a
   WebSocket ack, stamp a copy — adding a field to the wire payload
   changes the WS contract.
4. **Route every load through `classify_payload()`** and honour the
   returned `PersistedStateDecision`:
   - `decision.accepted` → use `decision.payload`.
   - `decision.refused` → raise a taxonomy error, count the refusal, and
     **leave the file alone**.
   Signal a read/JSON-decode failure with `readable=False` rather than
   swallowing it.
5. **Record both Gate 7 counters** at the call site (the store module is
   above the `data/` leaf boundary and may import `observability`):
   `get_metrics().record_persisted_state_migration(store, from_v, to_v)`
   on a `persisted_state.migrated` decision, and
   `record_persisted_state_refusal(store, code)` on any refusal. Both
   surface in `format_summary()`.
6. **Raise a taxonomy error with the right fingerprint** on the
   downgrade path — `persisted_state.schema_newer_than_app` — inheriting
   from `DataError` plus the stdlib exception your existing callers
   already catch.
7. **When you bump a `schema_version`, add its migration in the same
   commit.** `1 -> 2` needs a `PersistedStateMigration(1, fn, "summary")`.
   Without it the registry refuses to import.
8. **Run the guard before pushing:**
   ```bash
   python -m pytest tests/architecture/test_persisted_state_registry.py tests/test_persisted_state.py -q
   ```

## What you MUST NOT do

- **Do not reset, truncate, or delete state on a load failure.** Not "to
  recover gracefully", not "it was corrupt anyway". Refuse and report.
  This is rule 1 and it has no exceptions.
- **Do not treat a missing `schema_version` as corruption.** It is
  version 1. Every store's pre-envelope files are legitimate state.
- **Do not read state written by a newer app** by ignoring the fields you
  do not recognise. You cannot know what a future version's field means;
  guessing loses data silently, which is worse than refusing loudly.
- **Do not re-type your `schema_version` as a literal** in your store
  module. Call `require_schema_version()`. A second copy is a second
  place to forget to bump (Gate 17: no renamed-symbol forks).
- **Do not put an absolute path, a home directory, or a raw `str(err)`
  into a refusal `detail`, a log field, or an exception message.** Store
  ids, integers, and bounded codes only — the #224/#238 hygiene standard.
- **Do not add a store to `_LEGACY_UNREGISTERED_WRITERS`** in the
  architecture test to make it pass. That allowlist is empty and its
  documented goal is to stay empty; an entry needs explicit reviewer
  approval recorded in the PR body, per the standing rule for every
  drained allowlist in this repo.
- **Do not import `observability` from `data/persisted_state.py`.**
  `data/` is a strict leaf. That is why the module returns decisions
  instead of raising — the *caller* converts a refusal into a taxonomy
  error and a metric.
- **Do not build a per-feature update hook.** There are none by design.
  If your feature seems to need one, the design has gone wrong; raise it
  rather than adding a coupling point.

## When this rule applies

- Any PR adding a module that writes JSON under the platform config dir
  (`default_profiles_dir()`, `default_library_dir()`,
  `default_captures_dir()`, or a new sibling helper).
- Any PR adding a store class that the boot path in
  `cockpit/__main__.py` constructs with a config-dir helper's result —
  the dependency-injected shape `ProfileRegistry` uses. The guard detects
  this path too; being injected is not an exemption.
- Any PR changing the on-disk shape of an already-registered store
  (that is a `schema_version` bump plus its migration).
- Any PR adding a new per-platform config-dir helper — add it to
  `_CONFIG_DIR_RESOLVERS` in the architecture test in the same PR, or its
  callers become invisible to the guard.

## When this rule does NOT apply

- **Export artifacts.** A report or kit written to an operator-supplied
  `--output` path is not state the installer swaps around; the operator
  owns that file and its location. The ~60 modules under
  `cockpit/export/` and `reports/` are correctly out of scope.
- **In-memory state.** `HistoryStore` and friends do not survive a
  process restart, so an update cannot eat them.
- **Read-only consumers.** A module that reads a store to render a report
  persists nothing and registers nothing.
- **The update journal itself.** `update-journal.jsonl` is owned by the
  Rust shell (spec §5.1) and is outside the Python registry.

## Cross-references

- [`docs/superpowers/plans/2026-08-03-autoupdate-distribution.md`](../../docs/superpowers/plans/2026-08-03-autoupdate-distribution.md) §11 Contract A — the design source; §5.1 — the `persisted_state.*` taxonomy and Gate 7 counters.
- [`rytm_randomizer/data/persisted_state.py`](../../rytm_randomizer/data/persisted_state.py) — the fact table plus the pure load policy (`classify_payload`, `plan_migration`, `apply_migration_plan`).
- `tests/architecture/test_persisted_state_registry.py` — the drift guard (two detection paths, three-test allowlist ratchet, anti-vacuity pin).
- `tests/test_persisted_state.py` — the policy's behavioural suite, organised by the four rules above.
- [`.claude/rules/architecture.md`](architecture.md) — the `data/` leaf rule that forces the decision-returning shape, and the no-mutable-module-globals rule the registry's `MappingProxyType` satisfies.
- [`.claude/rules/coverage-gate-100pct.md`](coverage-gate-100pct.md) — Gate 1; the policy module carries 100% branch coverage.
- `rytm_randomizer/observability/metrics.py` — `record_persisted_state_migration` / `record_persisted_state_refusal` and their `format_summary()` lines.
