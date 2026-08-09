# Auto-update: versioned, gated, fast-to-fleet distribution

Date: 2026-08-03
Status: proposed
Base: `modularize-v1.34`
Driver: operator directive — installed apps must auto-update, with
version control "really good" and gated updates; the plan must
"really consider speed of distribution … how fast we can update this
app throughout the network and be aware of users and their versions —
the faster and more uniformly we can iterate."

---

## 1. Safety model first: updates are a transmit-shaped problem

This application runs on stage. An updater that restarts the app
mid-set is the same class of failure as an unwanted MIDI send, so the
update system inherits the repository's Live-but-Passive model:

| Live-but-Passive MIDI | Update analogue |
|---|---|
| Enumerating ports / opening inputs — free, ongoing | **Checking** for updates + downloading in the background — free, ongoing |
| Transmit — armed, per-action confirm | **Installing** — explicit operator confirmation, never automatic |
| Arming never survives reconnect | An accepted update never auto-installs after a crash/restart loop; consent is per-version |
| `RYTM_RAND_MIDI_BACKEND=off` escape hatch | **Freeze mode**: `RYTM_RAND_UPDATES=off` (or in-UI toggle) disables even the check — for the machine that goes to the gig |

Key derived rule: **download eagerly, install consensually.** The
artifact is already on disk by the time the operator says yes, so the
"cost" of consent is one app restart, not a download wait. This is the
single biggest speed-of-distribution lever available to a
consent-gated updater (see §5).

## 2. Version control: one source of truth, mechanically enforced

Today the version is declared independently in `pyproject.toml`,
`desktop/shell/Cargo.toml`, `desktop/shell/tauri.conf.json`, and
`desktop/web/package.json`. That is four places to drift.

1. **Canonical home: `VERSION` at the repo root** (single line,
   SemVer). Everything else derives from it:
   - `pyproject.toml` reads it (dynamic version via build backend).
   - `tauri.conf.json` / `Cargo.toml` / `package.json` are checked, not
     trusted: a new architecture test
     `tests/architecture/test_version_single_source.py` asserts all
     four agree with `VERSION`. Drift = red CI, the repo's standard
     move (same shape as the readme-freshness and plan-status guards).
   - The sidecar exposes it (`session_status.app_version`) and the
     shell embeds it (`tauri.conf.json` version) so **both halves of a
     running install can state their version** — used by diagnostics,
     the beacon (§6), and the update check itself.
2. **SemVer discipline.** MAJOR = migration/manual step required;
   MINOR = features; PATCH = fixes. Pre-releases (`-beta.N`) flow to
   the beta channel only.
3. **Tag-driven releases.** Pushing tag `vX.Y.Z` (protected tag
   pattern; only maintainers) is the ONLY way a release exists. The
   tag must match `VERSION` on the tagged commit (release workflow
   verifies, refuses otherwise). The tag is the audit trail.
4. **Changelog from conventional commits.** `feat:`/`fix:` history
   (already house style) generates `CHANGELOG.md` + the release notes
   the operator sees in the update prompt. A `BREAKING CHANGE:` footer
   or `!` marks MAJOR.
5. **Hardware-revalidation flag.** A release whose diff touches the
   parity surface, `mido`/`rtmidi` pins, or the ArmedApply seam gets
   `"hardware_revalidation": true` in its manifest entry (release
   workflow derives it from changed paths + a manual override). The
   update UI surfaces it loudly. This ties the update gate to the
   repo's hardest invariant.

## 3. Distribution architecture: static files, no servers to run

**Transport: `tauri-plugin-updater` v2** (built into the Tauri 2 stack
we ship). The shell fetches a channel manifest, compares versions,
downloads the platform artifact, verifies the updater signature,
stages it, and swaps on restart.

**Artifact host: GitHub Releases.** Served from GitHub's global CDN —
worldwide edge distribution with zero infrastructure owned by us. Old
releases stay downloadable forever (rollback recovery path).

**Integrity: Tauri updater Ed25519 signatures** on every artifact,
independent of OS code signing. The private key lives only in GitHub
Actions secrets; the public key is compiled into the shell. An update
that doesn't verify is discarded silently-but-logged (Connection
Doctor surfaces it). This is available TODAY, before the paid
Apple/Windows certificates land.

**Channel = manifest file.** `stable.json` and `beta.json` live in a
dedicated `releases` branch (or gh-pages), served raw. Each contains:

