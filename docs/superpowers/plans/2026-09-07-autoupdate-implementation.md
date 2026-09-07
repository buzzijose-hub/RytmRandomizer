# Auto-update implementation plan

Date: 2026-09-07
Status: proposed (awaiting kickoff)
Base: `modularize-v1.34`
Design source of truth: [`2026-08-03-autoupdate-distribution.md`](2026-08-03-autoupdate-distribution.md)
(the spec; this plan never restates its contracts — section references
below point into it). Diagram: `docs/ARCHITECTURE_DIAGRAMS.md` §37.

## Execution shape — three PRs, one external follow-up

The spec's six workstreams collapse into three non-stacked PRs against
`modularize-v1.34` (cascade-merge rule: bundle where units are
coupled; keep PRs independent where they are not), plus U6 which waits
on the certificate purchase and gets its own PR when that lands.

```
PR-A  (U1 + U2)   repo/CI/Python — version spine, release train, contracts
        │
        ├────────────► PR-B  (U3 + U4)  Rust shell updater + cockpit UX
        │                     │
        └────────────► PR-C  (U5)  e2e, ping assets, snapshot, dashboard
                              (starts after A; its client-flow specs need B)
```

Each PR carries the standard 18-gate body, 100% branch coverage on
touched production files, and the drift guards that already run
(version ratchet, plan-index, all-workflow pin scan) must stay green
throughout — PR-A deliberately flips the version guard from ratchet
mode to full mode by creating `VERSION`.

## Maintainability & reuse contract (binding on every agent)

A maintainability review of this plan found four seams where eleven
parallel agents would naturally fork logic. Each is now a named
single-source abstraction; every agent's DoD includes "no fork —
including renamed-symbol forks (Gate 17) — of R1–R5."

| # | Abstraction | Single home | Who reuses it |
|---|---|---|---|
| R1 | Release toolkit: SemVer parse/compare, `VERSION` read, manifest schema + `validate()` + `generate()` | `scripts/release_lib.py` (importable, unit-tested; scripts stay thin CLIs over it) | `sync_version.py`, `prepare_release.py`, `validate_manifest.py`, release.yml verify-tag + manifest jobs, promote.yml, manifest-validate.yml — SemVer logic exists exactly once in Python |
| R2 | Cross-language contract fixtures: the I3 valid manifest, an invalid-manifest corpus, and bucketing test vectors | `tests/fixtures/update_manifest/` | Python validator tests, Rust serde/policy tests, TS e2e mocks — one truth, three languages, zero per-language re-typing; every invalid fixture must be rejected by BOTH the Python validator and Rust serde |
| R3 | Updater split: pure policy core `(state, event, config) → (state, effects)` + journal writer + thin I/O driver | `desktop/shell/src/{update_policy.rs, update_journal.rs, updater.rs}` | policy tests enumerate the closed vocabulary exhaustively with zero network/Tauri mocking; the driver interprets effects and stays thin |
| R4 | One TS protocol module for the I2 event + I8 row shapes | `desktop/web/src/updateProtocol.ts` | store slice, chip, panel, e2e specs — no inline re-declaration of either shape anywhere |
| R5 | Workflow logic lives in scripts, YAML orchestrates | `scripts/*.py` via R1 | any workflow step beyond ~10 lines of shell must be a tested script; the three manifest-validation sites are three one-line invocations of the same validator |

Two existing abstractions are reaffirmed as the only extension points
(not new work, but agents must route through them): the
persisted-state registry (spec §11 Contract A) for any store, and the
`PanelSpec` generic renderer for the panel — **the activity list
reuses the existing operator-log list component**; a second
journal-list component is the fork R4 exists to prevent.

R1's generator must round-trip its own validator in-process
(generate → validate before any commit), so the pipeline can never
publish a manifest its own gate would refuse.

## PR-A — version spine + release train (U1 + U2)

**Scope (Python / CI / docs only; no Rust, no TS):**

