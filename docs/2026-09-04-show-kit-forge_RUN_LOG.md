# Show Kit Forge Run Log

Started: 2026-09-04; integration resumed: 2026-09-07

Branch: `codex/show-kit-forge-complete`

Base: `origin/modularize-v1.34` at
`0b77f9fef019dbfe1da943019b339bd446f95725`

Status: implementation published in
[PR #238](https://github.com/buzzijose-hub/RytmRandomizer/pull/238) against
`modularize-v1.34`; final CI and operator-present studio validation are tracked
in the run state.

## Workstream record

- **Preservation and resume:** the dirty primary checkout and earlier
  `show-kit-forge` worktree remain untouched. The current integration began
  at the same fetched base in `show-kit-forge-complete`; scoped fixes were
  developed in three independent worktrees and copied by file ownership.
- **Review fixes:** source slots are protected across cues and active banks;
  captures, disconnects, sends, and source removal revoke stale live readiness
  or plan authority. Every live Show Forge Rytm SEND requires a fresh exact
  source capture and explicit manual reload acknowledgment. Fully locked A4
  partners preserve the exact source bytes and compare the complete payload.
  Imported offsets cannot redefine the promoted A4 semantic projection.
- **Persistence hardening:** bounded reads validate the opened file identity;
  publication checks capacity before writing; duplicate export ids remain
  recoverable WS errors. No existing favorite or package is overwritten.
- **Evidence dependency:** the frozen AL02 blocked-export manifest updates
  only its `devices/__init__.py` dependency hash for the new optional offline
  capability export. Its blocked status, 18 mapping gaps, and output/authority
  claims are unchanged. No V1.34 fixture was regenerated.
- **Plan:** one clean integration worktree, one branch, and one non-stacked PR
  shape were established in
  [`superpowers/plans/2026-09-04-show-kit-forge.md`](superpowers/plans/2026-09-04-show-kit-forge.md).
- **A4 evidence/codec:** three hash-pinned 2026-08-28 captures establish only
  Filter 1 Frequency at native Track 1 offset 128, 350-byte track stride, and
  unsigned big-endian Q8.8 over `0x0000..0x7F00`. A distinct offline renderer
  validates checksum, re-decode, and intended-native-byte isolation and always
  reports `hardware_send_validated = false`. The legacy Filter 2 Resonance
  hardware-write-validated writer remains separate.
- **A4 scratch handoff:** the generated four-track file has SHA-256
  `829eee0209a248012a968e96df33acd007619a0078255c4fd034b5afda3520dd`,
  checksum 9533, and intended values T1 `16.25`, T2 `48.50`, T3 `80.75`, T4
  `112.25`. Its status is `pending_physical_outbound_validation`; its
  observation list is empty.
- **Show-bank domain:** source captures are immutable; selected candidate,
  Rytm live audition, favorite, manual save attestation, semantic recapture,
  and show-time readiness are separate records. Lifecycle status is derived as
  `source -> candidate -> favorite -> hardware-saved -> verified -> show-ready`.
- **Persistence/export:** bank edits publish new canonical JSON revisions;
  exact framed SysEx is content-addressed and retained only on an explicit
  action. Self-contained `.show-pack` directories carry cue order, recovery
  text, checksums, retained frames, and a final manifest, and fail closed on
  file-set/schema/framing/hash/path/cross-reference mismatches.
- **Cockpit workflow:** the frontend consumes authoritative whole-state events;
  it keeps A4 SEND disabled and labels candidates offline-only. Rytm audition
  reuses Preview -> PREPARE -> exact confirmed `ArmedApply` SEND and visibly
  remains live/unsaved. OXI fields are metadata only.
- **Readiness:** favorite recapture compares the promoted semantic projection.
  A separate show-time preflight compares each fresh whole-payload capture
  fingerprint exactly with its retained successful recapture; either mismatch
  revokes readiness and retains recovery evidence.
- **Documentation:** STATUS, Cockpit Quickstart, architecture prose/diagrams,
  and the manual hardware-validation guide were reconciled with the
  implementation. The remaining physical steps are recorded in
  [`hardware-validation/2026-09-04-show-kit-forge-studio-checklist.md`](hardware-validation/2026-09-04-show-kit-forge-studio-checklist.md).

## Authority and non-claims

- No documentation or automated test in this run represents an A4 SEND.
- No persistent KIT save is performed by Cockpit; the operator must save on
  each instrument and then recapture.
- The existing Rytm `ArmedApply` route is implemented, but this bundle's
  physical one-pad SEND, untouched-pad observation, and manual restore/return
  capture have not yet been performed.
- A4 physical return of the generated scratch artifact has not yet been
  observed.
- `verified` is not `show-ready`; only a fresh paired exact
  whole-payload-fingerprint preflight grants the latter.
- OXI remains the sequencing owner. No direct OXI control is implemented or
  claimed.
- No hardware observation has been fabricated; all studio observation fields
  remain blank.

## Verification record

The September 7 integration completed 8,788 Python tests with five skips;
all 22 touched production modules reached 100% branch coverage. Frontend
verification completed 779 tests with 100% coverage, typecheck, lint, build,
and one mocked browser journey. A post-push coverage review removed an
unnecessary exclusion and added four rejection cases: the 13-case Forge file
passes independently with 100% statement and branch coverage. The complete
recorded results and hosted CI status are maintained in the
[run report](superpowers/plans/2026-09-04-show-kit-forge_RUN_REPORT.md).

Independent reviewers found and drove fixes for import type exactness,
canonical A4 semantic offsets, source-slot protection, stale plan/readiness
revocation, repeated-audition source reload, strict publication bounds,
fixture reuse, missing decision telemetry, and operator instruction order.
The remaining large-panel readability concern is documented as Minor.
Physical MIDI/SysEx transfer was not run.

## Remaining gate

Complete every unchecked item in the dated studio checklist with Jose present.
In particular: manually return and save the generated A4 Filter 1 Frequency
scratch artifact before recapture; execute one exact-plan Rytm pad audition,
manually reload the source KIT, and prove its whole-payload fingerprint
returns; then save both chosen favorites, recapture, and run the fresh paired exact
whole-payload-fingerprint preflight for every cue.

## September 7 maintainer-review closeout

Reconciled review5133649443 against starting head6cfde1fc in isolated worktrees.
The [review ledger](2026-09-07-show-kit-forge-review-reconciliation.md) maps every
requested finding, including non-reproduced allegations and retained minors.
Final local Python: 8,926 passed/5 skipped; 32 touched modules at100% line and
branch coverage. Final web:809 tests at100%, plus21 browser journeys/2existing
skips with disabled/fake MIDI. Static and schema gates pass. The run report
records timings, earlier diagnostics and current external closeout receipts.
The full run includes the final bounded-diagnostic regressions added after
the fast/Cockpit benchmark runs. No physical observation is claimed.

## September 7 packaged-launch correction

The identified Windows build at `4cb0defdee3aa` compiled successfully but
failed the real GUI smoke: the shell supplied a fresh token and port while
the frontend kept dialing port 4317. It is a diagnostic artifact only.
The client now resolves the validated loopback port on every dial, preserving
explicit URL overrides and the existing authenticated handshake. Forty-three
new regression cases cover bootstrap precedence, invalid values, late injection
and reconnect behavior. Full frontend: 852 tests at 100% coverage; typecheck,
lint and production build pass. Full Playwright: 21 passed, two existing skips
in 51.3 seconds. A rebuilt artifact and non-default-port packaged smoke remain
required; no physical input, arm or output was requested.
