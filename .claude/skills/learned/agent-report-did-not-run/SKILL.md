---
name: agent-report-did-not-run
description: A parallel agent's suite that errors at collection because a sibling agent's module is absent reports as green to the orchestrator. Parse the runner's own summary — never the agent's prose — and treat "did not run" as a third outcome distinct from pass and fail.
user-invocable: false
origin: auto-extracted-2026-09-08
---

# "Green" and "ran" are different facts

**Extracted:** 2026-09-08
**Context:** The auto-update program (11 parallel worktree agents). The single
largest defect — 17 of 21 merge failures — was caught by a test the agent had
**already written correctly** and which **never executed**.

## Problem

Agent A2 owned `scripts/prepare_release.py`, which imports `release_lib` from
agent A1's scope. In A2's isolated worktree, `release_lib.py` did not exist.
A2 wrote an honest guard:

```python
pytest.fail("scripts/release_lib.py is missing", pytrace=False)
```

Run in A2's worktree:

```
ERROR tests/test_prepare_release.py - Failed: scripts/release_lib.py is missi...
18 errors in 0.53s
```

**Zero tests ran.** A2's prose report said "80 tests pass, 100% branch coverage"
— true, but measured against a throwaway stand-in it deleted before handoff.
The orchestrator recorded the agent as green.

Copy A2's **untouched** suite into a tree containing A1's real `release_lib.py`:

```
15 failed, 65 passed in 0.58s
```

Headed by `test_apply_bump_release_versions[1.34.0-minor-1.35.0]` — the exact
bug (`prerelease` is `()` not `None`, so every bump returned the current
version) that caused most of the merge failures. **No new test was needed.
The correct test existed and had never run.**

## Why the usual signals miss it

- The agent's summary is prose, and it was not lying — it described a real run
  against a stand-in.
- Coverage was 100% — of the code that ran, against a stub.
- `pytest` does exit non-zero here, but an orchestrator reading a
  `tail -1` of piped output sees `18 errors in 0.53s` and an exit code from
  `tail`, not from pytest. **Pipelines launder exit codes.**

## Pattern

Treat **DID NOT RUN** as a third outcome, and decide it mechanically:

```bash
pytest -q 2>&1 | python scripts/check_agent_report.py --runner pytest
# exit 0 = ran and passed | 1 = ran and failed | 2 = DID NOT RUN
```

`scripts/check_agent_report.py` parses the runner's own summary (pytest, cargo,
vitest) and rejects: collection errors, `no tests collected`, zero-collected,
and zero-passed-zero-failed.

Reject an agent's completion on exit 2. An agent that cannot be green in
isolation must say so as its **headline**, not a footnote — that is information
the orchestrator acts on, not a blemish on the agent.

## Related failure shapes in the same run

- **Fail-open cross-track guards.** A Rust corpus test wrapped its whole body
  in `if let Ok(entries) = std::fs::read_dir(&invalid_dir)`. The directory
  belonged to another agent and was absent, so the body — including its
  `assert!(checked > 0)` — never executed. `cargo test` was green. Assert the
  fixture exists **outside** the conditional.
- **Coverage against a stub.** A script hit 100% branch coverage while
  crashing on every real invocation, because its tests stubbed the collaborator
  it loads.

## Cross-references

- `.claude/rules/parallel-agent-composition.md` §1, §2, §5 — the binding rule.
- `scripts/check_agent_report.py` + `tests/test_check_agent_report.py`.
- `.claude/skills/learned/parallel-agent-bundle/SKILL.md` — dispatch side.
- `agent-memory/feedback_verify_composition_not_agents.md`.
