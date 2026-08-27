# Targeted live-kit mutation run report

Date: 2026-08-26

## Outcome

The run added first-class Rytm pad and A4 track include targets, intersected
them with independent locks, carried scope through session/WS/UI and the public
device planner seam, promoted verified Rytm captures into in-memory mutation
anchors, and retained captured A4 mutation as a blocked zero-event plan.

## Timeline and review

1. Read the repo contribution, memory, architecture, Cockpit, Rytm snapshot,
   and A4 Patch Genome surfaces.
2. Added target/scope models, session and protocol state, planner/send-plan
   filtering, UI controls, capture promotion, and focused tests.
3. Split Cockpit DTOs from the device-neutral scope after architecture review.
4. Hardened strict identifier validation, final packet invariants, real-adapter
   state preservation/metrics, and async UI rollback ordering.
5. Updated durable architecture/quickstart/status documentation and completed
   focused, broad, frontend, architecture, lint, and frozen-parity verification.

## Escalations and lessons

- The dirty capture baseline made isolated worktrees unsafe for overlapping
  files; no PR, push, merge, or fixture rewrite occurred.
- The sender needs the same target/lock invariant as the candidate generator;
  filtering only at generation time leaves stale-plan risk.
- Live CC evidence and saved-kit byte-offset evidence are different proof
  classes. Captured A4 mutation must remain blocked until the latter exists.
- Optimistic whole-state controls need generation guards because acknowledgments
  can complete out of order.

The in-scope change spans the existing Cockpit backend/frontend, shared device
planner seam, focused tests, and architecture/operator docs. Exact LOC is not
reported because this worktree already contained overlapping uncommitted
capture and Patch Genome work before the run.

## Verification

- Focused Python target/capture/planner/WS regression: 443 passed.
- Affected Python module coverage review: 100% statements and branches (670
  statements, 204 branches); its focused regression set passed 333 tests.
- Broad non-architecture fast suite: 5,213 passed, 3 skipped.
- Architecture suite excluding the repository-wide dead-symbol scanner: 693
  passed with one pre-existing warn-only `main`-symbol notice.
- Frozen V1.34 parity: 685 passed; no fixture changed and capture mode was not
  used.
- Frontend: 43 files / 519 tests passed at 100% statements, branches,
  functions, and lines; TypeScript, ESLint, and production Vite build passed.
- Ruff, Black, isort, `git diff --check`, state-schema parsing, and learned-skill
  validation passed.

The dead-symbol architecture test was separately attempted earlier in this
dirty checkout and did not complete within 180 seconds because it recursively
scans every Python file under the repository root, including large unrelated
untracked reference/artifact trees. Those user-owned trees were not moved or
deleted to force the scanner green; all other architecture tests completed.

## Phase 2 — explicitly armed Rytm output

The follow-on implemented the separately authorized Rytm Cockpit output
composition without changing the packaged Tauri default. The new manual launch
requires `--arm`, `--cockpit-live-kit-sidecar`, an exact
`--cockpit-rytm-output-port`, and `--confirm-cockpit-rytm-send`. Startup checks
the exact name but does not open it. The real adapter exposes that configured
name passively and opens it only when `apply_send_plan` receives the ready plan.

The React SEND action now shows the exact output, current plan id, actual packet
pads, and estimated message count. It sends the plan id only after operator
confirmation. Armed WS sessions reject missing, non-string, stale, or
mismatched plan confirmation before calling the adapter. A mock-safe integration
test proves that the injected output records no open and no messages after a
rejected SEND, then opens the exact port once and transmits exactly the prepared
packet count after matching confirmation.

Phase 2 verification:

- focused backend/protocol/entrypoint regression: 221 passed;
- application parser and armed-boundary regression: 242 passed;
- all Cockpit Python tests: 1,522 passed, 3 skipped;
- broad non-architecture fast suite: 5,229 passed, 3 skipped;
- architecture excluding the known repository-wide scanner: 693 passed with
  the same pre-existing warn-only `main` notice;
- frozen V1.34 parity: 685 passed with no fixture changes;
- frontend: 43 files / 522 tests at 100% statements, branches, functions, and
  lines; typecheck, ESLint, and production build passed;
- Ruff, Black, isort, and `git diff --check` passed.

No automated test imported a physical MIDI backend, opened a real port, or sent
MIDI. The operator-present capture → target one pad → lock another → low depth
→ PREPARE → confirm SEND → verify untouched pads → reload original kit rehearsal
is documented but was not executed without an operator and connected hardware.
A4 captured-kit mutation remains unchanged and fail-closed.
