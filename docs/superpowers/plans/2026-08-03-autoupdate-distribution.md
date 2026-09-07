# Auto-update: versioned, gated, fast-to-fleet distribution

Date: 2026-08-03 (completed as an implementable spec 2026-09-07)
Status: proposed (spec complete; implementation not started)
Base: `modularize-v1.34`
Driver: operator directive — installed apps must auto-update, with
version control "really good" and gated updates; the plan must
"really consider speed of distribution … how fast we can update this
app throughout the network and be aware of users and their versions —
the faster and more uniformly we can iterate."

---

## 0. Resolved decision gates

The four gates from the original proposal are resolved below with the
recommended defaults. Each is a one-line change to overturn before U1
starts; none is load-bearing for the others except D1.

| Gate | Decision | Rationale |
|---|---|---|
| **D1 — fleet awareness** | **Tier 1: edge-worker beacon** | The driver directive explicitly demands "be aware of users and their versions"; static files alone cannot answer it. The beacon is structurally incapable of gating updates (see §6) and costs one free-tier worker. |
| **D2 — check cadence** | Launch + every 4 h while running + manual "Check now" | Hours-scale worst-case T_notice with zero infrastructure; a ~1 KB CDN GET is cheap enough to be frequent. |
| **D3 — default consent affordance** | "Install on next launch" pre-selected | Fastest fleet convergence that never forces a restart on a stage machine. |
| **D4 — beta channel population** | Maintainers first (`buzzijose-hub`, `edward-rosado`); widen by invitation after two beta→stable cycles | Smallest honest test population that still exercises both OS families in daily use. |

## 0.1 Drift verification (2026-09-07)

