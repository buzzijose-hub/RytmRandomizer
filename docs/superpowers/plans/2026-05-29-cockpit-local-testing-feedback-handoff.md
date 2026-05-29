# Cockpit Local Testing Feedback Handoff

Date: 2026-05-29

## Current Decision Point

PR #145 is the single consolidated pull request for Jose's local cockpit testing
feedback bundle:

- PR: https://github.com/buzzijose-hub/RytmRandomizer/pull/145
- Branch: `codex/cockpit-local-testing-feedback-bundle`
- Base: `modularize-v1.34`
- Remote head: `0fd3c8fec90dc1f2b96dfa20eae0a62b17132431`
- State: open, not draft
- Mergeability: mergeable, blocked only by Eddie's existing changes-requested review
- Checks: green, including `desktop-web`, `desktop-web-e2e`, `desktop-shell`,
  Python tests, architecture, CodeQL, and `required-checks`

The remaining blocker is human review, not failing tests or merge conflicts.

## What Jose Tested Locally

Jose installed and ran the cockpit, then compared it against expectations from
the mockups, Analog Rytm Overbridge, and the Analog Rytm / Analog Four manuals.
Key observations:

- The installed cockpit initially opened but stayed disconnected/reconnecting.
- Running the GUI locally worked better than the installed shell.
- The cockpit originally showed only four Rytm pads; Jose expects all 12 Rytm
  tracks visible in one unified performance view.
- The UI did not clearly show whether the app was connected to hardware or which
  MIDI/WebSocket devices were active.
- SEND did not visibly reach the device during local testing, and scene changes
  became awkward after attempting SEND.
- The visible pad controls were too shallow. Pad 1 showed only a few controls,
  but BD Hard alone needs the broader engine surface: tune, sweep time, snap
  amount, waveform, hold time, tick/transient, level, filter envelope, amp
  envelope, sample controls, modulators, velocity/aftertouch targets, etc.
- The UI should use Analog Rytm Overbridge as the practical reference for
  complete parameter coverage, while keeping the RytmRandomizer performance
  workflow focused on seeing all pads at once.
- Snapshot history belongs in a left-side expandable/session panel; selecting a
  snapshot should recall/load its settings.
- The profile wizard Browse button failed in local testing; copy/paste path was
  the workaround.
- Profile Analyze behavior was confusing or incomplete. The expected direction is
  reference-track inspiration: analyze a song, derive traits, and create an
  original mutation direction rather than copying the source.
- Export Model did not visibly do anything.
- Future but important: live queue / staged snapshots for long performance sets.

## What PR #145 Implements

The PR addresses the first consolidated slice of those findings:

- Installer/shell token handshake:
  - shell pins `RYTM_RAND_WS_TOKEN_FILE`
  - sidecar mints token into that file
  - shell reads and injects `window.__RYTM_RAND_WS_TOKEN__`
  - token bridge keeps polling/reinjecting so sidecar restart does not leave a
    stale frontend token
- Cockpit UI:
  - 12-pad Rytm surface with planned/locked pads 5-12 before full snapshot data
  - staged Analog Four device rail entries
  - richer pad cards with grouped parameters
  - connection/readiness/safety rail improvements
  - clearer dry-run/live SEND language
  - operator command logging and error surfacing
  - snapshot list/recall surface with keyboard accessibility preserved
- Profile wizard:
  - Browse fallback with accessible status messaging
  - Add Source starts analysis flow immediately
- Backend/CLI:
  - cockpit token-file handling covered in tests
- Documentation:
  - plan doc for the local testing feedback bundle

## Review Feedback Already Addressed

Eddie requested changes because an earlier PR head broke seven existing
desktop-web tests:

- HistoryStrip lost the roving-tabindex keyboard contract.
- Wizard paste-path fallback was missing `role="status"`.

Those were fixed before the current remote head. CI now confirms `desktop-web`
and `desktop-web-e2e` pass.

## Local Workspace Caveat

The local worktree
`.worktrees/cockpit-local-testing-feedback-bundle` is not a clean source of
truth tonight. It has two sources of confusing status:

- unrelated CRLF/parity fixture dirt that must not be staged
- the branch checkout is stale relative to the pushed PR head because the final
  rebase was produced with Git plumbing and force-pushed directly

Tomorrow, trust the remote PR head first. If local inspection is needed, create a
fresh worktree from `origin/codex/cockpit-local-testing-feedback-bundle` or fetch
and inspect the remote commit directly. Do not stage the parity fixture noise.

## Recommended Tomorrow Flow

1. Check PR #145 first:
   - `gh pr view 145 --json mergeable,mergeStateStatus,reviewDecision,statusCheckRollup`
   - If Eddie approved and checks are still green, merge using the repo's normal
     squash path.
   - If it is still changes-requested, nudge Eddie; there are no unresolved
     review threads and all checks are green.
2. Avoid opening another stacked PR on top of #145 while it is blocked.
3. If work must continue while waiting, keep it read-only or local-only:
   - map the next full 12-pad parameter schema from the Analog Rytm manual and
     Overbridge screenshot
   - define the device/connection state model needed for the cockpit
   - plan profile analyzer behavior without copying copyrighted tracks
   - review PR #144 / #143 only if explicitly requested and independent
4. After #145 merges, the next logical product slice is a single larger PR for
   deeper cockpit parameter coverage and device/session UX, not multiple tiny
   stacked PRs.

## Product Direction Learned

Jose's target is not merely "a CLI wrapped in a window." The product direction is
a live-performance/studio cockpit:

- all 12 Rytm pads visible at once
- Analog Four present as a first-class connected device
- complete sound-engine controls informed by manuals and Overbridge
- mock/passive preview first, explicit arm before hardware send
- clear device connection state and safety status
- snapshots as a session timeline / recall surface
- style/reference-track inspiration that produces original mutation moves
- future queue/journal workflow for long live sets

Safety principle remains unchanged: passive preview first, mock-safe planning,
explicit `--arm` before real hardware, and no unattended hardware behavior unless
separately designed and approved.