1. `VERSION` file at repo root, initial content `1.34.0` (matching
   today's pyproject truth; the first cut release bumps from here).
2. `pyproject.toml` → `dynamic = ["version"]` +
   `[tool.setuptools.dynamic]`; delete the duplicate declaration.
3. `scripts/release_lib.py` (R1) + `scripts/sync_version.py` — idempotent writer for `Cargo.toml`,
   `tauri.conf.json`, `package.json` (all move 0.1.0 → 1.34.0 in this
   PR); `just version-sync` target.
4. `scripts/prepare_release.py` — bump derivation from conventional
   commits (spec §2.4), changelog generation, release-PR body.
5. `rytm_randomizer/__version__` via `importlib.metadata` with
   `VERSION` fallback; `session_status.app_version` in the WS
   bootstrap (+ regenerated `live_gui_protocol.ts`; the web store
   exposes it read-only — no UI yet, that is PR-B).
6. `data/persisted_state.py` registry + its architecture test
   (spec §11 Contract A); register the existing config-dir writers
   (session store, library store, profile registry, show-bank store
   when merged); drainable allowlist for any legacy writer without a
   `schema_version`, goal empty.
7. `.claude/rules/update-compatibility.md` (spec §11 propagation).
8. Workflows: `installers.yml` → `workflow_call` conversion;
   `release.yml` (verify-tag → shared build → updater-sign →
   changelog → Release publish → `beta.json` commit); `promote.yml`
   (environment `stable-promote`); `manifest-validate.yml`;
   `test_ci_workflow.py` scope map (spec §9.2 — the pin-scan widening
   already landed with the spec PR).
9. Manifest schema fixture + invalid corpus + bucket vectors
   (`tests/fixtures/update_manifest/`, R2) + the R1 validator
   consumed by all three workflow validation sites.
10. `releases` branch bootstrap (empty manifests + README stub).

### PR-A pipeline work package (A5, execution-ready)

Grounded in the current tree (verified 2026-09-07): `test.yml`
triggers on **unfiltered** `push:`, and `installers.yml` already owns
`push: tags: v*` + `workflow_dispatch` with `permissions: contents:
read`. Both facts force specific edits below.

1. **`installers.yml` → reusable build.** Add a `workflow_call:`
   trigger with inputs `{sign: bool = false, updater_artifacts: bool
   = false, ref: string = ''}` and job outputs naming the produced
   artifacts. **Remove the `push: tags: v*` trigger** — once
   `release.yml` owns tags, keeping it would double-build every
   release. Keep `workflow_dispatch` as the standing no-tag rehearsal
   (its header already calls it the "manual release dry-run").
   Existing `permissions: contents: read` and setup-python pip caching
   stay (the invariants test enforces caching on every setup-python
   step in every workflow once the scope map lands).
2. **`release.yml`** — `on: push: tags: ["v*"]` + `workflow_dispatch`
   with a `dry_run` input; `concurrency: release` (no
   cancel-in-progress); top-level `permissions: contents: write`.
   Jobs: `verify-tag` (tag == `VERSION` at the tagged commit, ancestor
   of `modularize-v1.34`) → `build` (`uses:
   ./.github/workflows/installers.yml` with `sign` derived from
   secret presence, `updater_artifacts: true`) → `publish`
   (signature step no-ops without the keypair secret and the release
   is created as an **unsigned draft** — the fork-safe degrade that
   keeps the train testable before operator action #1) → `changelog`
   → `manifest` (generate `beta.json` + upload the §6 ping assets;
   under `dry_run`, manifests become run artifacts instead of a
   `releases`-branch commit). Every job writes its §9.7 step summary.
3. **`promote.yml`** — `workflow_dispatch` inputs `{version,
   rollout_percent}`; `environment: stable-promote`; `permissions:
   contents: write`; validate-with-the-fixture-schema **before**
   committing `stable.json`; shares the `release` concurrency group so
   a promote never races a release.
4. **`manifest-validate.yml`** — `on: push: branches: [releases]`;
   `permissions: contents: read`; runs the Python validator; the step
   summary names the failing rule (spec §9.7).
5. **`fleet-snapshot.yml`** — `schedule: cron "0 */6 * * *"`;
   `permissions: contents: write`; reads the Releases API with the
   default token, appends the I5 row, **skips the commit when counts
   are unchanged** (no noise commits), and never opens issues on
   failure — a red run + summary is the alert.
6. **`test.yml` edits (two, surgical):** add `branches-ignore:
   ["releases"]` to the `push:` trigger (spec §9.6 cost containment —
   today an unfiltered push trigger would run the full suite on every
   manifest commit), and nothing else: PR-event behavior, the weekly
   schedule, and the `required-checks` aggregate are untouched, which
   the scope-map update to `test_ci_workflow.py` asserts explicitly.
7. **Invariants compliance:** the widened pin scan (already live)
   covers any install lines the new workflows add; the scope map
   registers all five workflows with their exemption class
   (tag/dispatch/schedule/branch-push — none joins `required-checks`);
   every new workflow file must `yaml.safe_load` cleanly under the
   existing loader the invariants test uses.

**Verification recipe:**
`pytest tests/architecture/ -q` (version guard now in full mode);
`pip install -e .` clean under dynamic version; `python -m
rytm_randomizer.cli --help` unchanged bytes except any version line;
a `release.yml` `workflow_dispatch` dry run produces the full train
(unsigned draft + manifest artifacts) with **exactly one** build
firing (proves the installers tag-trigger removal — no double-fire);
a push to a scratch `releases` branch triggers `manifest-validate.yml`
and does NOT trigger `test.yml`; `manifest-validate.yml` refuses a
deliberately malformed fixture; every new workflow's `permissions:`
block matches spec §9.4's least-privilege table.

**Watch-outs:** editable installs + `importlib.metadata` staleness
(the fallback covers source checkouts); pyproject line ~305's
duplicate is load-bearing for nothing (verify with a grep for
consumers before deletion); `tauri.conf.json` version participates in
bundle identity — confirm `installers.yml` artifacts still build.

## PR-B — shell updater + cockpit UX (U3 + U4)

**Scope (Rust + TS; no Python beyond the PanelSpec builder):**

1. `desktop/shell`: `tauri-plugin-updater` dependency; `updater.rs`
   implementing the §5 state machine — consent tokens (per-version,
   process-lifetime), bucketing (§5, vector-tested), freeze mode
   (zero-network, call-count-asserted), manifest fetch + serde
   validation (§4 rules incl. host pinning), eager download/stage,
   install-now and install-on-quit wired into the existing
   graceful-shutdown sequence, fire-and-forget ping GET (§6).
   Public key lands in `tauri.conf.json` only after the operator
   action item below; until then the updater runs in
   check-and-notify-only mode (structurally cannot install unsigned).
2. **Absorbs the standing follow-up:** shell re-injects the fresh WS
   token into the live webview after a sidecar restart.
3. Shell → webview state bridge (one typed event, mirroring the
   existing injection pattern).
4. Cockpit: header chip + `PanelSpec`-driven update panel (§7),
   announcer integration, freeze toggle, dev-loop fallback copy,
   maintainer dashboard link; axe floor 0; vitest at the 100%
   thresholds.

**Verification recipe:** `cargo test` (consent invariant: install
entry unreachable without a version-bound token; token for A refuses
B; bucketing vectors; freeze zero-network + `freeze_suppressed` row;
manifest refusals; the §5.1 journal contract — one row per transition,
closed vocabulary, path-injection probe proving bounded details,
rotation caps);
`npx vitest run --coverage`; `npm run lint`; `tsc`; manual
`cargo run` against a local mock manifest via
`RYTM_RAND_UPDATE_MANIFEST_URL`.

**Watch-outs:** updater artifacts require `createUpdaterArtifacts` in
the bundler config — coordinate with `installers.yml` (PR-A owns the
workflow; PR-B flips the bundler flag and PR-A's shared build must
tolerate its absence until then); the #238 lesson — nothing in the
panel may transmit on mount before the WS handshake completes.

## PR-C — e2e, fleet, dashboard (U5)

**Scope:**

1. Playwright mock-manifest fixture (static server, ephemeral port)
   + the seven §8 e2e specs asserting the spec §7.1 labels and
   default selection (I9) (chip, staged, consent persistence,
   skip-version, freeze silence, bucket boundary via test-only
   forced id, hardware-reval banner, ping independence).
2. `release.yml` gains the per-OS one-byte ping assets (§6).
3. `fleet-snapshot.yml` (cron) + `fleet-history.json` writer +
   schema check in `manifest-validate.yml`.
4. `index.html` dashboard on the `releases` branch (§6.1) + the
   fixture-driven render check.

**Verification recipe:** `npm run e2e` full suite green (the existing
20+ specs must not regress — port discipline per §9.5); snapshot
script against the fixture Releases-API payload; dashboard render
check against synthetic history.

## Operator action items (cannot be done by an agent)

| # | Action | Needed by | Notes |
|---|---|---|---|
| 1 | Generate the Tauri updater keypair; store private key + password as repo secrets | PR-B install mode (PR-A's signing step no-ops without it) | one-time; public key committed in PR-B |
| 2 | Create the `stable-promote` environment with required-reviewer protection | PR-A (`promote.yml` references it) | repo Settings → Environments |
| 3 | Protect the `v*` tag pattern (maintainers only) | PR-A | Settings → Tags |
| 4 | Enable GitHub Pages serving the `releases` branch | PR-C dashboard | Settings → Pages |
| 5 | U6: purchase Apple Developer + Windows signing certificate | U6 only | the program's single money item (spec §0.2) |

## Parallel execution model

Per `.claude/rules/maximize-parallelization.md` and the
`parallel-agent-bundle` skill: development is **maximally parallel from
T0**; only the *merge train* is serial (A → B → C, one at a time per
the cascade discipline). Nothing in B or C waits for A's code — every
cross-track dependency is a spec-fixed interface, pre-declared below,
so no agent ever consumes another agent's output.

### Pre-declared interface contracts (frozen before any agent starts)

| # | Contract | Producer | Consumers |
|---|---|---|---|
| I1 | `session_status.app_version: str` (strict SemVer) | A3 | B-web |
| I2 | Shell→webview event `rytm-update-state`: `{state, version, notes, hardware_revalidation, error_code}` with `state` ∈ the §5 vocabulary | B-rust | B-web |
| I3 | Manifest schema fixture at `tests/fixtures/update_manifest/manifest.v1.json` (spec §4 verbatim) | A5 | B-rust serde tests, C-e2e mock, C validator |
| I4 | Env vars exactly as spec §7 | spec | A, B, C |
| I5 | `fleet-history.json` row: `{date, counts: {version: {os: n}}, stable: {version, rollout_percent}, beta: {version, rollout_percent}}` | C-snap | C-dash |
| I6 | Ping asset naming `beacon-<version>-<target>.txt` (spec §6) | A5 | B-rust, C-snap |
| I7 | `rytm_randomizer/_version.py::__version__` accessor | A1 | A3 |
| I8 | Update-journal row `{ts, event, version, detail}` with the spec §5.1 closed event vocabulary; file `update-journal.jsonl`, 2-generation rotation | B-rust | B-web (activity list), C-e2e (row assertions), Doctor export |
| I9 | Consent-prompt UX: spec §7.1 mockup is normative — labels, element order, default radio (`When I quit the app`), and the five body variants, verbatim | spec §7.1 | B-web (renders it), C-e2e (asserts its exact labels + default selection) |

### Orchestrator-reserved files (no agent may touch these)

`docs/STATUS.md`, `docs/superpowers/plans/INDEX.md`, `README.md`,
`docs/ARCHITECTURE.md` §2 rows, `docs/ARCHITECTURE_DIAGRAMS.md`,
`rytm_randomizer/help_text.py` + `tests/fixtures/cli_help_expected.txt`,
`data/__init__.py`. The orchestrator writes each exactly once at
integration time — this converts the highest-collision files of every
past cascade from N-way keep-both conflicts into a single authored
edit.

### Agent dispatch matrix — PR-A (six agents, one integration)

| Agent | Owned files (disjoint) | Interface produced |
|---|---|---|
| A1 version-spine | `VERSION`, `pyproject.toml`, `scripts/sync_version.py`, `Justfile`, `rytm_randomizer/_version.py`, the three synced manifests | I7 |
| A2 release-prep | `scripts/prepare_release.py`, its test file | — |
| A3 app-version | `cockpit/ws/` bootstrap field, regenerated `live_gui_protocol.ts`, store read-only slice, their tests | I1 (consumes I7 as a frozen import path, not A1's output) |
| A4 persisted-state | `data/persisted_state.py`, its arch test, `.claude/rules/update-compatibility.md`, `schema_version` registrations in the existing store modules, typed `persisted_state.*` taxonomy errors + `record_persisted_state_migration` metrics (spec §5.1, Gate 7) | — |
| A5 workflows | the full pipeline work package below (`installers/release/promote/manifest-validate` + the two `test.yml` edits), `test_ci_workflow.py` scope map, schema fixture + Python validator | I3, I6 |
| A6 branch-bootstrap | `releases` branch content only (no main-branch files) | — |

All six run concurrently in one worktree-per-agent
(`parallel-agents-need-git-worktrees`); the orchestrator integrates,
authors the reserved-file edits once, runs the full gate stack, and
opens PR-A. Known cross-scope seam: A4 touches store modules that no
other A-agent owns — verified disjoint.

### Agent dispatch matrix — PR-B (two agents, T0 start)

| Agent | Owned files | Contract |
|---|---|---|
| B-rust | `desktop/shell/**` (the R3 three-module split — update_policy.rs / update_journal.rs / updater.rs — the §5.1 update journal with rotation + bounded path-free details, sidecar token re-injection, conf) | produces I2 + I8; consumes I3 fixture verbatim from the spec, not from A5's branch |
| B-web | `desktop/web/src/**`, `desktop/web/tests/**` (`updateProtocol.ts` (R4), chip + panel rendering the spec §7.1 mockup verbatim (I9), journal-backed activity list via the existing operator-log list component, operator-log mirror rows for check/signature failures, store slice, axe) | consumes I1/I2/I8 as typed stubs checked against the contract table |

Both start at T0 against base; PR-B rebases once onto merged A
(expected conflicts: none — file scopes verified disjoint from all of
A except the generated protocol file, which A3 owns and B-web merely
reads; regeneration at rebase reconciles it mechanically).

### Agent dispatch matrix — PR-C (three agents)

| Agent | Owned files | Start |
|---|---|---|
| C-e2e | `desktop/web/e2e/update_*.spec.ts` + the mock-manifest fixture | T0 (mock serves I3; client-flow specs assert I8 journal rows per spec §8, marked `.fixme` until B merges — the spec files themselves are written at T0) |
| C-snap | `fleet-snapshot.yml`, snapshot script + fixture test, ping-asset step in `release.yml` (coordinated hunk — A5 leaves a marked insertion point) | T0 |
| C-dash | `index.html` dashboard + render-check test | T0 (against synthetic I5 data) |

### Effort under maximal parallelism

Wall-clock collapses from ~5 serial sessions to ~2: T0 dispatches all
eleven agents; integration+merge of A in session 1; B and C rebase,
activate, and merge in session 2. The critical path is A-integration →
merge train, not any single agent's work.

## Definition of done (program level)

- A `v1.35.0-beta.1` tag produces a signed release, a valid
  `beta.json`, and ping assets, end-to-end, with zero manual steps
  beyond the tag push.
- A promote run moves it to `stable.json` at 10%, and the dashboard
  shows the adoption curve with the promote marker after two
  snapshots.
- A dev-loop client and a bundled client both render the correct §5
  states against the mock manifest; freeze mode provably issues zero
  requests; consent invariants hold under `cargo test`.
- No fork of R1–R5 anywhere in the three PRs (Gate 17, including
  renamed-symbol forks); the R1 generate→validate round-trip runs in
  every pipeline path that writes a manifest.
- All spec drift guards green; `test_version_single_source.py` running
  in full (post-U1) mode; 18-gate bodies on all three PRs; zero new
  operational cost (§0.2 table unchanged).
- Observability floor holds end-to-end: a deliberately broken
  signature in the mock manifest produces — with no debugging — a
  `signature_rejected` journal row, an operator-log entry, a Doctor
  export containing it, and a red `manifest-validate`/e2e assertion;
  a persisted-state refusal shows up in `format_summary()`. Nothing
  in the update path can fail silently.
