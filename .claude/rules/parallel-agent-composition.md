# Parallel-agent composition — mandatory rule

**Authority:** This file + `tests/architecture/test_workflow_script_invocations_resolve.py` + `tests/architecture/test_cross_language_event_seams_agree.py` (mechanical enforcement) + the 2026-09-07 auto-update post-mortem.
**Scope:** Any run that dispatches two or more agents whose outputs must compose — parallel worktree bundles, cascade workstreams, multi-track feature programs.
**Companion to:** [`maximize-parallelization.md`](maximize-parallelization.md) (dispatch work in parallel) and [`autonomous-agent-execution.md`](autonomous-agent-execution.md) (don't pause between steps). Those two say *go wide, go fast*. This one says *and here is what you must verify before you believe it worked*.

## Why this rule exists

The auto-update program ran 11 agents in parallel worktrees. Every agent
produced genuinely good work: 100% branch coverage per track, a
compile-time-enforced consent guarantee in Rust, Gate 17 clean repo-wide,
159/159 cargo tests, 854/854 vitest. The merged tree had **21 failures and
seven blockers**, and every single blocker sat in a producer/consumer pair
that no individual agent could see.

The post-mortem's finding matters more than the blocker list:

> The 11-way split was close to right. It was **verified as if it were 11
> separate programs.**

The decomposition was not the problem — the reuse contracts held (agents
imported rather than forked; Gate 17 came back clean; one doc-comment
conflict across eleven agents). What was missing was cheaper than a
re-decomposition, and this rule is it.

## The rule

### 1. A green report that did not run is a RED report

The single most expensive defect of that run (17 of 21 merge failures) was
caught by a test the agent had **already written correctly** — and which
never executed. In its own worktree the suite errored at collection because
the collaborator's file was absent; the agent honestly reported the guard;
the orchestration recorded "green".

Dropping the real collaborator beside that untouched suite produced
**15 failures in 0.58 seconds**.

So: **parse the runner's own summary, never the agent's prose.** Reject an
agent's completion when its suite reports any of:

- a collection error, or `no tests collected`
- a non-zero skip count on a cross-track test
- zero collected items for a file the agent claims to have covered
- a coverage figure measured against a stub of another agent's module

An agent that *cannot* be green in isolation must say so as its headline,
not in a footnote — and that is information the orchestrator acts on, not a
blemish on the agent.

### 2. Cross-track tests must fail closed

The Rust corpus test in that run was written correctly and was dead code:

```rust
if let Ok(entries) = std::fs::read_dir(&invalid_dir) {   // dir absent in this worktree
    ...
    assert!(checked > 0);                                 // never reached
}
```

`cargo test` was green. Any guard over another agent's artifact must assert
the artifact **exists** outside the conditional, and assert the checked count
is non-zero. The repo's own precedent is
`tests/architecture/test_live_gui_protocol_is_generated.py`'s
`assert GENERATOR_PATH.is_file()`.

Corollary: **land shared fixture corpora on the kickoff base before T0**, so
every worktree branches from a tree that already contains them. A corpus that
only exists in its author's worktree is a corpus nobody else tests against.

### 3. One integration checkpoint at first cross-agent import

Not a cadence — **one** halt, placed where the first consumer's import of a
producer becomes real. Merge to a composed tree and run only mechanical
checks (no new tests to author):

1. Execute every `python scripts/*.py <subcommand>` string appearing in any
   workflow YAML, and require the documented **effect** — a written file, a
   non-zero exit on bad input — not merely exit 0.
2. Invoke every script defining `__main__` once against its canonical fixture.
3. Feed each producer's sample output to its consumer's real validator.

In the post-mortem this single checkpoint would have caught four of the seven
blockers, hours earlier, while the owning agent still had context. It costs
one serialisation point in an N-way run. That is the whole price.

### 4. Every cross-language seam gets a drift guard, and the contract names a CALL FORM

A contract that fixes a **noun** (a payload shape, an event name, a file path)
leaves the **verb** free. The worst blocker of the run had both sides agreeing
on the string `"rytm-update-state"` and disagreeing on the mechanism: the
shell emitted over Tauri IPC, the webview subscribed with the DOM's
`addEventListener`, `@tauri-apps/api` was not even a dependency, and the
feature was totally inert while both suites stayed green.

So a cross-boundary contract row must specify the **function the consumer
calls**, not only the data that crosses — `subscribeUpdateState(cb)`, not
"an event named X carrying shape Y".

This repo already knew this. `tests/architecture/test_frontend_matches_handshake_contract.py`
pins the two-argument `new WebSocket(url, subprotocol)` **call form**, written
after PR #113 shipped the one-argument shape. The auto-update plan added
**zero** such guards for its nine interface contracts — a Gate 17 violation by
the plan itself, reusing none of the eight existing `desktop/web` drift guards.

Prefer, in order: (a) **generate** one side from the other with a `--check`
gate (`scripts/generate_live_gui_protocol_ts.py`); (b) a drift guard asserting
the call form; (c) prose. Only (a) and (b) fail CI.

### 5. Consumer tests exercise the real collaborator at the checkpoint

Forbidden as a stand-in for another agent's artifact: monkeypatching the
loader, a `tmp_path` stub of the collaborator file, and `window.dispatchEvent`
substituting for `window.emit`. One run hit **100% branch coverage on a script
that crashed on every real invocation**, because its tests stubbed the module
it loads.

Agents may stub while working in isolation — that is what keeps them
parallel — but each agent owns at least one test that exercises the real
collaborator, and those run at the §3 checkpoint.

### 6. Some defects are spec defects; budget a human read

Two of the seven blockers were **unreachable by any decomposition or test
rule**: the manifest corpus contained host and scheme fixtures and no
path-violation fixture, so a perfect corpus-iterating test passed against both
implementations and still shipped a security gap; and "is an empty manifest
valid?" was simply unanswered in the spec, so two agents answered it
differently and both were defensible.

A shared corpus enforces agreement only on cases someone thought to write
down. Where a spec clause is a **security boundary**, mark it as one and give
it an adversarial `(input, verdict)` table checked in at T0 — and still budget
a human reading the clause against every implementation of it.

## What you MUST NOT do

- **Do not** accept an agent's self-reported "all green" without the runner's
  own summary line.
- **Do not** let a cross-track guard skip silently when its fixture is absent.
- **Do not** write a contract row that names only data. Name the call.
- **Do not** re-decompose to fix a reporting bug. Merging two agents to prevent
  one seam defect costs the largest wall-clock unit in a run to buy what a
  static guard buys for nothing.
- **Do not** measure coverage against a stub of another agent's module and
  report it as Gate 1 evidence.

## Cross-references

- `.claude/rules/maximize-parallelization.md` — dispatch independent work in parallel.
- `.claude/rules/autonomous-agent-execution.md` — run to a hard stop without pausing.
- `.claude/rules/cascade-merge-pattern.md` — bundle the parallel outputs into one PR.
- `scripts/check_agent_report.py` — §1 mechanised (`just agent-report pytest`).
- `scripts/survey_before_writing.py` + `just survey <name>` — Gate 17's survey
  step, as a command. Run it BEFORE writing a module: the orchestrator of this
  very run wrote a fully-tested fork of `check_touched_coverage.py` and found
  the original afterwards. `tests/architecture/test_no_forked_sibling_scripts.py`
  is the backstop that catches it at commit time if the survey is skipped.
- `scripts/check_touched_coverage.py` + `just gate1` — the Gate 1 measurement
  that can actually fail. The hand-rolled `--cov` recipe this rule's sibling
  used to document measured nothing and exited 0: the §5 "coverage against a
  stub" trap in another guise.
- `tests/architecture/test_workflow_script_invocations_resolve.py` — §3 mechanised.
- `tests/architecture/test_cross_language_event_seams_agree.py` — §4 mechanised.
- `tests/architecture/test_frontend_matches_handshake_contract.py` — the call-form precedent.
- `tests/architecture/test_live_gui_protocol_is_generated.py` — the generate-and-`--check` precedent.