```json
{
  "version": "1.35.1",
  "notes": "…generated changelog excerpt…",
  "pub_date": "…",
  "hardware_revalidation": false,
  "rollout_percent": 100,
  "platforms": {
    "darwin-aarch64": { "signature": "…", "url": "https://github.com/…/v1.35.1/….app.tar.gz" },
    "windows-x86_64": { "signature": "…", "url": "…-setup.nsis.zip" },
    "linux-x86_64":   { "signature": "…", "url": "….AppImage.tar.gz" }
  }
}
```

**Promotion and rollback are both one-line Git commits** to the
manifest file — reviewable, revertable, instant (next client check
sees it). Rollback = re-point `stable.json` at the previous release.
No client-side downgrade machinery needed: clients that already
updated stay put (or reinstall from Releases); clients that haven't
never see the bad version. Time-to-stop-the-bleeding = one commit +
one CDN TTL.

**Atomic app+sidecar.** The PyInstaller sidecar ships inside the
bundle, so the Rust shell and Python engine update as one artifact —
version skew between the two halves is structurally impossible. The
WS subprotocol pin (`rytm-rand-cockpit-v1`) stays as the belt-and-
suspenders guard.

## 4. Gating: who gets what, when

Layered, all independently controllable:

1. **Channel gate.** Beta testers opt into `beta` in-UI; everyone else
   is on `stable`. Promotion beta→stable is a human-approved CI job
   (GitHub environment protection — an actual approval button, same
   trust shape as CODEOWNERS).
2. **Staged rollout gate — serverless.** `rollout_percent` in the
   manifest + deterministic client bucketing: the client hashes its
   stable anonymous install id into a 0-99 bucket; it takes the update
   only if `bucket < rollout_percent`. Raising 10 → 50 → 100 is three
   manifest commits. No server, perfectly uniform (hash is stable per
   install, so nobody flaps in/out).
3. **Operator gate.** Passive "Update available" chip → changelog +
   (if flagged) the hardware-revalidation warning → explicit choice:
   **Restart & install** / **Install on next launch** (default) /
   **Skip this version**. Never a modal ambush; WCAG AA like the rest
   of the cockpit.
4. **Freeze gate.** `RYTM_RAND_UPDATES=off` or the in-UI "Freeze
   updates (performance mode)" toggle: no check, no download, no chip.
5. **Minimum-version policy (reserved).** The manifest schema carries
   `"minimum_version"` from day one but the client treats it as
   advisory-banner-only. If a catastrophic-fix scenario ever demands
   forced updates, the mechanism exists without a schema migration —
   flipping it to blocking is a deliberate future decision, not a
   hotfix.

## 5. Speed of distribution — the explicit design target

Fleet update latency decomposes as:

```
T_fleet = T_publish + T_notice + T_download + T_consent
```

Each term is attacked separately:

- **T_publish (tag → artifacts live): target < 45 min.** The release
  workflow parallelizes the three OS builds (matrix, same as
  installers.yml today). Manifest commit is automated at the end.
  Measured and reported per release.
- **T_notice (artifacts live → client knows): target ≤ 6 h, typ. min.**
  Check on every launch + a background re-check every 4–6 h while
  running + a manual "Check now" in the update panel. Checks are a
  single ~1 KB manifest GET against a CDN — cheap enough to be
  frequent. (A push channel is deliberately out of scope: a static
  CDN poll at this cadence gives hours-scale worst case with zero
  infrastructure; revisit only if the fleet ever needs minutes-scale.)
- **T_download (know → ready to install): hidden entirely.** The
  artifact downloads in the background at notice time (passive =
  free). By the time the operator sees the chip, the update is staged
  locally and verified. Metered/slow networks see a progress state,
  nothing blocks.
- **T_consent (ready → running new version): the honest bottleneck,
  by design.** Mitigations without violating the consent rule:
  "Install on next launch" is the default affordance — updates apply
  at natural restarts, which for a desktop music tool happen daily;
  the chip persists (calmly) until acted on; skip-this-version stops
  nagging without freezing the fleet. **We do not auto-install. Ever.**
  The fleet dashboard (§6) tells us when consent-lag, not
  distribution-lag, is what's left — that's the signal to ship
  release notes worth restarting for, not to remove the gate.

**Uniformity** comes from the staged-rollout hash (nobody flaps, every
percentage step is a superset of the last) plus the dashboard showing
the real version histogram, so 10→50→100 promotion is driven by
observed health, not guesswork.

## 6. Fleet awareness: knowing who runs what

The requirement "be aware of users and their versions" needs a data
path back. Two tiers, decided at implementation gate D1:

- **Tier 0 (free, coarse, day one):** GitHub Releases download counts
  per artifact + versioned manifest fetches. Tells us adoption volume,
  not live fleet state.
