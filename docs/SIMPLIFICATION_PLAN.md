# RytmRandomizer — Simplification Plan (Maximum-Parallel Execution)

**Status:** Proposed · 2026-05-18
**Base:** `modularize-v1.34` @ `3e2a3d5`
**Scope:** Moderate refactor — add abstractions PR #21 needs + finish in-flight type-tightening prior PRs flagged.
**Mode:** Cooperative with PR #21. Codex rebases onto these abstractions; PR #21 shrinks from ~30k LOC to ~5–8k.
**Execution model:** Each workstream is an **isolated git worktree** with a dedicated agent crew. Independent workstreams run **simultaneously** in background tasks. A top-level orchestrator (Claude) coordinates merges.

---

## Why this exists

Two things came together:

1. **The cleanup batch (PRs #22–#28) exposed real bloat** the audits couldn't touch without changing semantics: ~3,600 LOC of dead code already removed, the V1.34 monolith retired, but the package still has duck-typed boundaries (`Sender = Any`, mixins that read "off `self` but do not declare them"), a 1,374-LOC behavior-pad-lane registry, and an 8-arm `if/elif` tail on `shell.dispatch` that the PR-#15 refactor explicitly punted on.

2. **PR #21 sprawled into ~33 new top-level files** because four abstractions don't exist: no `Device` Protocol, no `SnapshotDecoder[T]`/`MutationPlanner[T]` base, no CLI command registry, no `PassiveReportFormatter`.

**Cooperative goal:** land the abstractions on base; codex rebases PR #21 against them.

**Non-goal:** changing V1.34 byte-level behavior. The 11 parity-API symbols (`docs/ARCHITECTURE.md` §8) are untouchable; engine→wire byte sequence stays identical; JSON fixtures in `tests/fixtures/v134_parity/` must continue to match.

---

## What's already DRY (don't touch)

- **Domain data** is single-source in `rytm_randomizer/data/`. Top-level `profiles.py`/`scenes.py`/`constants.py` derive from it. Nothing to do.
- **Pad-engine helpers** consolidated in `engines/_runtime.py` (PR H1). Still mixin-shaped (see WS-S2) but the duplication is gone.
- **Shell dispatch** for 84 of 92 arms is already a table (`shell._DISPATCH`, PR #15/H2). Eight special-shaped arms remain inline; closing that gap is WS-S3.

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
```

Wall-clock target: **~3–4 days** (vs ~2 weeks sequential), driven by Wave-1 parallelism.

---

## Agent crew per workstream

Every workstream uses the same crew shape — the only difference is which plugin agents Claude (orchestrator) dispatches in parallel for that workstream's worktree:

| Phase | Agent | Plugin | What it does |
|---|---|---|---|
| 0. Worktree setup | (orchestrator) | — | `git worktree add` an isolated branch off `modularize-v1.34`. |
| 1. Plan | `planner` | `everything-claude-code` | Reads the WS spec from this doc, produces a step-by-step plan with file list and acceptance criteria. |
| 2. Test-first | `tdd-guide` | `everything-claude-code` | Writes the failing tests for the new Protocol/registry/formatter from the plan. RED. |
| 3. Implement | (orchestrator) | — | Writes the minimum code to turn the new tests GREEN while keeping the 505 V1.34 parity fixtures green. |
| 4. Type/style check | `python-reviewer` | `everything-claude-code` | Confirms PEP 8, type annotations, Pythonic idioms, immutability where appropriate. |
| 5. Code review | `code-reviewer` | `everything-claude-code` | Catches CRITICAL/HIGH issues. |
| 6. Security review | `security-reviewer` | `everything-claude-code` | Required only for WS-S1/S5/S7 (boundary/IO/registry changes). |
| 7. Build/CI guard | `build-error-resolver` | `everything-claude-code` | Stands by; engaged only if CI fails. |
| 8. Doc update | `doc-updater` | `everything-claude-code` | Updates `docs/STATUS.md` "Recent Cleanup" entry + `docs/ARCHITECTURE.md` if the WS touches a documented boundary. |

Phases 1, 2, 4, 5, 6 run in parallel where their inputs are independent. The orchestrator stitches the outputs.

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

## Orchestrator runbook (executable summary)

### Setup phase
```
# Create 4 worktrees in parallel (Wave 1 streams)
git worktree add RytmRandomizer-worktrees/ws-s1-midi-sender-protocol     -b refactor/midi-sender-protocol      modularize-v1.34
git worktree add RytmRandomizer-worktrees/ws-s2-pad-runtime-protocol     -b refactor/pad-runtime-protocol      modularize-v1.34
git worktree add RytmRandomizer-worktrees/ws-s3-shell-dispatch-close     -b refactor/shell-dispatch-close      modularize-v1.34
git worktree add RytmRandomizer-worktrees/ws-s4-passive-report-formatter -b refactor/passive-report-formatter  modularize-v1.34
```

### Wave 1 (one message, four parallel agents per phase)

**Phase 1 — Plan (single message, 4 background agents):**
```
Agent(planner, "WS-S1 plan", worktree=ws-s1, in background)
Agent(architect, "WS-S2 plan", worktree=ws-s2, in background)
Agent(architect, "WS-S3 plan", worktree=ws-s3, in background)
Agent(planner, "WS-S4 plan", worktree=ws-s4, in background)
```

**Phase 2 — TDD (single message, 4 background agents):**
```
Agent(tdd-guide, "WS-S1 tests", worktree=ws-s1, in background)
Agent(tdd-guide, "WS-S2 tests", worktree=ws-s2, in background)
Agent(tdd-guide, "WS-S3 tests", worktree=ws-s3, in background)
Agent(tdd-guide, "WS-S4 tests", worktree=ws-s4, in background)
```

**Phase 3 — Implement (orchestrator writes code in each worktree):**
Do the four implementations in alternating Edit calls across worktrees; PowerShell verifies parity fixtures pass in each one.

**Phase 4 — Review (single message, multi-agent fanout per worktree):**
For each WS, dispatch `code-reviewer` + `python-reviewer` in parallel. Add `security-reviewer` for WS-S1 (boundary change).

**Phase 5 — Docs + PR open:**
`doc-updater` per worktree, then `gh pr create` for each. PR auto-merges via the same monitor pattern as the last batch.

### Wave 2 (after Wave 1 fully merged)

Same shape, 2 worktrees:
```
git worktree add ... -b refactor/device-protocol-registry  main
git worktree add ... -b refactor/snapshot-envelope         main
```

`architect` agent is **mandatory and blocking** for both (Protocol surfaces are load-bearing). After architect approval, parallel TDD + implement + review.

### Wave 3 (after Wave 2)

One worktree, full crew. Lands the diff-killer for codex.

### Hand-off to codex

After all 7 PRs merge, **the orchestrator opens an issue against PR #21** with the rebase instructions, the new module list, and the migration mapping. Example issue body:

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

## Verification at each wave

- **Wave 1 merge:** clean venv → `pip install -e ".[dev]"` → `pytest` 2,000+ tests green (incl. all 505 V1.34 parity fixtures) → `pyright --strict` clean on the new Protocol surfaces → CI matrix green on all 3 OSs.
- **Wave 2 merge:** `AnalogRytmDevice.to_mock_messages(plan)` byte-identical to current direct engine path (new golden test); `snapshot/envelope.py` helpers byte-identical to originals.
- **Wave 3 merge:** PR #24's 55 CLI golden tests pass unchanged; new command can be added by dropping a file in `cli/commands/` with zero `cli.py` change (demonstration test).
- **After hand-off:** codex's rebased PR #21 is **<10k LOC**.

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
