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
| **D1 — fleet awareness** | **GitHub-native beacon** (per-release ping assets + a free scheduled snapshot job) | The driver directive demands "be aware of users and their versions"; the zero-opex constraint (§0.2) rules out any operated service, even free-tier. GitHub download counters + a cron Actions job answer the question with no account, domain, deployment, or pricing policy outside what the repo already uses (see §6). |
| **D2 — check cadence** | Launch + every 4 h while running + manual "Check now" | Hours-scale worst-case T_notice with zero infrastructure; a ~1 KB CDN GET is cheap enough to be frequent. |
| **D3 — default consent affordance** | "Install on next launch" pre-selected | Fastest fleet convergence that never forces a restart on a stage machine. |
| **D4 — beta channel population** | Maintainers first (`buzzijose-hub`, `edward-rosado`); widen by invitation after two beta→stable cycles | Smallest honest test population that still exercises both OS families in daily use. |

## 0.2 Standing constraint: zero operational cost

The operator mandate is **zero recurring operational cost and zero
operated services**. Every component below must be free on the
infrastructure the project already uses (a public GitHub repository)
and must require no account, deployment, domain, or pricing policy
outside it. Full cost inventory:

| Component | Cost | Notes |
|---|---|---|
| Manifest + artifact hosting | $0 | GitHub Releases / raw branch files on the public repo |
| Release/promote/validate/snapshot workflows | $0 | GitHub Actions on a public repo (this is conditional: if the repo ever went private, the 3-OS build matrix — macOS especially — starts consuming paid minutes; that event re-opens this table) |
| Updater signatures | $0 | Ed25519 keypair; no CA involved |
| Fleet awareness (§6) | $0 | GitHub-native beacon — download-counted ping assets + a scheduled snapshot job; no operated service |
| Fleet dashboard (§6.1) | $0 | one static page on GitHub Pages serving the `releases` branch; no build, no external scripts |
| **OS code signing (U6 only)** | **the one money item** | Apple Developer ≈ $99/yr + a Windows signing certificate — already deferred to the operator's planned certificate purchase; nothing else in this spec spends anything |

An earlier draft of D1 proposed a Cloudflare Worker beacon. It is
**rejected under this constraint** — even at $0 it is an operated
service with an external pricing policy — and recorded here so it is
not re-proposed without noticing the constraint.

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