- **Tier 1 (recommended): the update beacon.** The manifest is fetched
  *through* a tiny edge worker (Cloudflare Worker free tier) instead
  of raw CDN: `GET /check?channel=stable&v=1.34.2&os=darwin-aarch64&id=<anon>`.
  The worker logs the tuple and 302s to (or proxies) the static
  manifest — the client experience is identical, the worker can never
  gate anything (it's a dumb logger; if it's down, clients fall back
  to the raw CDN URL — availability of updates NEVER depends on the
  beacon).
  - `id` is a random UUID minted at install, stored locally, carrying
    zero PII — it exists so the dashboard can distinguish "1 user
    checking hourly" from "24 users". Privacy line item in the README;
    disabled by `RYTM_RAND_UPDATES=off` and by a separate
    `RYTM_RAND_UPDATE_BEACON=off` for check-but-don't-report.
  - Output: a version histogram over time — the direct answer to "how
    fast and uniformly are we iterating", per channel, per OS, with
    rollout-percent overlays. Start with the worker's built-in
    analytics; graduate to a small dashboard page when needed.

## 7. Update UX (cockpit)

- Header chip: `⬆ 1.35.1 ready` (icon + shape + text, colorblind-safe
  per the a11y standard). Hidden in freeze mode.
- Update panel (PanelSpec, bottom region like the Doctor): current
  version, channel selector (stable/beta), changelog of the staged
  update, hardware-revalidation banner when flagged, the three consent
  actions, "Check now", freeze toggle, and last-check/last-beacon
  timestamps (honesty about what phoned home).
- Failure honesty: signature-verify failures and download failures
  appear in the Connection Doctor journal, never silently retried into
  oblivion.
- Every state e2e-testable against a **mock manifest server** fixture
  (the Playwright platform from PR #221 — specs drive: chip appears,
  staged download, consent flows, skip-version persistence, freeze
  mode, rollout bucketing boundaries, signature-reject path).

## 8. Workstreams

| WS | Scope | Depends on |
|---|---|---|
| **U1 — version spine** | `VERSION` file, derivations, drift-guard arch test, `session_status.app_version`, tag-verify script | — |
| **U2 — release pipeline** | tag-triggered workflow: 3-OS matrix build, updater-key signing, changelog gen, manifest gen, Release upload, `releases` branch commit; environment-protected `promote` job (beta→stable) | U1 |
| **U3 — shell updater** (Rust) | `tauri-plugin-updater` integration, channel/rollout/freeze logic, background download + staged-install state machine, beacon fetch-through with raw-CDN fallback; **absorbs the queued shell follow-up: re-inject fresh WS token after sidecar restart** | U1; rustup (done) |
| **U4 — cockpit UX** | chip, update panel, consent flows, a11y, freeze toggle; sidecar relays updater state over WS if the shell owns it (bridge via the existing shell→page injection or a small WS extension) | U3 shape |
| **U5 — e2e + fleet dashboard** | mock-manifest Playwright fixture + specs (§7); Tier-0 metrics; Tier-1 beacon worker + histogram if D1 says yes | U2–U4 |
| **U6 — signed rollout** | OS code signing (Apple notarization, Windows cert) once certificates are purchased; flip macOS/Windows to updates-on-by-default; beta channel with real testers | certs (external) |

Sequencing: U1+U2 land first (pure CI/repo work, immediately
verifiable). U3+U4 in parallel after (disjoint: Rust vs TS). U5 rides
along. U6 waits on the certificate purchase already planned.

## 9. Decision gates for the maintainer

- **D1 — beacon tier.** Tier 1 (edge-worker beacon, recommended: it is
  the only way to actually "be aware of users and their versions")
  vs Tier 0 only (zero third-party infra, coarse data). Tier 1 adds
  one free-tier Cloudflare Worker to operate.
- **D2 — check cadence.** Proposed: launch + every 4 h + manual.
- **D3 — default consent affordance.** Proposed: "Install on next
  launch" pre-selected (fastest fleet convergence that never forces a
  restart).
- **D4 — beta channel population.** Who opts in first.

## 10. Risks & honest constraints

- **Unsigned-app updates on macOS** can trip Gatekeeper on the swapped
  bundle; until notarization (U6), macOS updates stay behind an
  "experimental" flag or ship-with-caveat. Windows NSIS updates work
  unsigned but SmartScreen nags on first install (unchanged from
  today).
- **Linux coverage**: the updater handles AppImage; `.deb`/`.rpm`
  installs update via the distro package path — the manifest chip
  still notifies, but install consent hands off to the package
  manager instructions.
- **Consent is the floor on fleet speed.** By design. The dashboard
  makes the residual lag visible instead of pretending it away.
- **Rust builds enter the local loop** (U3): rustup now installed on
  the dev machine; CI remains the release oracle.
