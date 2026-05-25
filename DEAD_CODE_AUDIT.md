# Dead-Code Audit — RytmRandomizer (May 25, 2026)

## TL;DR

| Category | Count | Action |
|---------|------:|--------|
| **HIGH confidence (safe to remove)** | **3** | Remove (TypeScript test fixtures) |
| MEDIUM (manual inspection) | 0 | — |
| FALSE POSITIVE (allowlist) | 17 | Document allowlist for ratchet test |
| Truly unreferenced Python top-level symbols | **0** | — |
| Orphan Python modules (zero importers) | **0** | — |
| Vulture findings on `rytm_randomizer/` (conf ≥80) | **0** | — |
| Commented-out code blocks ≥5 lines | **0** | — |

The codebase is already extremely clean. The only **HIGH confidence** dead code is in
`desktop/web/tests/cockpit/_fixtures.ts`: 3 exported symbols that no test imports.

LOC removed: **~57** (3 unused TypeScript fixtures).

---

## Methodology

Three orthogonal scans across `rytm_randomizer/` (Python source), `tests/`
(Python tests), and `desktop/web/` (TypeScript):

1. **vulture** (`--min-confidence 80`) against `rytm_randomizer/` and `tests/`.
   - `_deadcode/vulture_80.txt` (full repo: 4 hits, all unused `dst` mock params)
   - `_deadcode/vulture_80_src.txt` (src-only: **0 hits**)
   - `_deadcode/vulture_100.txt` (src-only @ conf 100: **0 hits**)
   - `_deadcode/vulture_60.txt` (full repo at lower threshold: 293 hits — almost all
     `pytestmark` false positives + signature placeholder vars)

2. **AST scan** (`_deadcode/scan_unreferenced.py`) — for each top-level public
   `def` / `class` / module-level assignment in `rytm_randomizer/`, count token
   references across all 493 `.py` files in the repo. Categorize:
   - **TRULY_UNREFERENCED** — zero token occurrences outside the definition line
   - **MODULE_LOCAL_ONLY** — referenced only inside the defining file
   - **EXTERNAL_REFERENCES** — used elsewhere (live API)

   Results: **TRULY_UNREFERENCED = 0**, MODULE_LOCAL_ONLY = 355,
   EXTERNAL_REFERENCES = 1109 (of 1464 candidates).

3. **Orphan module scan** (`_deadcode/scan_orphan_modules.py`) — for each
   non-`__init__.py` module under `rytm_randomizer/`, regex-search the repo
   for `from … <leaf> import`, `import … <leaf>`, or the fully-qualified
   dotted form.

   Results: **0 orphan modules** out of 203.

4. **ts-prune** against `desktop/web/`:
   - `_deadcode/ts_prune.txt` (131 reports — almost all barrel re-exports
     from `src/cockpit/index.ts`, `src/types/index.ts`, etc., which are
     intentional public-API surface).
   - **3 genuine unused fixtures** in `tests/cockpit/_fixtures.ts`.

5. **Commented-out-code scan** — grep for ≥5 contiguous comment lines
   containing Python keywords (`def`, `class`, `import`, `return`, etc.).
   **0 hits.**

---

## Category 1 — HIGH confidence dead code (safe to remove)

### TypeScript test fixtures (3 symbols, ~57 LOC)

`desktop/web/tests/cockpit/_fixtures.ts`:

| Line | Symbol | Type | Rationale |
|-----:|--------|------|-----------|
| 65 | `highRiskCandidate` | `MutationCandidate` const | Zero importers; `candidate` (line 24) is the one actually used in tests |
| 115 | `sceneProfile` | `ProfileModel` const | Zero importers; `profile` (line 47) is the one actually used in tests |
| 165 | `SendRecord` | `interface` | Zero importers anywhere |

Verified via:
```
grep -rn "highRiskCandidate\|sceneProfile\|SendRecord" --include="*.ts" --include="*.tsx"
  desktop/web/tests/ desktop/web/src/
```
Only matches are the definitions themselves.

**Removal: Phase 2, Commit 1.**

---

## Category 2 — Top-level unreferenced Python symbols

**Empty.** AST scan confirms zero. Every top-level public symbol under
`rytm_randomizer/` has at least one in-file reference (most are dataclass
fields, `Final` constants packaged into `_HEADER` / `_USAGE` blocks,
parse-function helpers, etc.).

---

## Category 3 — Unused TypeScript exports

131 ts-prune findings total; 128 are barrel re-exports from `src/cockpit/index.ts`,
`src/state/index.ts`, `src/types/index.ts`, `src/wizard/index.ts`. Spot-checked
several (`valueToAngle`, `INITIAL_STATE`) — they are imported directly from the
source file in tests / other source files, **not** via the barrel. The barrel
exports are intentional public-API surface and must stay.

