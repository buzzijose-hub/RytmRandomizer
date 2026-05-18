# RytmRandomizer — Simplification Plan (Maximum-Parallel Execution)

**Status:** Proposed · 2026-05-18
**Base:** `modularize-v1.34` @ `3e2a3d5`
**Scope:** Moderate refactor — add abstractions PR #21 needs + finish in-flight type-tightening prior PRs flagged.
**Mode:** Cooperative with PR #21. Codex rebases onto these abstractions; PR #21 shrinks from ~30k LOC to ~5–8k.
**Execution model:** Each workstream is an **isolated git worktree** with a dedicated agent crew. Independent workstreams run **simultaneously** in background tasks. A top-level orchestrator (Claude) drives the entire pipeline end-to-end with **no human approval gates** — auto-merge on green CI, auto-rebase on cascade conflicts, auto-escalate to specialists on failure, and auto-loop until all 7 PRs are merged.

---

## Why this exists

Two things came together:

1. **The cleanup batch (PRs #22–#28) exposed real bloat** the audits couldn't touch without changing semantics: ~3,600 LOC of dead code already removed, the V1.34 monolith retired, but the package still has duck-typed boundaries (`Sender = Any`, mixins that read "off `self` but do not declare them"), a 1,374-LOC behavior-pad-lane registry, and an 8-arm `if/elif` tail on `shell.dispatch` that the PR-#15 refactor explicitly punted on.

2. **PR #21 sprawled into ~33 new top-level files** because four abstractions don't exist: no `Device` Protocol, no `SnapshotDecoder[T]`/`MutationPlanner[T]` base, no CLI command registry, no `PassiveReportFormatter`.

**Cooperative goal:** land the abstractions on base; codex rebases PR #21 against them.

**Non-goal:** changing V1.34 byte-level behavior. The 11 parity-API symbols (`docs/ARCHITECTURE.md` §8) are untouchable; engine→wire byte sequence stays identical; JSON fixtures in `tests/fixtures/v134_parity/` must continue to match.

---

## Gated requirements (apply to every WS — no exceptions)

These three gates are baked into every workstream's acceptance criteria and into the orchestrator's state machine. A WS does **not** transition from `reviewing` → `pr_open` until all three gates pass locally; if any gate fails in CI after PR open, the orchestrator auto-reverts that WS's last commit and re-enters `implementing`.

| Gate | Threshold | Enforcement |
|---|---|---|
| **Branch coverage on touched files** | **100%** | `pytest --cov=<touched paths> --cov-branch --cov-fail-under=100`. The orchestrator computes the touched-file list from `git diff --name-only origin/modularize-v1.34...HEAD -- 'rytm_randomizer/*.py'` and passes it to `--cov`. The repo's existing 87% floor in `.coveragerc` is a ratchet for the whole package and stays unchanged; the WS-local 100% gate is **stricter** and applies only to new or modified code. |
| **V1.34 parity** | All **505 JSON parity fixtures** in `tests/fixtures/v134_parity/` byte-identical | `pytest tests/test_engines_pad*.py tests/test_group_runner.py tests/test_scene_runner.py` green. The orchestrator never sets `PARITY_CAPTURE_MODE=1` in any WS — capture is a deliberate, separate workstream. |
| **Lint / type / format** | clean | `python -m ruff check . && python -m black --check . && python -m isort --profile black --check-only . && python -m pyright --strict <touched paths>`. The systemic black target-py311 fix from PR #28 means dev formatting == CI formatting. |

**Why 100% branch coverage on touched code (not the whole package):**
- The whole-package floor is a ratchet — it can only go up, never down. Lowering it would break the cleanup-batch invariant.
- New code at 100% means the touched-paths floor ratchets up the package floor over time, naturally and without negotiation.
- Branch coverage (not just line) catches "what if `resolved_bounds is None`" and "what if depth=0" — the exact corner cases the duck-typed mixin contract currently lets slip.
- Existing untouched files keep their current coverage; we are not retro-bumping them.

**How the orchestrator computes touched files:**
```powershell
$touched = git diff --name-only origin/modularize-v1.34...HEAD -- 'rytm_randomizer/*.py'
$cov_args = $touched | ForEach-Object { "--cov=$($_ -replace '/', '.' -replace '\.py$','')" }
pytest @cov_args --cov-branch --cov-fail-under=100 --cov-report=term-missing
```

If `--cov-fail-under=100` fails, the `tdd-guide` agent is re-dispatched with the missing-branch output to write the gap-closing tests.

---

## What's already DRY (don't touch)

- **Domain data** is single-source in `rytm_randomizer/data/`. Top-level `profiles.py`/`scenes.py`/`constants.py` derive from it. Nothing to do.
- **Pad-engine helpers** consolidated in `engines/_runtime.py` (PR H1). Still mixin-shaped (see WS-S2) but the duplication is gone.
- **Shell dispatch** for 84 of 92 arms is already a table (`shell._DISPATCH`, PR #15/H2). Eight special-shaped arms remain inline; closing that gap is WS-S3.

---

## Autonomous execution contract (no human in the loop)

The orchestrator runs from PR-#29-merged through PR-#7-of-7-merged with **zero human approvals**. The contract:

### Kickoff trigger

A single message starts the entire pipeline. Two equivalent triggers:

- **Manual one-shot:** user runs `/loop run docs/SIMPLIFICATION_PLAN.md` (the loop skill resumes via the `<<autonomous-loop-dynamic>>` sentinel each wake-up).
- **Scheduled:** `CronCreate` arms an autonomous loop with the sentinel `<<autonomous-loop>>`; first firing is the kickoff.

### Self-driving decision rules (deterministic, no AskUserQuestion)

| Situation | Auto-action | Escalation threshold |
|---|---|---|
| Worktree branch needs creating | `git worktree add` off latest `origin/modularize-v1.34` | n/a |
| Local tests pass + lint clean | `git push -u origin <branch>` then `gh pr create` | n/a |
| CI green + req=SUCCESS | `gh pr merge --squash` (no --auto, immediate) | n/a |
| CI lint fails on black target-version | Re-run `python -m black --target-version=py311` and force-push | After 2 attempts, escalate to `build-error-resolver` |
| CI test fails (regression in parity fixtures) | `git revert` the local commit, dispatch `tdd-guide` to rewrite the change behind the failing test | After 2 attempts, escalate to `architect` to redesign the WS |
| CI test fails (regression in cleanup-tests like `test_real_midi_adapter_boundary`) | Inspect the failure, edit the test reference list, force-push | After 2 attempts, escalate to `build-error-resolver` |
| Cascade conflict on `docs/STATUS.md` "Recent Cleanup" | `reset --hard origin/modularize-v1.34` + cherry-pick own commits + auto-resolve STATUS.md by keeping both entries + force-push | n/a (deterministic, proven pattern from PRs #22-#28) |
| Mergeability state UNKNOWN | Wait 10s, recheck | After 3 polls, fall back to monitor |
| PR stays `req=pending` >20 min after green checks | Inspect `propagate-required-checks` job; if missing, invoke the `github-token-no-workflow-trigger` skill's Checks API propagation | After 1 escalation, leave PR open and log incident |
| `architect` agent design conflicts with parity-fixture acceptance | Architect designs FOR parity, never against it. Conflict means design is wrong → re-spawn architect with the failing fixture attached | After 2 attempts, drop the WS to "blocked" state and continue with remaining WSes |

**No question mark ever reaches the user.** If the orchestrator hits a state not enumerated above, it logs the state to `docs/SIMPLIFICATION_RUN_LOG.md` and continues with the next eligible action.

### Loop semantics

- **Outer loop:** `<<autonomous-loop-dynamic>>` re-enters the orchestrator on each `ScheduleWakeup` firing. Wake-up cadence: **1200s** while waiting on CI (one cache miss buys ~20 min of wait); **60-90s** when actively reconciling PR cascade conflicts.
- **Termination condition:** all 7 simplification PRs are MERGED **and** the codex hand-off issue is opened against PR #21. The orchestrator writes "DONE" to `docs/SIMPLIFICATION_RUN_LOG.md`, calls `TaskStop` on all monitors, and stops scheduling wake-ups.
- **Hard time budget:** 72 hours wall-clock. If not done at +72h, write "BUDGET_EXCEEDED" to the run log with current state snapshot and stop. (Soft target: ~24h based on the 6-PR cleanup batch cadence.)

### Persistent state files (survive context compaction)

All state the orchestrator needs is on disk, not in conversation context:

- `docs/SIMPLIFICATION_PLAN.md` (this file) — the playbook.
- `docs/SIMPLIFICATION_RUN_LOG.md` — append-only event log: timestamps, WS state transitions, escalations, errors. Created on first wake-up. Used to recover state after compaction.
- `docs/SIMPLIFICATION_STATE.json` — current WS states (`pending|planning|tdd|implementing|reviewing|pr_open|ci_running|merged|blocked`), branch heads, PR numbers, last-merge SHAs. Atomic write per transition.
- `tests/fixtures/v134_parity/` — 505 JSON goldens. **The orchestrator never modifies these** without invoking `PARITY_CAPTURE_MODE=1` deliberately; a parity-fixture diff in a code-only WS is treated as a regression, not an intended change.

After compaction, the orchestrator resumes by: reading `SIMPLIFICATION_STATE.json`, running `gh pr list --search head:refactor/ --json number,mergeable,mergeStateStatus`, and reconciling.

### Permission profile

The kickoff message MUST be launched with permission mode `acceptEdits` (or higher) so the orchestrator can: create worktrees, edit files, run `gh pr create` / `gh pr merge`, force-push branches it owns, delete merged branches, and write to `docs/SIMPLIFICATION_RUN_LOG.md`. It **does not** need to be `bypassPermissions` — every tool it uses is in the allowlist for `acceptEdits` once branches it owns are scoped to `refactor/*` and `docs/simplification-*`.

The orchestrator **must refuse** to: force-push to `modularize-v1.34`, delete branches it doesn't own, run `gh pr close` on PR #21 (codex's), or rewrite history on already-merged PRs. These are hard-coded blocklist items, not approval-gated.

### Codex coordination (still no human in the loop)

PR #21's evolution is monitored by a persistent `Monitor` task. When codex pushes a new commit to `codex/dual-machine-mock-bridge`, the orchestrator does **not** intervene — codex is on its own track. The orchestrator only opens the hand-off issue **once Wave 3 merges**. The issue body is generated from `SIMPLIFICATION_STATE.json` (final SHAs + module list) using a templated `gh api repos/.../issues -X POST`.

If codex's PR #21 has merged by the time Wave 3 lands (i.e. they didn't wait for us), the orchestrator logs "PR_21_LANDED_FIRST" and skips the hand-off issue.

---

## Workstream graph

```
WAVE 1 (4 streams, all parallel — disjoint files, no cross-deps)
  WS-S1  MidiSender Protocol         midi_io.py, mock_midi.py, real_midi_adapter.py
  WS-S2  PadRuntime Protocol         engines/_runtime.py + engines/pad{1-4}.py
  WS-S3  Close shell.dispatch tail   shell.py
  WS-S4  PassiveReportFormatter      new reports/formatter.py + shim sites

WAVE 2 (2 streams, parallel after Wave 1)
  WS-S5  Device Protocol + registry  needs: WS-S1
  WS-S6  Generic Elektron SysEx      needs: WS-S5

WAVE 3 (1 stream, gated)
  WS-S7  CLI command registry        needs: WS-S4, WS-S6

WAVE 4 (1 stream, gated on all 7 merged) — autonomous learning + hand-off
  WS-L   Learning extraction + run report      saves to .claude/skills, .claude/rules
  WS-H   PR #21 hand-off issue                 auto-generated from final state
```

Each WS passes through the same 11-phase pipeline (plan → tdd → implement → **coverage gate** → review × 3 in parallel → **docs** → PR open → CI → merge), with mandatory 100% branch coverage on touched files and mandatory `doc-updater` commit before PR opens.

Wall-clock target: **~3–4 days** (vs ~2 weeks sequential), driven by Wave-1 parallelism and the merge cascade pattern proven in PRs #22–#28.

---

## Agent crew per workstream

Every workstream uses the same crew shape — the only difference is which plugin agents Claude (orchestrator) dispatches in parallel for that workstream's worktree:

| Phase | Agent | Plugin | What it does |
|---|---|---|---|
| 0. Worktree setup | (orchestrator) | — | `git worktree add` an isolated branch off `modularize-v1.34`. |
| 1. Plan | `planner` | `everything-claude-code` | Reads the WS spec from this doc, produces a step-by-step plan with file list and acceptance criteria. |
| 2. Test-first | `tdd-guide` | `everything-claude-code` | Writes the failing tests for the new Protocol/registry/formatter from the plan. RED. |
| 3. Implement | (orchestrator) | — | Writes the minimum code to turn the new tests GREEN while keeping the 505 V1.34 parity fixtures green. |
| 4. **Branch-coverage gate** | (orchestrator) + `tdd-guide` if gap | — | Runs `pytest --cov=<touched paths> --cov-branch --cov-fail-under=100`. If gaps exist, re-dispatches `tdd-guide` with the missing-branch report. Loops up to 2× before escalating to `architect`. **Hard gate — no PR opens until 100%.** |
| 5. Type/style check | `python-reviewer` | `everything-claude-code` | Confirms PEP 8, type annotations, Pythonic idioms, immutability where appropriate. |
| 6. Code review | `code-reviewer` | `everything-claude-code` | Catches CRITICAL/HIGH issues. |
| 7. Security review | `security-reviewer` | `everything-claude-code` | Required only for WS-S1/S5/S7 (boundary/IO/registry changes). |
| 8. Build/CI guard | `build-error-resolver` | `everything-claude-code` | Stands by; engaged only if CI fails. |
| 9. **Documentation update** | `doc-updater` | `everything-claude-code` | Updates `docs/STATUS.md` "Recent Cleanup" entry. Updates `docs/ARCHITECTURE.md` if the WS touches a documented boundary (S1/S2/S5/S6/S7 all do). Updates `docs/CODEMAPS/*` if the WS adds new top-level modules. **Required — not optional.** Runs before PR open. |
| 10. PR open | (orchestrator) | — | `gh pr create` with WS-specific body referencing this plan + STATUS.md entry. |

Phases 1, 2, 5, 6, 7 run in parallel where their inputs are independent. Phase 4 (coverage gate) and Phase 9 (docs) are blocking — no PR opens until both pass. Phase 8 is on standby and only engages on CI failure.

---

## Parallel dispatch protocol (the orchestrator's job)

For **Wave 1**, the orchestrator does this in a **single message** with multiple Agent calls:

```
# Pseudocode — one message, four parallel Agent dispatches
Agent(WS-S1 planner) in background
Agent(WS-S2 planner) in background
Agent(WS-S3 planner) in background
Agent(WS-S4 planner) in background
```

Once all four planner agents report back, the orchestrator dispatches the next batch — again in a single message:

```
Agent(WS-S1 tdd-guide) in background
Agent(WS-S2 tdd-guide) in background
Agent(WS-S3 tdd-guide) in background
Agent(WS-S4 tdd-guide) in background
```

While TDD agents write tests, the orchestrator can pre-dispatch **architecture review** for WS-S5/WS-S6 (Wave 2) so design feedback lands the moment Wave 1 unblocks them.

For **Wave 1 implementation**, the orchestrator (or a `claude` subagent per worktree) writes code directly in each worktree, also in parallel — one Bash/Edit per worktree's path. PowerShell/Bash invocations are issued to disjoint paths, so they can run concurrently.

**Review and merge cascade** runs persistent via a `Monitor` task watching all open PRs (the same `bmawysm6c`-style monitor used during the last batch).

---

## WS-S1 — `MidiSender` Protocol

**Worktree:** `RytmRandomizer-worktrees/ws-s1-midi-sender-protocol`
**Branch:** `refactor/midi-sender-protocol`
**Owns:** `rytm_randomizer/midi_io.py`, `rytm_randomizer/mock_midi.py`, `rytm_randomizer/real_midi_adapter.py` (signatures only).

**Replaces:** `Sender = Any` everywhere.

**Adds:**
```python
@runtime_checkable
class MidiSender(Protocol):
    """Anything with .send(MidiMessage) works.

    Satisfied by: mido.ports.BaseOutput, MockMidiSender, RealMidiSender.
    """
    def send(self, message: object) -> None: ...
```

**Changes:** every `Sender = Any` → `MidiSender`. Replace class-name sniff (`midi_io.py:96-109`) with `isinstance(out, MockMidiSender)`.

**Agent crew (parallel where possible):**
1. `everything-claude-code:planner` — produce file-level plan (10 min).
2. `everything-claude-code:tdd-guide` — write `tests/test_midi_sender_protocol.py` asserting `runtime_checkable` against all three implementations. (15 min, parallel with planner output digest.)
3. Orchestrator implements the Protocol + annotation changes. (30 min.)
4. **Parallel:**
   - `everything-claude-code:python-reviewer` reviews Python idioms.
   - `everything-claude-code:code-reviewer` reviews boundary discipline.
   - `everything-claude-code:security-reviewer` reviews the runtime_checkable choice (Protocols with `runtime_checkable` skip strict structural checks).
5. `everything-claude-code:doc-updater` updates STATUS.md.

**Acceptance:** all three senders pass `isinstance(_, MidiSender)`; pyright clean on annotated surfaces; 2,000+ tests + 505 parity fixtures green.

**Risk:** very low. Pure type tightening.

---

## WS-S2 — `PadRuntime` Protocol (replace duck-typed mixin contract)

**Worktree:** `RytmRandomizer-worktrees/ws-s2-pad-runtime-protocol`
**Branch:** `refactor/pad-runtime-protocol`
**Owns:** `rytm_randomizer/engines/_runtime.py`, `rytm_randomizer/engines/pad{1-4}.py`.

**Today:** `engines/_runtime.py:36` says "the mixins are duck-typed — they read these off `self` but do not declare them." Pyright sees nothing.

**Adds:** `PadRuntimeState` Protocol declaring all 11 attributes. Mixin methods become module-level functions taking `state: PadRuntimeState`.

**Agent crew:**
1. `everything-claude-code:architect` — design the Protocol surface so PR #21's pad-12 engine fits without churn. (20 min.)
2. `everything-claude-code:tdd-guide` — write Protocol-conformance tests. (parallel with #1.)
3. Orchestrator refactors each `pad{1-4}.py` `__init__` to instantiate a `PadRuntimeState` dataclass and forward to module-level helpers. (45 min.)
4. **Parallel:**
   - `everything-claude-code:python-reviewer`
   - `everything-claude-code:code-reviewer`
   - **CRITICAL:** run all 505 V1.34 parity fixtures locally before pushing. Byte-identical is non-negotiable.
5. `everything-claude-code:doc-updater`.

**Acceptance:** parity fixtures byte-identical; pyright sees the contract; mixin disappears.

**Risk:** medium. Touches every engine constructor. Parity tests are the safety net.

---

## WS-S3 — Close `shell.dispatch` 8-arm tail

**Worktree:** `RytmRandomizer-worktrees/ws-s3-shell-dispatch-close`
**Branch:** `refactor/shell-dispatch-close`
**Owns:** `rytm_randomizer/shell.py`.

**Today:** 8 special-shaped arms (`q`, `t`, `p`, scene-lookup, depth-guard, depth-prompt, unknown-fallback) inline in `dispatch()` (`shell.py:609-695`).

**Adds:** `DispatchEntry` dataclass with `kind: Literal["simple","quit","reselect","scene_lookup","depth_guard","depth_prompt","unknown"]`. `dispatch()` branches on `entry.kind`.

**Agent crew:**
1. `everything-claude-code:architect` — confirm the `kind` taxonomy covers PR #21's expected 5–7 new command shapes. (15 min.)
2. `everything-claude-code:tdd-guide` — characterization tests for each `kind`, asserting current behavior. (parallel.)
3. Orchestrator refactors. (45 min.)
4. **Parallel:**
   - `everything-claude-code:code-reviewer`
   - `everything-claude-code:python-reviewer`
5. `everything-claude-code:doc-updater`.

**Acceptance:** behavior byte-identical (existing 55 CLI golden tests + dispatch char tests); LOC drops ~120.

**Risk:** low–medium. Depth-prompt arms call stdin; the entry payload must carry that as data not a closure.

---

## WS-S4 — `PassiveReportFormatter`

**Worktree:** `RytmRandomizer-worktrees/ws-s4-passive-report-formatter`
**Branch:** `refactor/passive-report-formatter`
**Owns:** new `rytm_randomizer/reports/formatter.py`; thin shim updates at use sites in `reports.py`, `inspection.py`, `project_status_report.py`.

**Adds:** `PassiveReportHeader` dataclass + `PASSIVE_FOOTER` constant + `render_passive_report()` helper.

**Agent crew:**
1. `everything-claude-code:planner`
2. `everything-claude-code:tdd-guide` — golden-string compare on current report output.
3. Orchestrator extracts.
4. `everything-claude-code:refactor-cleaner` — runs after to find any other near-duplicate "Safety:" footers in the codebase missed by the extraction.
5. `everything-claude-code:doc-updater`.

**Acceptance:** byte-identical report text; LOC reduction visible.

**Risk:** very low.

---

## WS-S5 — `Device` Protocol + registry (THE PR-#21 UNBLOCKER)

**Worktree:** `RytmRandomizer-worktrees/ws-s5-device-protocol`
**Branch:** `refactor/device-protocol-registry`
**Owns:** new `rytm_randomizer/devices/{base,registry,analog_rytm}.py`.
**Depends on:** WS-S1 merged (uses `MidiSender`).

**Adds:**
```python
class Device(Protocol):
    device_id: str
    display_name: str
    default_midi_channel: int
    track_count: int
    sysex_manufacturer_id: bytes

    def decode_snapshot(self, raw: bytes, slot: int) -> Snapshot: ...
    def plan_mutation(self, snapshot: Snapshot, depth: int) -> MutationPlan: ...
    def to_mock_messages(self, plan: MutationPlan) -> list[MidiMessage]: ...
    def to_cc_messages(self, plan: MutationPlan) -> Iterable[ControlChange]: ...
```

Plus `register_device` / `get_device` / `all_devices`. `AnalogRytmDevice` wraps existing `data/`, `engines/`, `randomization.py`.

**Agent crew:**
1. `everything-claude-code:architect` — **load-bearing decision.** Surface area must fit Rytm AND A4 cleanly. Run before tests. (45 min, blocking.)
2. `everything-claude-code:tdd-guide` — Protocol-conformance tests for `AnalogRytmDevice`.
3. Orchestrator implements wrapper.
4. **Parallel:**
   - `everything-claude-code:code-reviewer`
   - `everything-claude-code:security-reviewer` — boundary protocol: confirm device methods can't bypass `MidiSender`.
   - `everything-claude-code:python-reviewer` — Protocol vs ABC choice rationale.
5. `everything-claude-code:doc-updater` — adds section 9 to `docs/ARCHITECTURE.md`.

**Acceptance:** `get_device("analog_rytm_mk2").to_mock_messages(plan)` byte-identical to current direct engine path (new golden test); 505 parity fixtures still green.

**Risk:** medium. Protocol surface is the load-bearing decision. Mitigation: architect agent's first pass is reviewed against the PR-#21 file list before tests start.

---

## WS-S6 — Generic Elektron SysEx envelope + `SnapshotDecoder[T]`/`MutationPlanner[T]`

**Worktree:** `RytmRandomizer-worktrees/ws-s6-snapshot-envelope`
**Branch:** `refactor/snapshot-envelope`
**Owns:** new `rytm_randomizer/snapshot/{envelope,decoder,planner,mock_runtime}.py`.
**Depends on:** WS-S5 (uses `Device`).

**Adds:** `unpack_elektron_7bit`, `find_kit_record`, `read_ascii_name`, `format_manufacturer_id` as generic helpers. `SnapshotDecoder[T]` / `MutationPlanner[T]` Protocols.

**Agent crew:** identical shape to WS-S5. Architect agent first; `tdd-guide` ensures the relocated helpers produce byte-identical output to the originals (V1.34 parity fixtures are the source of truth).

**Acceptance:** existing Rytm snapshot path uses the relocated helpers without behavior change.

**Risk:** medium. Byte-level equivalence is the gate.

---

## WS-S7 — CLI command registry (the diff-killer for codex)

**Worktree:** `RytmRandomizer-worktrees/ws-s7-cli-registry`
**Branch:** `refactor/cli-command-registry`
**Owns:** `rytm_randomizer/cli.py` (refactor) + new `rytm_randomizer/cli/registry.py` + `rytm_randomizer/cli/commands/<name>.py` per existing command.
**Depends on:** WS-S4 (uses `PassiveReportFormatter`), WS-S6 (uses snapshot helpers if any CLI command surfaces them).

**Adds:** `CliCommand` dataclass + registry. Each existing command moves to `cli/commands/<name>.py` with a `register()` call at the bottom.

**Agent crew:**
1. `everything-claude-code:planner` — split the existing 453-LOC `cli.py` into ~12 command files.
2. `everything-claude-code:tdd-guide` — leverage the 55-test golden suite from PR #24 to assert byte-identical output for every command.
3. Orchestrator refactors.
4. **Parallel:**
   - `everything-claude-code:code-reviewer`
   - `everything-claude-code:python-reviewer`
   - `everything-claude-code:refactor-cleaner` — after refactor, find any dead helpers in old `cli.py` to remove.
5. `everything-claude-code:doc-updater`.

**Acceptance:** PR #24's 55 golden tests pass unchanged; `cli.py` is a thin dispatcher; new commands added without touching `cli.py`.

**Risk:** medium. User-facing surface. Golden tests are the safety net.

---

## Orchestrator state machine (self-executing, no human gates)

The orchestrator is a deterministic state machine. Each wake-up it: reads `docs/SIMPLIFICATION_STATE.json`, queries `gh pr list` for live state, picks the next eligible action, executes it, atomically updates the state file, then either dispatches background tasks and exits (waiting for notifications) or calls `ScheduleWakeup` for a long-fallback re-entry.

### State transitions per WS

```
pending ─┬─ (Wave 1: always) ──> planning
         └─ (Wave 2/3: deps merged) ──> planning

planning      ──(planner|architect agent returns plan)──>       tdd
tdd           ──(tdd-guide writes failing tests, local RED)──>  implementing
implementing  ──(orchestrator codes + local pytest GREEN)──>    coverage_gate
coverage_gate ──(100% branch on touched files)──>               reviewing
              └─(gap)──> tdd (re-dispatch tdd-guide w/ gap report; max 2 retries)
reviewing     ──(reviewer agents return ≤ MEDIUM issues)──>     docs
              └─(HIGH/CRITICAL issue)──> implementing (max 2 retries)
docs          ──(doc-updater commits STATUS.md / ARCHITECTURE.md / CODEMAPS)──> pr_open
pr_open       ──(CI green + req=SUCCESS)──> merging
merging       ──(gh pr merge --squash returns MERGED)──> merged

(any state) ──(cascade DIRTY)──> auto-rebase loop ──> pr_open
(any state) ──(2× retry exhausted in any phase)──> blocked

merged (all 7 WSes) ──> learning ──> handoff ──> DONE
```

`coverage_gate` and `docs` are **first-class blocking states** — they are not optional sub-steps of `reviewing`. A WS cannot reach `pr_open` without passing both.

`blocked` is terminal for that WS only; the orchestrator continues with the remaining WSes.

### Wave-1 kickoff (single message, 4-parallel)

On the first eligible wake-up after PR #29 merges, the orchestrator does this in **one tool-call message**:

```
# 4 parallel worktree creates (PowerShell, no inter-deps)
git worktree add RytmRandomizer-worktrees/ws-s1-midi-sender-protocol     -b refactor/midi-sender-protocol      origin/modularize-v1.34
git worktree add RytmRandomizer-worktrees/ws-s2-pad-runtime-protocol     -b refactor/pad-runtime-protocol      origin/modularize-v1.34
git worktree add RytmRandomizer-worktrees/ws-s3-shell-dispatch-close     -b refactor/shell-dispatch-close      origin/modularize-v1.34
git worktree add RytmRandomizer-worktrees/ws-s4-passive-report-formatter -b refactor/passive-report-formatter  origin/modularize-v1.34
```

Same message also dispatches 4 background planner/architect agents — one per WS — and the persistent CI monitor. State file updated to `planning` for all four. Orchestrator exits the turn.

### Wave-1 phase fanout (event-driven, no polling)

When a planner agent completes (notification arrives), orchestrator:

1. Reads its output, atomically transitions that WS to `tdd`.
2. Dispatches the `tdd-guide` agent for that WS (background).
3. Exits turn.

When `tdd-guide` completes:

1. Orchestrator runs the failing tests locally to confirm RED, transitions to `implementing`.
2. Writes the minimum code to GREEN (Edit calls in that WS's worktree).
3. Runs `pytest -o addopts='' --no-header -q` + parity fixtures locally. If green, transitions to `reviewing`.
4. Dispatches `code-reviewer` + `python-reviewer` + (for WS-S1, S5, S7) `security-reviewer` in **one parallel message**.
5. Exits turn.

When all reviewers return: if no HIGH/CRITICAL issues, orchestrator dispatches `doc-updater`, opens the PR, transitions to `pr_open`. If HIGH/CRITICAL: re-enter `implementing` with the reviewer feedback; second retry; if still failing, mark `blocked` and log to run log.

### Auto-merge cascade (proven pattern from PRs #22–#28)

Persistent CI monitor pages the orchestrator on every PR state change. When a WS's PR reaches `MERGEABLE + req=SUCCESS`:

```
gh pr merge <N> --squash
# Verify MERGED
# Atomic state update: WS -> merged
# Check all other WS PRs for DIRTY state caused by this merge:
foreach DIRTY PR:
  - reset --hard origin/modularize-v1.34
  - cherry-pick own commits
  - auto-resolve docs/STATUS.md "Recent Cleanup" (keep-both rule)
  - force-push
```

This loop is **fully autonomous** — it's the same logic that handled the 6-PR cascade in ~3 hours. No approval gates anywhere.

### Wave-2/3 gating

`SIMPLIFICATION_STATE.json` tracks `deps_satisfied` per WS. The state machine doesn't transition a Wave-2 WS out of `pending` until its dependency rows show `merged`. The transition itself is event-driven: the merge action triggers a dependency-recompute, which may flip the next wave's WSes to `planning` in the same turn.

`architect` for WS-S5 and WS-S6 is **mandatory and blocking** — the architect agent runs solo (not parallel with TDD) because its output reshapes the test contracts. The 45-min architect run is the only true single-threaded bottleneck.

### Final-phase 1: Learning extraction (mandatory before hand-off)

Once all 7 WSes are `merged`, the orchestrator enters the `learning` state. The goal is to capture what was non-obvious so the next autonomous run is faster and cleaner. This is **not** optional — it's the same kind of "save the lesson while it's fresh" practice that produced `python_tooling_pitfalls.md` and the `github-token-no-workflow-trigger` skill during the cleanup batch.

**Step 1 — Aggregate signal from `docs/SIMPLIFICATION_RUN_LOG.md`:**

The orchestrator reads the run log and identifies:
- Every escalation (which gate caused it, which agent resolved it).
- Every cascade-rebase event (frequency, which files conflicted).
- Every retry loop (which WS, which phase, root cause).
- Every "blocked" state that recovered (and how).
- Every unexpected agent output (planner produced wrong scope, architect missed a constraint, etc.).
- CI failure modes (lint drift, parity regression, coverage gap, timeout).

**Step 2 — Dispatch `everything-claude-code:learn-eval` per extractable pattern:**

For each pattern that recurred 2+ times or caused a >1-hour delay, the orchestrator dispatches the `learn-eval` skill (which extends `/learn` with a quality gate). The skill self-evaluates with the rubric (Specificity / Actionability / Scope Fit / Non-redundancy / Coverage, each scored 1–5) and only saves at score ≥ 3 on every dimension.

**Step 3 — Save outputs to the repo (not user home):**

| Output | Path | Format |
|---|---|---|
| Project skills | `.claude/skills/learned/<name>/SKILL.md` | One file per pattern; YAML frontmatter + body. |
| Project rules | `.claude/rules/<topic>.md` | E.g. `.claude/rules/parity-fixture-discipline.md`, `.claude/rules/coverage-gate-100pct.md`. |
| Agent memory updates | `.claude/CLAUDE.md` | Append a "Learned in simplification run" section if any rules generalize beyond skills. |
| Run report | `docs/SIMPLIFICATION_RUN_REPORT.md` | Human-readable summary: timeline, escalations, lessons, LOC impact, agent-hours. |

**Step 4 — Memory file updates (project scope):**

The orchestrator updates the project-scoped memory directory (`.claude/projects/<project-id>/memory/`) with new entries for:
- Workflow patterns that worked (auto-rebase cascade, monitor-driven merge).
- Tooling gotchas discovered (extends `python_tooling_pitfalls.md` from the cleanup batch).
- Architecture decisions (Protocol vs ABC choices, Wave-1 disjoint-file ownership pattern).

**Step 5 — Commit the learnings as a final PR:**

The orchestrator creates one final PR titled `docs(learnings): capture autonomous simplification-run lessons` containing:
- `.claude/skills/learned/*/SKILL.md` additions.
- `.claude/rules/*.md` additions.
- `docs/SIMPLIFICATION_RUN_REPORT.md`.
- Updated `.claude/CLAUDE.md`.

This PR follows the same gated pipeline (100% coverage doesn't apply — it's docs/skills only; lint/format do).

**Why this matters:** the cleanup batch produced exactly two reusable artifacts (`python_tooling_pitfalls.md` and `github-token-no-workflow-trigger/SKILL.md`) and both have prevented recurring issues. The simplification run will produce more — capturing them is the difference between a one-shot effort and a permanently faster pipeline.

---

### Final-phase 2: Hand-off to codex (automatic, no human)

After the learning PR merges, the orchestrator's final action is:

1. Read `SIMPLIFICATION_STATE.json` to get final SHAs and module list.
2. Render hand-off issue body from a template (the issue body below, with SHA placeholders filled).
3. `gh issue create --repo buzzijose-hub/RytmRandomizer --title "PR #21 rebase guide: WS-S1..WS-S7 landed" --body-file <rendered>`.
4. (Optional) `gh pr comment 21 --body "Hand-off issue: #<NN>"` so codex sees it on PR #21.
5. Write "DONE" + final timestamps to `docs/SIMPLIFICATION_RUN_LOG.md`.
6. `TaskStop` on all monitors. No further `ScheduleWakeup`.

### Hand-off issue body template

The orchestrator generates this from state at run time:

> PR #21 rebase guide (post-WS-S1..WS-S7):
> - Your `analog_four_*` 8 files → 1 file `devices/analog_four.py` + data table in `data/analog_four_param_maps.py`. Register `AnalogFourDevice(Device)`.
> - Your `dual_machine_mock_bridge.py` → one-line generic bridge over `all_devices()`.
> - Your 6 guarded/hardware sender pairs → `GuardedSender[Device]` base + per-device adapters (~30 LOC each).
> - Your +1,313-line CLI additions → 12 files under `cli/commands/`, each ~30 LOC.
> - Your snapshot/decoder/planner files → use `snapshot/envelope.py` helpers; drop the duplicated `_find_kit_record`/`_unpack_elektron_7bit`.
>
> Expected diff after rebase: ~5–8k LOC.

---

## Background monitors

One persistent `Monitor` task watches all in-flight WS PRs and pages the orchestrator when any reaches `req=SUCCESS`. Identical pattern to the cleanup batch's `bmawysm6c` monitor.

A second persistent `Monitor` watches PR #21's branch for codex pushes; pages the orchestrator when codex rebases.

---

## Verification at each wave (all three gates required)

Every WS, every wave: **100% branch coverage on touched files** + **505 parity fixtures byte-identical** + **lint/black/isort/pyright --strict clean** + **doc-updater commit landed**. Per-wave additions:

- **Wave 1 merge:** clean venv → `pip install -e ".[dev]"` → `pytest` 2,000+ tests green → `pyright --strict` clean on the new Protocol surfaces → CI matrix green on all 3 OSs → `docs/STATUS.md` "Recent Cleanup" entries land for S1/S2/S3/S4.
- **Wave 2 merge:** `AnalogRytmDevice.to_mock_messages(plan)` byte-identical to current direct engine path (new golden test); `snapshot/envelope.py` helpers byte-identical to originals; `docs/ARCHITECTURE.md` section 9 ("Device protocol") added.
- **Wave 3 merge:** PR #24's 55 CLI golden tests pass unchanged; new command can be added by dropping a file in `cli/commands/` with zero `cli.py` change (demonstration test); `docs/ARCHITECTURE.md` section 10 ("CLI command registry") added.
- **Learning PR merge:** `.claude/skills/learned/` and `.claude/rules/` populated; `docs/SIMPLIFICATION_RUN_REPORT.md` complete; `.claude/CLAUDE.md` updated.
- **After hand-off:** codex's rebased PR #21 is **<10k LOC** (or "PR_21_LANDED_FIRST" was logged).

---

## Out of scope (explicit non-goals)

- **Collapsing the four pad engines** — "Ambitious" option declined. Each `engines/pad{1-4}.py` stays as-is.
- **Pyright as a CI gate** — separate workstream once Protocols land.
- **PR #21's `essence_*` family** — natural cluster, codex relocates it during rebase.
- **The 11 V1.34 parity-API symbols** (`docs/ARCHITECTURE.md` §8). Untouched.

---

## Why this beats sequential

- Wave 1's 4 streams touch disjoint files. Their planners, TDD agents, code-reviewers, and python-reviewers all run in parallel — that's **~16 agents in flight simultaneously** at the review peak, vs 4 sequentially.
- Wave 2's architect-first gate is the only true serialization point; after architect approval, TDD + impl + review parallelizes again.
- The cleanup batch (PRs #22–#28) merged 6 PRs in ~3 hours using this same monitor-driven cascade pattern. 7 simplification PRs should land in ~1 day of focused orchestration.
- Codex receives a clean rebase guide instead of a 30k-LOC review. PR #21 ships in days, not weeks.
- **Autonomy** means the human's time investment is the kickoff message + 1 PR-#29 approval, not the 24+ hours of cascade-merging that would otherwise need a human in the loop.

---

## How to launch (single command)

After PR #29 is merged, the entire pipeline starts with one message to a fresh Claude Code session:

```
/loop run docs/SIMPLIFICATION_PLAN.md

Read the plan, then start at the "Autonomous execution contract" section.
Create docs/SIMPLIFICATION_STATE.json with all 7 WSes in "pending",
docs/SIMPLIFICATION_RUN_LOG.md with a kickoff entry, and execute the
Wave-1 kickoff in your next turn. Run until "DONE" is written to the
log file. Do not ask the user any questions; the contract is the
playbook.
```

Equivalent autonomous-cron form (no human present at kickoff):

```
CronCreate: every 1h, prompt = "<<autonomous-loop>>",
            description = "RytmRandomizer simplification orchestrator"
```

The first cron firing initializes state files (if absent) and runs Wave-1 kickoff. Subsequent firings re-enter the state machine.

**Hard stop:** the human can interrupt anytime by:
- Sending `STOP` to the session (orchestrator writes "INTERRUPTED" to log + TaskStop monitors).
- Calling `CronDelete` on the cron entry.
- Closing PR #29 (orchestrator detects on next wake and writes "PLAN_REVOKED" to log).

No other human input is required from kickoff through `DONE`.

---

## Recovery from interruption / compaction / crash

The orchestrator is resumable because all state is on disk:

1. On any wake-up where the conversation looks empty / compacted, the orchestrator first does: `Read docs/SIMPLIFICATION_STATE.json`. If absent → first-run kickoff. If present → reconciliation.
2. Reconciliation:
   - `gh pr list --search head:refactor/` to learn live PR states.
   - `git worktree list` to find existing worktrees.
   - Compare to state file. If state file is stale (PR merged but file says `pr_open`), update state file and re-evaluate.
3. If a WS is stuck in `implementing` or `reviewing` with no in-flight background agents (notification queue empty), re-dispatch the appropriate agent.
4. Continue from the next eligible action.

The run log is the audit trail — every state transition is a one-line append. After-the-fact debugging never requires "what was the orchestrator thinking" — just `cat docs/SIMPLIFICATION_RUN_LOG.md`.
