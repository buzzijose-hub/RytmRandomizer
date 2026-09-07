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

## PR-A — version spine + release train (U1 + U2)

**Scope (Python / CI / docs only; no Rust, no TS):**

1. `VERSION` file at repo root, initial content `1.34.0` (matching
   today's pyproject truth; the first cut release bumps from here).
2. `pyproject.toml` → `dynamic = ["version"]` +
   `[tool.setuptools.dynamic]`; delete the duplicate declaration.
3. `scripts/sync_version.py` — idempotent writer for `Cargo.toml`,
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
9. Manifest schema fixture (`tests/fixtures/update_manifest/`) +
   Python-side validator consumed by `manifest-validate.yml`.
10. `releases` branch bootstrap (empty manifests + README stub).

**Verification recipe:**
`pytest tests/architecture/ -q` (version guard now in full mode);
`pip install -e .` clean under dynamic version; `python -m
rytm_randomizer.cli --help` unchanged bytes except any version line;
a `v1.34.1-beta.1` tag on a throwaway commit runs `release.yml`
end-to-end in a fork-safe dry mode (signing step no-ops when the
secret is absent — the workflow must degrade to unsigned-artifact +
draft-release so the pipeline is testable before the keypair exists);
`manifest-validate.yml` refuses a deliberately malformed fixture.

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
B; bucketing vectors; freeze zero-network; manifest refusals);
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
   + the seven §8 e2e specs (chip, staged, consent persistence,
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

## Sequencing & effort

PR-A first (everything keys off it; ~2 sessions). PR-B and PR-C can
start in parallel worktrees once A merges (disjoint file scopes:
Rust+TS vs e2e+workflows+branch artifacts), with PR-C's client-flow
specs landing after B merges — the fixture, snapshot, and dashboard
halves of C are A-only-dependent. Every merge follows the repo's
one-at-a-time cascade discipline; each PR is re-reviewed at its final
head per the standing review workflow.

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
- All spec drift guards green; `test_version_single_source.py` running
  in full (post-U1) mode; 18-gate bodies on all three PRs; zero new
  operational cost (§0.2 table unchanged).