The remaining 3 findings — `highRiskCandidate`, `sceneProfile`, `SendRecord` —
are real unused test fixtures (Category 1).

---

## Category 4 — Commented-out code blocks

**0 hits.** No blocks ≥5 contiguous comment lines that look like code.

---

## Category 5 — Private helpers without callers

Vulture at confidence 80 finds zero unused private helpers in `rytm_randomizer/`.
Two-line manual check at conf 60 turned up 4 borderline cases, all explained:

| Hit | Reason it's not dead |
|-----|---------------------|
| `cli_registry.py:195 discover_all` | Plugin discovery sweep — invoked at import time by tests that exercise the registry, but the call is inside a string-built `__import__` chain |
| `cockpit/ws/server.py:269 ws_endpoint` | FastAPI endpoint registered via decorator; never imported by name |
| `cockpit/ws/wizard_handlers.py:96 _set_path_policy` | Handler registered into the wizard handler dispatch dict — vulture can't see the dict registration |
| `observability/errors.py:165 __getattr__` | Module-level `__getattr__` is *the* lazy-attribute hook Python calls implicitly |

All four are false positives.

---

## Category 6 — Unused test fixtures

Python: 4 vulture hits, all unused `dst` parameters in mock functions whose
signature must match `os.replace(src, dst)`. These are signature placeholders,
not dead code. Renaming to `_dst` would silence vulture but is cosmetic.

TypeScript: see Category 1.

---

## Category 7 — Whole-module deletion candidates

**0 orphan modules.** Every `.py` file under `rytm_randomizer/` has at least
one external importer. Verified by `_deadcode/scan_orphan_modules.py` (17s runtime
across 203 modules × 493 files).

---

## False-positive allowlist

These symbols look unreferenced to a naive scanner but are wired in through
indirect dispatch (string keys, decorators, plugin discovery, etc.). They
must be exempted from the ratchet arch test:

```python
# (module_path, symbol_name)
_GRANDFATHERED_INDIRECT_REFERENCES = frozenset(
    {
        # ----- CLI registry (string dispatch from cli.py lazy_commands) -----
        ("rytm_randomizer/cli_registry.py", "discover_all"),
        # ----- WebSocket endpoints (FastAPI @app.websocket decorator) -----
        ("rytm_randomizer/cockpit/ws/server.py", "ws_endpoint"),
        # ----- Wizard handler dispatch (registered into dict, not imported) -----
        ("rytm_randomizer/cockpit/ws/wizard_handlers.py", "_set_path_policy"),
        # ----- Module-level __getattr__ (Python lazy-attr hook) -----
        ("rytm_randomizer/observability/errors.py", "__getattr__"),
    }
)
```

The ratchet test will instead check the **module-local-only** set (355 symbols)
to be the floor — additions must be accompanied by an explicit allowlist entry
OR a refactor to make the symbol `_private`.

---

## Recommended Removal PRs

### PR 1: Remove unused TypeScript test fixtures (this branch)
- `desktop/web/tests/cockpit/_fixtures.ts` — delete `highRiskCandidate`,
  `sceneProfile`, `SendRecord` (~57 LOC).
- Run `npx tsc --noEmit` and `npx vitest run` in `desktop/web/`.

### PR 2: Architecture ratchet test (this branch)
- Add `tests/architecture/test_no_unreferenced_top_level_symbols.py`
- Frozen baseline of 355 module-local-only symbols + 4-entry indirect-ref allowlist.
- Three-test pattern: enforce-floor + allowlist-realness + no-orphans-in-allowlist.

### PR 3 (deferred — out of scope for this audit)
The 355 module-local-only symbols could be made `_private` to enforce the
convention more strictly. That is a wide refactor (each rename touches one
file but may break external imports we missed). Recommend tackling per-module
in follow-up PRs.

---

## Architecture test recommendation

Add `tests/architecture/test_no_unreferenced_top_level_symbols.py` with
three tests (mirroring `test_plan_doc_status_truth.py`):

1. **`test_no_new_unreferenced_top_level_symbols`** — runs the AST scanner,
   asserts that any newly-introduced top-level public symbol with zero
   external references either appears in the grandfathered allowlist or
   is renamed to start with `_`.

2. **`test_grandfathered_unreferenced_set_only_contains_real_symbols`** —
   every `(module, symbol)` in the grandfather frozenset must still exist
   on disk. Catches stale allowlist entries after refactors.

3. **`test_grandfathered_unreferenced_set_does_not_have_referenced_entries`**
   — if a symbol gets a real external referrer (someone backfills the usage),
   the grandfather entry becomes redundant and must be pruned. Keeps the
   allowlist shrinking monotonically.