**Pull, not push — and no server to operate.** Nothing is ever pushed
to a client. Each install polls the channel manifest (a ~1 KB static
JSON on GitHub's CDN) at launch, every 4 h while running, and on
manual "Check now"; the artifact is then staged in the background and
installed only on operator consent (§5). A push channel (WebSocket /
notification service) was considered and deliberately rejected: the
poll cadence already yields hours-scale worst-case fleet notice with
**zero operated infrastructure**, and a push path would add a server
whose availability sat in front of update delivery. The only optional
hosted piece in the whole design is the fleet-awareness beacon (§6) —
a logging redirector that can vanish without affecting a single
update.

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
  "build": {
    "source_sha": "<40-hex commit the tag pointed at>",
    "workflow_run_url": "https://github.com/…/actions/runs/…",
    "builder_workflow_sha": "<sha of release.yml itself at build time>"
  },
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
- `build` is informational provenance (never validated for update
  eligibility — a client must not refuse an update over provenance
  fields) but makes every release auditable the way AL16 evidence
  manifests are: artifact → workflow run → source commit.
- The manifest schema is pinned by a fixture + a Rust serde round-trip
  test AND a Python-side fixture validator, so both consumers drift
  together or fail loudly.

## 5. Update state machine (shell-owned)

The end-to-end process — release pipeline, client state machine, and
fleet awareness on one canvas — is diagrammed in
[`docs/ARCHITECTURE_DIAGRAMS.md` §37](../../ARCHITECTURE_DIAGRAMS.md#37-auto-update-flow-designed--spec-complete-implementation-pending)
(one canonical diagram; this section is the normative text it renders).

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

### 5.1 Update journal — the observability substrate

The updater runs in the Rust shell, outside the Python
`observability/` stack — and with zero servers, client-side failures
are visible **only** locally. Observability is therefore designed in,
not bolted on:

- **Every §5 state transition appends one structured JSONL row** to
  `update-journal.jsonl` in the config dir (size-capped rotation, two
  generations): `{ts, event, version, detail}` with `event` drawn from
  a closed vocabulary (`check_started`, `check_ok`, `check_failed`,
  `manifest_rejected`, `bucket_excluded`, `download_started`,
  `download_ok`, `stage_failed`, `signature_rejected`,
  `consent_granted`, `install_started`, `install_ok`, `install_failed`,
  `skip_recorded`, `freeze_suppressed`, `ping_ok`, `ping_failed`) and
  `detail` a **bounded, path-free** map (the #224/#238 hygiene
  standard: no absolute paths, no raw `str(err)` passthrough — typed
  reason codes plus sizes/durations only).
- **The journal is the single source of truth** for three consumers:
  the update panel's "recent update activity" list (§7), the
  Connection Doctor's export bundle (extended to include the journal
  tail), and the e2e suite — specs assert journal rows rather than
  scraping UI state, which makes every failure path testable.
- **Privacy:** the journal never leaves the machine and is never
  transmitted anywhere — consent history is operator-local evidence,
  full stop.
- **Sidecar-side pieces use the existing stack** (Gate 7, no
  exceptions): persisted-state migrations and refusals (§11 Contract
  A) raise typed taxonomy errors with fingerprints
  (`persisted_state.schema_newer_than_app`,
  `persisted_state.migration_failed`) and record
  `get_metrics().record_persisted_state_migration(store, from_v,
  to_v)` / refusal counters, surfaced by `format_summary()` and the
  Doctor journal like every other boundary.
- **Failure honesty has a floor:** `check_failed` and
  `signature_rejected` rows are also mirrored as operator-log entries
  in the cockpit (the ReconnectBanner-era pattern), so a silently
  failing updater is impossible — it either works or it visibly says
  why, locally.

## 6. Fleet awareness — GitHub-native, zero-opex (D1)

The question to answer: which versions is the fleet running, per
channel and OS, over time — without operating anything.

- **Ping assets as counters.** Every release uploads tiny
  `beacon-<version>-<target>.txt` assets (one byte, one per OS
  target). When a client performs its scheduled update check, it also
  fires a fire-and-forget GET of the ping asset for **its own running
  version and OS**. GitHub increments that asset's `download_count` —
  which makes the counts a per-version, per-OS check-in tally.
- **Snapshotting.** A scheduled (cron) `fleet-snapshot.yml` workflow —
  free on the public repo — reads the counts via the Releases API and
  appends a dated row to `fleet-history.json` on the `releases`
  branch. Deltas between snapshots are the version histogram over
  time; installs ≈ check-ins ÷ expected daily cadence.
- **Structurally unable to gate, by construction.** The ping is
  fire-and-forget and entirely separate from the manifest fetch: its
  failure, absence, or removal cannot delay or block an update check
  (pinned by a §8 test). There is no server whose uptime sits in front
  of anything.
- **Privacy — stronger than the rejected worker design.** No install
  identifier is ever transmitted: the `install_id` of §5 exists only
  locally as the rollout-bucketing input. The only signal that leaves
  the machine is an anonymous HTTP GET of a public release asset.
  Opt-outs: `RYTM_RAND_UPDATES=off` (no traffic at all) and
  `RYTM_RAND_UPDATE_BEACON=off` (checks continue, ping never fires).
- **Honest limits.** Counts are check-ins, not unique installs (the
  cadence estimate covers fleet-sizing); per-version resolution begins
  at the first release that ships ping assets; a client that never
  updates past a pre-beacon version is invisible (acceptable — the
  histogram's job is steering rollouts of new releases).

### 6.1 Fleet dashboard — monitoring a rollout over time

The answer to "how many devices, on which versions, and how is the
rollout going" is a **static dashboard page served by GitHub Pages
from the `releases` branch** — the page lives next to the data it
charts, so it fetches `fleet-history.json` same-origin with no CORS,
no build step, no external service, and no cost (Pages is free on the
public repo; enabling it is a one-time repo setting, recorded in U5).

- **`index.html` on the `releases` branch** — one self-contained page
  (inline JS + SVG; no external scripts or chart libraries, so the
  page has zero third-party dependencies and works offline against a
  checked-out branch).
- **What it renders:**
  1. *Fleet composition now* — estimated devices per version, split by
     OS (stacked bars from the latest snapshot delta).
  2. *Rollout adoption curve* — version share over time across
     snapshots: the line you watch while stepping a rollout, with
     **rollout-percent markers** annotated where promote commits moved
     10 → 50 → 100.
  3. *Raw check-ins* alongside every estimate — the page always shows
     the measured number next to the derived one.
- **Estimator, stated on the page itself:** estimated devices =
  check-ins per interval ÷ expected checks per device per interval
  (from the §0-D2 cadence: launch + every 4 h while running). It is an
  estimate and the dashboard says so; the raw counts are the ground
  truth.
- **Data plumbing:** each `fleet-snapshot.yml` row records, besides
  the per-asset counts, the current `stable`/`beta` manifest
  `version` + `rollout_percent` — which is what lets the adoption
  curve carry its promote markers without mining git history.
- **In-app link:** the cockpit update panel (§7) links to the
  dashboard URL for maintainers; the panel itself never fetches fleet
  data (operators see their own version, not the fleet).
- **Validation:** the estimator/delta logic lives in one small
  embedded function; `manifest-validate.yml` extends to sanity-check
  `fleet-history.json` rows against a schema fixture, and U5 ships a
  fixture-driven render check (the page against a synthetic history
  produces the expected series — run under the existing web test
  tooling, not a new stack).

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

Architecture tests (**the first three land with this spec PR**, each
mutation-proven at introduction; the rest arrive with their
workstreams):
- `test_version_single_source.py` — §2.3, **landed**: self-upgrading —
  pins today's five-declaration inventory as a drainable baseline and
  switches to the full single-source contract automatically when U1
  creates `VERSION`.
- `test_plan_index_rows.py` — **landed**: every plan doc has an
  `INDEX.md` row and every row links a real file (found two missing
  rows at introduction).
- The §9.2 pin-scan widening — **landed**: `test_ci_workflow.py` now
  collects lint pins from every install site in every workflow and
  asserts cross-site agreement (the second `test.yml` site at line 418
  was previously invisible to it).
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
- freeze mode: zero network calls (mock transport asserts call count 0)
  AND a `freeze_suppressed` journal row.
- journal contract: every §5 transition writes exactly one row with a
  closed-vocabulary event; failure paths (`manifest_rejected`,
  `signature_rejected`, `stage_failed`) each produce their row with a
  typed reason code; a path-injection probe proves `detail` never
  contains an absolute path; rotation caps hold.

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
- ping independence: the beacon asset URL pointed at a dead port; the
  update check still completes and the chip still appears (the ping is
  fire-and-forget and cannot gate).
- fleet-snapshot: the snapshot script against a fixture Releases API
  payload appends the correct dated row to `fleet-history.json`
  (including the stable/beta version + rollout_percent columns).
- dashboard render: the embedded estimator/series function against a
  synthetic `fleet-history.json` fixture produces the expected
  composition and adoption series.
- `hardware_revalidation: true` renders the banner naming the manual
  validation doc.
- journal-backed assertions: the consent-flow and failure-path specs
  assert §5.1 journal rows (not just UI state), and the panel's
  activity list matches the journal tail.

CI: see §9 — the pipeline design is a first-class part of this spec,
not an implementation detail.

## 9. Pipeline integration & invariants

The repo's pipelines are themselves a guarded surface
(`tests/architecture/test_ci_workflow.py`: lint-pin parity, pip
caching, the `required-checks` aggregate) — and #224 demonstrated the
failure mode this section exists to prevent: a new workflow step
installing lint tools **outside** the pin-scan's field of view. Every
pipeline this spec adds lands inside the enforcement perimeter on day
one.

**Pipeline inventory and touchpoints:**

| Workflow | Trigger | Role in this design |
|---|---|---|
| `test.yml` | PR / push | Untouched. The release PR that `cut-release` opens is an ordinary PR — it must pass the full `required-checks` aggregate before anyone may tag. |
| `installers.yml` | push / dispatch | **Converted to a reusable workflow (`workflow_call`)** exposing the 3-OS bundle build. |
| `release.yml` | push `v*` tags | verify-tag → **calls the shared build** → updater-sign → changelog → GitHub Release → generate + commit `beta.json`. |
| `promote.yml` | `workflow_dispatch`, environment `stable-promote` (required human approval) | Validates, then copies beta → `stable.json` at a chosen `rollout_percent`. |
| `manifest-validate.yml` | push to the `releases` branch | Schema-validates `stable.json`/`beta.json` against the pinned fixture — **the last gate in front of the fleet**; rollback commits pass through it too. |
| `fleet-snapshot.yml` | schedule (cron) | Reads release-asset download counts, appends a dated row to `fleet-history.json` on the `releases` branch. Scheduled workflow: exempt from `required-checks`, inside the pin/caching scans (§9.2). |

Rules, each with an enforcement home:

1. **Single build truth.** `release.yml` never re-implements build
   steps; it `workflow_call`s the same job CI artifacts use, so a
   build change in a feature PR reaches release builds in the same
   commit — the two can never drift. (This conversion is U2's first
   task, and it is also what lets a release build be rehearsed from a
   PR without tag rights.)
2. **Enforcement-perimeter membership.** `test_ci_workflow.py` gains
   an explicit workflow scope map: PR-event jobs must appear in
   `required-checks.needs`; tag/dispatch workflows are exempt from the
   aggregate **but not from the pin/caching scans**, and the pin scan
   is widened to walk *every* workflow file rather than `test.yml`
   alone — closing the #224-class gap for good rather than per
   incident.
3. **Secrets and trigger safety.** `TAURI_SIGNING_PRIVATE_KEY` (+
   password) exist only in tag-triggered `release.yml` and the
   environment-gated `promote.yml`; no `pull_request_target` anywhere;
   fork-originated events can never reach a signing context.
   `concurrency` groups serialize releases (one tag build at a time)
   and serialize promote against release.
4. **Least-privilege permissions, explicitly.** Every workflow this
   spec adds declares a top-level `permissions:` block with the
   minimum needed: `contents: write` only where a release or a
   `releases`-branch commit is actually produced (`release.yml`,
   `promote.yml`, `fleet-snapshot.yml`), `contents: read` everywhere
   else, and no other scopes anywhere. The reusable build keeps
   `installers.yml`'s existing `contents: read`.
5. **Action pinning follows the #219 decision:** float majors
   (`actions/checkout@v7`-style); no patch pins — a security-scanning
   or build action frozen at a patch is the anti-pattern this repo
   already litigated and closed.
6. **CI cost containment.** Pushes to the `releases` branch (manifest
   commits, rollbacks) are excluded from `test.yml` triggers;
   `manifest-validate.yml` is their sole — and sufficient — gate. The
   mock-manifest e2e fixture binds an ephemeral port so it composes
   with the existing e2e job's `workers: 1` / port-4317 constraints.
7. **Pipeline observability.** Every workflow this spec adds writes a
   `GITHUB_STEP_SUMMARY` block with its structured outcome —
   `release.yml`: version, artifact list + sizes, signature status,
   manifest committed; `promote.yml`: from→to version and
   rollout_percent; `manifest-validate.yml`: per-file verdicts with
   failing rule named; `fleet-snapshot.yml`: row appended + count
   deltas — so a maintainer reads outcomes from the run page without
   spelunking logs, and a failed gate names its rule.
8. **Bot coexistence.** `cut-release` writes only via an ordinary PR
   (full gates), so it cannot fight the coverage-ratchet bot's
   push-back behavior; neither bot ever pushes to a branch the other
   owns.

## 10. Workstreams, acceptance criteria, sequencing

| WS | Scope | Acceptance criteria | Depends on |
|---|---|---|---|
| **U1 — version spine** | `VERSION`, derivations, `sync_version.py`, drift-guard test, `app_version` in session_status; `data/persisted_state.py` registry + its arch test; `.claude/rules/update-compatibility.md` | arch tests green (the version guard's pre-U1 ratchet already landed with the spec; U1 flips it to full mode by creating `VERSION`); one `version =` left in pyproject; every existing config-dir writer registered with a `schema_version`; the rule file lands with the registry | — |
| **U2 — release pipeline** | `installers.yml` → `workflow_call` conversion; `release.yml`, updater keypair in secrets, changelog gen, manifest gen, `releases` branch; `promote.yml` with environment gate; `manifest-validate.yml`; `test_ci_workflow.py` scope map (the all-workflow pin scan of §9.2 already landed with the spec) | a `v*-beta.N` tag on a throwaway commit produces signed artifacts + a valid `beta.json` end-to-end, verified against the schema fixture; `cut-release` derives the right bump from a synthetic commit history in a workflow test; CI artifact and release build come from the same called workflow; an intentionally malformed manifest is refused by `manifest-validate.yml` | U1 |
| **U3 — shell updater** | plugin integration, state machine §5, bucketing, freeze, the fire-and-forget ping GET (§6); **absorbs the standing shell follow-up: re-inject the fresh WS token after sidecar restart** | Rust test list §8 green; mock-manifest flows work in `cargo run` | U1 (rustup: done 2026-08-03) |
| **U4 — cockpit UX** | chip + PanelSpec panel + consent flows + freeze toggle + dev-loop fallback | axe floor 0; announcer integration; CLI-help parity guard untouched (no CLI surface) | U3 state shape |
| **U5 — e2e + fleet snapshot** | mock-manifest fixture + the §8 spec list; ping assets in the release job; `fleet-snapshot.yml` + `fleet-history.json`; the §6.1 dashboard page + Pages enablement | all §8 e2e specs green in CI; the ping-independence spec proves the beacon cannot gate; a snapshot run against fixture API data produces the expected fleet-history row; the dashboard render check passes against the synthetic history fixture; old-state boot compat suite green against the committed vN-1 fixtures | U2–U4 |
| **U6 — signed rollout** | OS code signing (notarization + Windows cert), flip macOS/Windows updates on by default, beta cohort per D4 | one full beta→stable promotion executed with real installs | certificates (external) |

Sequencing: U1+U2 first (pure CI/repo work, immediately verifiable);
U3+U4 in parallel (disjoint Rust vs TS); U5 rides along; U6 waits on
the certificate purchase. Every PR carries the standard 18-gate body;
U1 and U2 are the natural first PR (small, high-leverage, unblocks
everything).

## 11. Change-resilience: the developer contract

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

## 12. Risks & honest constraints

- **Unsigned macOS in-place updates** can trip Gatekeeper on the
  swapped bundle: until U6, macOS updates ship behind an
  "experimental" caveat in the panel copy.
- **Linux:** the updater handles AppImage; `.deb`/`.rpm` installs get
  the chip as notification-only with package-manager instructions.
- **Actions minutes are free only while the repository is public.** A
  future move to private re-opens §0.2's cost table (macOS build
  minutes in particular) — flagged so the constraint is re-checked at
  that decision, not discovered after it.
- **Consent is the floor on fleet speed — by design.** The histogram
  makes residual consent-lag visible instead of pretending it away;
  the answer to slow adoption is release notes worth restarting for,
  never removing the gate.
- **Two prior in-file version duplicates** (pyproject) prove drift is
  real here, not theoretical — U1's "exactly one occurrence" assertion
  exists because of it.