The original proposal predates the merges of PRs #220–#237. Every
environmental claim below was re-verified against the current tree:
the bundled-sidecar entry stub is now
`rytm_randomizer.app.main(["--arm", "--cockpit-kit-capture-sidecar"])`
(PR #237; `desktop/shell/src/sidecar.rs` + shell README), the panel
platform still registers bottom-region panels beside the Connection
Doctor (`panels/registry.ts:73-75`), the shell's graceful-shutdown
sequence (stdin sentinel → SIGTERM → 5 s grace) is the hook
install-on-quit rides, `tauri.conf.json` carries no updater config yet,
the shell-side WS-token re-injection follow-up remains unimplemented
(so U3 still absorbs it), rustup is installed on the dev machine, and
the five-declaration/two-value version drift in §2 was measured, not
assumed. The Playwright e2e platform (#221) and the CLI-help parity
guard (#236) referenced below both exist as described.

## 1. Safety model: updates are a transmit-shaped problem

This application runs on stage. An updater that restarts the app
mid-set is the same class of failure as an unwanted MIDI send, so the
update system inherits the Live-but-Passive model:

| Live-but-Passive MIDI | Update analogue |
|---|---|
| Enumerating ports / opening inputs — free, ongoing | **Checking** for updates + **downloading/staging** in the background — free, ongoing |
| Transmit — armed, per-action confirm | **Installing** — explicit operator consent, never automatic |
| Arming never survives reconnect | Consent is **per-version**; an accepted update never auto-installs after a crash loop, and a new version voids prior consent |
| `RYTM_RAND_MIDI_BACKEND=off` escape hatch | **Freeze mode**: `RYTM_RAND_UPDATES=off` (env) or the in-UI "Freeze updates (performance mode)" toggle — no check, no download, no chip |

Derived rule — the single biggest speed lever available to a
consent-gated updater: **download eagerly, install consensually.** The
artifact is staged and signature-verified before the operator ever
sees the "update ready" chip, so consent costs one restart, never a
download wait.

**Enforced invariant (not prose):** no code path may invoke the
install/restart step without a consent token minted by an explicit UI
action in the current process lifetime. Pinned by Rust unit tests in
the shell (§8) the same way `KitMutationUnsupportedError` pins the kit
seam.

## 2. Version spine — one source of truth, mechanically enforced

Current reality (measured 2026-09-07): **five version declarations,
two values** — `pyproject.toml` says `1.34.0` twice (lines 7 and 305),
while `desktop/shell/Cargo.toml`, `desktop/shell/tauri.conf.json`, and
`desktop/web/package.json` all say `0.1.0`. This is the drift the
spine eliminates.

1. **Canonical home: `VERSION` at the repo root** — single line,
   strict SemVer (`MAJOR.MINOR.PATCH` with optional `-beta.N`).
2. **Derivations:**
   - `pyproject.toml`: `dynamic = ["version"]` +
     `[tool.setuptools.dynamic] version = {file = "VERSION"}` — and the
     second in-file copy (line ~305) is deleted, not synchronized.
   - `Cargo.toml` / `tauri.conf.json` / `package.json`: updated by
     `scripts/sync_version.py` (idempotent; run by the release
     workflow and by a new `just version-sync` target), and **checked, not
     trusted**, in CI.
   - Runtime: `rytm_randomizer/__version__` read via
     `importlib.metadata` with a `VERSION`-file fallback for source
     checkouts; the WS bootstrap `session_status` payload gains
     `app_version: str` so both halves of a running install can state
     their version (consumed by diagnostics, the beacon, and the
     update panel).
3. **Drift guard:** new
   `tests/architecture/test_version_single_source.py` asserts (a)
   `VERSION` parses as strict SemVer, (b) all four derived files equal
   it exactly, (c) exactly one `version =` occurrence remains in
   `pyproject.toml`. Red CI on any drift — the repo's standard move.
4. **Version bumps are derived, never hand-authored.** Feature PRs do
   not touch `VERSION` or any derived file — ever. A `cut-release`
   `workflow_dispatch` (or `scripts/prepare_release.py` locally) derives
   the bump level from conventional commits since the last tag
   (`BREAKING CHANGE:`/`!` ⇒ MAJOR, `feat:` ⇒ MINOR, else PATCH),
   writes `VERSION`, runs `sync_version.py`, generates the changelog,
   and opens the release PR. The drift guard makes a hand-edit that
   forgets a derived file fail CI; release-prep is the only sanctioned
   editor.
5. **Tag-driven releases.** Pushing tag `vX.Y.Z` (protected pattern,
   maintainers only) is the ONLY way a release exists. The release
   workflow refuses unless the tag name matches `VERSION` at the
   tagged commit AND the commit is an ancestor of the integration
   branch. Pre-release tags (`v1.35.0-beta.1`) flow to the beta
   channel only.
6. **Changelog from conventional commits** (already house style):
   generated per release, committed as the release notes body, and
   excerpted into the manifest `notes` field the operator sees before
   consenting. `BREAKING CHANGE:`/`!` ⇒ MAJOR.
7. **Hardware-revalidation flag.** The release workflow derives
   `hardware_revalidation: true` when the diff since the previous tag
   touches any of: `rytm_randomizer/engines/`, `rytm_randomizer/senders/`,
   `midi_io.py`, `real_midi_adapter.py`, `mido_provider.py`,
   `tests/fixtures/v134_parity/`, or the pinned `mido`/`python-rtmidi`
   versions — OR the tag annotation contains `[hw-reval]`
   (conservative OR; there is no way to force it false when the paths
   say true). The path list lives once in `scripts/release_paths.py`,
   imported by both the workflow and a new architecture test that
   asserts it is a **superset** of the transmit-allowlist modules and
   the parity-fixture root — so when a future feature widens the wire
   surface, the release flag follows automatically instead of rotting.
   The update UI surfaces the flag loudly (§7).

## 3. Distribution architecture — static files, no servers we operate

- **Transport: `tauri-plugin-updater` v2.** The shell owns
  check/download/verify/stage/install (it must — it swaps the bundle).
  The web UI never performs update I/O; it renders state the shell
  publishes (§7).
- **Artifact host: GitHub Releases** (global CDN, permanent retention
  of old installers = the recovery path).
- **Integrity: Tauri updater Ed25519 signatures** on every artifact,
  independent of OS code signing and available today, before
  certificates. Private key only in Actions secrets
  (`TAURI_SIGNING_PRIVATE_KEY` + password); public key embedded in
  `tauri.conf.json` `plugins.updater.pubkey`. An artifact that fails
  verification is discarded and the failure is journaled to the
  Connection Doctor — never silently retried into oblivion.
- **Channel = manifest file.** `stable.json` and `beta.json` on the
  dedicated `releases` branch, fetched raw. Promotion and rollback are
  both one-line, reviewable, revertable Git commits; rollback =
  re-point `stable.json` at the previous release (clients that already
  updated stay put; clients that haven't never see the bad version).
- **Atomic app+sidecar.** The PyInstaller sidecar ships inside the
  bundle (entry stub pinned to
  `rytm_randomizer.app.main(["--arm", "--cockpit-kit-capture-sidecar"])`
  since PR #237), so shell and engine update as one artifact — version
  skew between halves is structurally impossible; the pinned WS
  subprotocol remains the belt-and-suspenders guard.

## 4. Manifest schema (v1)

One JSON document per channel:

```json
{
  "schema_version": 1,
  "channel": "stable",
  "version": "1.35.1",
  "pub_date": "2026-09-14T00:00:00Z",
  "notes": "markdown excerpt of the generated changelog",
  "hardware_revalidation": false,
  "rollout_percent": 100,
  "minimum_version": null,
  "platforms": {
    "darwin-aarch64": { "signature": "<minisign>", "url": "https://github.com/…/releases/download/v1.35.1/….app.tar.gz" },
    "darwin-x86_64":  { "signature": "…", "url": "…" },
    "windows-x86_64": { "signature": "…", "url": "…-setup.nsis.zip" },
    "linux-x86_64":   { "signature": "…", "url": "….AppImage.tar.gz" }
  }
}
```

Validation rules (client-side, fail-closed):

- `schema_version` must equal a version the client understands;
  otherwise the check result is "manifest not understood" (journaled),
  never a best-effort parse.
- `version` strict SemVer; the client acts only when it is **newer**
  than the running version (rollback is served by the manifest
  pointing at an older-than-latest release for *not-yet-updated*
  clients, never by client-side downgrade).
- `url` must be `https://github.com/<owner>/<repo>/releases/download/…`
  — any other host is refused.
- `rollout_percent` integer 0–100; missing ⇒ 100.
- `minimum_version` is **advisory-banner-only** in v1 (reserved; making
  it blocking is a deliberate future decision, not a hotfix).
- Unknown top-level keys are ignored (forward compatibility);
  `schema_version` gates interpretation.
- The manifest schema is pinned by a fixture + a Rust serde round-trip
  test AND a Python-side fixture validator, so both consumers drift
  together or fail loudly.

## 5. Update state machine (shell-owned)

```
idle ──check──▶ checking ──none──▶ up_to_date ──4h/manual──▶ checking
                  │
                  ├─manifest invalid/unreachable──▶ check_failed (journal; retry next cadence)
                  ▼
            update_available ──eager──▶ downloading ──verify──▶ staged
                  │                        │
                  │                        └─sig/IO fail──▶ stage_failed (journal)
                  ▼
   (bucket ≥ rollout_percent ⇒ treated as up_to_date this cycle)
staged ──chip visible──▶ consent{ install_now | install_on_quit(default) | skip_this_version }
   install_now      ──▶ installing ──▶ restart into new version
   install_on_quit  ──▶ installs at natural exit (choice persisted for THIS version only;
                        runs only after the shell's existing graceful-shutdown
                        sequence — stdin sentinel, SIGTERM, 5 s grace — has
                        confirmed the sidecar exited, never concurrently with it)
   skip_this_version──▶ suppress chip for this version (persisted; cleared by any newer version)
```

- **Freeze mode** short-circuits before `checking`: no network I/O of
  any kind, chip never renders.
- **Rollout bucketing (serverless, uniform):** `bucket = first 4 bytes
  of SHA-256(install_id) as big-endian u32, mod 100`; take the update
  iff `bucket < rollout_percent`. Stable per install — nobody flaps in
  or out as the percentage rises; every step is a superset of the
  last.
- `install_id`: UUIDv4 minted on first launch, stored in the config
  dir, never regenerated, zero PII (exists so the fleet histogram can
  distinguish 1 user checking hourly from 24 users).
- Consent tokens are process-lifetime and version-bound: a crash after
  consent does NOT auto-install on next start (mirrors never-auto-re-arm).

## 6. Fleet awareness — the beacon (D1: Tier 1)

- **Endpoint:** `GET /check?channel=<c>&v=<running>&os=<target>&id=<install_id>`
  on a Cloudflare Worker (free tier). It logs the tuple + timestamp
  and returns **302 → the raw manifest URL** (or 200-proxies it).
- **Structurally unable to gate:** the client treats any non-200/302,
  timeout > 3 s, or malformed response as "use the raw CDN URL
  directly." Update availability NEVER depends on the beacon; killing
  the worker in e2e must leave every update path green (§8).
- **Privacy:** the tuple above is the entire payload. Opt-outs:
  `RYTM_RAND_UPDATES=off` (no traffic at all) and
  `RYTM_RAND_UPDATE_BEACON=off` (check via raw CDN, report nothing).
  One README paragraph states exactly this.
- **Output:** version histogram over time per channel/OS with
  rollout-percent overlays — the direct measure of "how fast and
  uniformly we iterate." Worker analytics first; a small dashboard
  page only if it earns its keep.

## 7. Cockpit UX

- **Header chip** `⬆ 1.35.1 ready` — icon + shape + text (colorblind-
  safe per the a11y standard), announced once via the global announcer,
  hidden in freeze mode, persistent but calm until acted on.
- **Update panel** — a `PanelSpec` entry in the bottom region beside
  the Connection Doctor (registry row + generic renderer; no bespoke
  React): running version (`session_status.app_version`), channel
  selector (stable/beta), staged-update changelog, the
  `hardware_revalidation` banner when flagged (names the manual
  validation doc), the three consent actions, "Check now", the freeze
  toggle, and last-check/last-beacon timestamps (honesty about what
  phoned home).
- **Failure honesty:** signature/download/manifest failures appear in
  the Connection Doctor journal with bounded, path-free messages (the
  #224/#238 hygiene standard).
- **Dev loop:** in the two-terminal browser loop there is no shell, so
  the panel renders "updates run in the installed app" — never a
  broken control.
- **A11y:** axe floor 0 for panel and chip; keyboard operable;
  state-change announcements via the announcer; no live-region
  countdown spam (the OfflineShell precedent).
- **Env surface (documented per Gate 13):** `RYTM_RAND_UPDATES=off`,
  `RYTM_RAND_UPDATE_BEACON=off`, `RYTM_RAND_UPDATE_CHANNEL=<c>` (dev
  override), `RYTM_RAND_UPDATE_MANIFEST_URL=<url>` (e2e/mock only).

## 8. Test & enforcement spec

Architecture tests (new):
- `test_version_single_source.py` — §2.3.
- `test_update_env_documented.py` — the four env vars appear in the
  README/quickstart env tables (extends the existing Gate 13 pattern).

Rust unit tests (shell):
- consent invariant: the install entry point is unreachable without a
  version-bound consent token; a token for version A refuses version B.
- bucketing: SHA-256 vector tests pinning exact bucket values for
  known ids; boundary at `bucket == rollout_percent` excluded.
- manifest validation: schema fixture round-trip; wrong host refused;
  unknown `schema_version` refused; signature-verify failure surfaces
  as journal event, not retry loop.
- freeze mode: zero network calls (mock transport asserts call count 0).

Playwright e2e (the #221 platform; new fixture: a local static
manifest server wired via `RYTM_RAND_UPDATE_MANIFEST_URL`):
- chip appears when the mock manifest advertises a newer version;
  absent when equal/older.
- staged-download state renders; consent `install_on_quit` persists
  for that version and is voided by a newer manifest.
- `skip_this_version` suppresses the chip until the version changes.
- freeze mode: no chip, and the mock server logs **zero** requests.
- rollout boundary: forced `install_id` (env override, test-only) at
  bucket 99 vs `rollout_percent: 50` sees no update; at 100 sees it.
- beacon-down fallback: beacon URL pointed at a dead port; update
  still found via CDN URL.
- `hardware_revalidation: true` renders the banner naming the manual
  validation doc.

CI: `release.yml` (push `v*` tags) — verify-tag → 3-OS build matrix
(reusing the installers.yml build steps) → updater-sign → changelog →
GitHub Release publish → generate + commit `beta.json`.
`promote.yml` (workflow_dispatch, environment `stable-promote` with a
required human approval) — copy beta manifest → `stable.json` at a
chosen `rollout_percent`. Both workflows follow the
ci-workflow-invariants skill; neither joins `required-checks` (they are
not PR-event jobs), stated here so the aggregate's drift guard is not
"fixed" to include them.

## 9. Workstreams, acceptance criteria, sequencing

| WS | Scope | Acceptance criteria | Depends on |
|---|---|---|---|
| **U1 — version spine** | `VERSION`, derivations, `sync_version.py`, drift-guard test, `app_version` in session_status; `data/persisted_state.py` registry + its arch test; `.claude/rules/update-compatibility.md` | arch tests green; one `version =` left in pyproject; every existing config-dir writer registered with a `schema_version`; the rule file lands with the registry | — |
| **U2 — release pipeline** | `release.yml`, updater keypair in secrets, changelog gen, manifest gen, `releases` branch; `promote.yml` with environment gate | a `v*-beta.N` tag on a throwaway commit produces signed artifacts + a valid `beta.json` end-to-end, verified against the schema fixture; `cut-release` derives the right bump from a synthetic commit history in a workflow test | U1 |
| **U3 — shell updater** | plugin integration, state machine §5, bucketing, freeze, beacon fetch-through with CDN fallback; **absorbs the standing shell follow-up: re-inject the fresh WS token after sidecar restart** | Rust test list §8 green; mock-manifest flows work in `cargo run` | U1 (rustup: done 2026-08-03) |
| **U4 — cockpit UX** | chip + PanelSpec panel + consent flows + freeze toggle + dev-loop fallback | axe floor 0; announcer integration; CLI-help parity guard untouched (no CLI surface) | U3 state shape |
| **U5 — e2e + beacon** | mock-manifest fixture + the §8 spec list; beacon worker + histogram | all §8 e2e specs green in CI; beacon-down spec proves independence; old-state boot compat suite green against the committed vN-1 fixtures | U2–U4 |
| **U6 — signed rollout** | OS code signing (notarization + Windows cert), flip macOS/Windows updates on by default, beta cohort per D4 | one full beta→stable promotion executed with real installs | certificates (external) |

Sequencing: U1+U2 first (pure CI/repo work, immediately verifiable);
U3+U4 in parallel (disjoint Rust vs TS); U5 rides along; U6 waits on
the certificate purchase. Every PR carries the standard 18-gate body;
U1 and U2 are the natural first PR (small, high-leverage, unblocks
everything).

## 10. Change-resilience: the developer contract

The repo's features land weekly; the update system must survive them
without per-feature update work or tribal knowledge. The design rule:
**features integrate with updating by not integrating.** The updater
has deliberately zero in-app extension points — no hooks, no per-panel
update APIs, nothing a feature can couple to or break. The entire
interface between "a new feature" and "updating" is two mechanical
contracts, both enforced by tests rather than review vigilance:

| You (feature author) did… | The update system does… | You must do… | Enforced by |
|---|---|---|---|
| Added a feature / fixed a bug | Derives the bump from your conventional commit; changelog + manifest notes generated | Nothing | release-prep (§2.4) |
| Added **persisted operator state** (session, bank, favorites, …) | Survives the binary swapping under that state | Register the schema in the persisted-state registry with a `schema_version` (compile error / red arch test until you do) | contract A below |
| Touched wire behavior (engines, senders, parity surface, pins) | Sets `hardware_revalidation: true` on the next release automatically | Nothing | superset guard (§2.7) |
| Added an env var / CLI command / panel | Unaffected | Existing ratchets (env docs gate, CLI-help parity guard, PanelSpec registry) | pre-existing |
| Edited `VERSION` or a derived version file by hand | — | Don't; CI fails unless the commit came from release-prep | drift guard (§2.3) |

**Contract A — persisted-state compatibility.** Every module that
writes operator state under the config dir registers in a new
`data/persisted_state.py` fact table: `store name → current
schema_version → owning module`. Rules, all fail-closed:

- every persisted payload embeds its `schema_version` (the #236
  session store and the update manifest already model this);
- a newer app reading older same-major state migrates forward
  explicitly, or refuses with a journaled, bounded message — **never a
  silent reset** (an operator's show bank outliving an update is a
  product promise, not a nicety);
- an older app reading newer state refuses cleanly (the downgrade path
  after a manifest rollback);
- a new architecture test walks the registry and asserts each owner
  writes/validates its declared version, and each release commits an
  old-state fixture set under `tests/fixtures/persisted_state/` that a
  compat suite boots against — so "update didn't eat my state" is a
  regression test, not a hope.

**Contract propagation.** The contract ships as
`.claude/rules/update-compatibility.md` in U1 — the repo's rule files
are read by every agent session (human-driven or codex) at task start,
which is precisely how "any new feature understands how updating
works" without anyone remembering to explain it.

## 11. Risks & honest constraints

- **Unsigned macOS in-place updates** can trip Gatekeeper on the
  swapped bundle: until U6, macOS updates ship behind an
  "experimental" caveat in the panel copy.
- **Linux:** the updater handles AppImage; `.deb`/`.rpm` installs get
  the chip as notification-only with package-manager instructions.
- **Consent is the floor on fleet speed — by design.** The histogram
  makes residual consent-lag visible instead of pretending it away;
  the answer to slow adoption is release notes worth restarting for,
  never removing the gate.
- **Two prior in-file version duplicates** (pyproject) prove drift is
  real here, not theoretical — U1's "exactly one occurrence" assertion
  exists because of it.
