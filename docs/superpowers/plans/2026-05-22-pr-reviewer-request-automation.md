# PR Reviewer Request Automation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the repository PR workflow request and re-request `edward-rosado` automatically so agents and humans do not have to click GitHub's reviewer request button by hand.

**Architecture:** Add a small script-level helper that wraps `gh pr create` and `gh pr edit --add-reviewer` with the repo's default reviewer. Keep it outside package runtime code so passive CLI and hardware/MIDI behavior remain untouched.

**Tech Stack:** Python 3.11+, GitHub CLI, pytest fast tests, existing Justfile/docs workflow.

---

## File Structure

- Create `scripts/create_pr.py`: pure command builders plus CLI entry points for `gh pr create` and existing-PR `gh pr edit --add-reviewer`.
- Create `tests/test_create_pr_script.py`: fast tests that lock the default reviewer, optional reviewer dedupe, dry-run output, runner delegation, and existing-PR review re-request command.
- Modify `Justfile`: steer `just pr` users to the helper, show the raw fallback with the reviewer flag, and show the existing-PR review re-request command.
- Modify `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `docs/AGENT_TASK_RECIPES.md`, `docs/CODEX_CONTRIBUTING.md`, `docs/AUTONOMOUS_RUN_PLAYBOOK.md`, `docs/PLAN_REQUIREMENTS.md`, `docs/SIMPLIFICATION_PLAN.md`, `docs/SIMPLIFICATION_STATE.schema.json`, `.claude/rules/pr-body-conformance-checklist.md`, `.claude/rules/skill-routing.md`, and `.claude/skills/learned/cascade-merge-pattern/SKILL.md`: keep agent/human PR creation instructions aligned.
- Modify `.github/CODEOWNERS`: clarify that CODEOWNERS handles owner review while the helper requests Eddie.
- Modify `docs/STATUS.md`: hand-authored status entry for the workflow fix.

## Task 1: Lock The PR Command Contract

**Files:**
- Create: `tests/test_create_pr_script.py`
- Create later: `scripts/create_pr.py`

- [ ] **Step 1: Write the failing test**

```python
def test_default_create_command_requests_eddie(tmp_path):
    create_pr = _load_create_pr()
    body = tmp_path / "body.md"
    options = create_pr.PullRequestOptions(title="chore: demo", body_file=body)

    command = create_pr.build_create_command(options)

    assert command[:4] == ["gh", "pr", "create", "--base"]
    assert ["--reviewer", "edward-rosado"] == command[4:6]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_create_pr_script.py -n 0`
Expected: FAIL because `scripts/create_pr.py` does not exist yet.

- [ ] **Step 3: Write minimal implementation**

Add `PullRequestOptions`, `normalize_reviewers`, `build_create_command`, and `main`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_create_pr_script.py -n 0`
Expected: PASS.

## Task 2: Wire The Human And Agent PR Paths

**Files:**
- Modify: `Justfile`
- Modify: `AGENTS.md`
- Modify: `CLAUDE.md`
- Modify: `CONTRIBUTING.md`
- Modify: `docs/AGENT_TASK_RECIPES.md`
- Modify: `docs/CODEX_CONTRIBUTING.md`
- Modify: `docs/AUTONOMOUS_RUN_PLAYBOOK.md`
- Modify: `docs/PLAN_REQUIREMENTS.md`
- Modify: `docs/SIMPLIFICATION_PLAN.md`
- Modify: `docs/SIMPLIFICATION_STATE.schema.json`
- Modify: `.claude/rules/pr-body-conformance-checklist.md`
- Modify: `.claude/rules/skill-routing.md`
- Modify: `.claude/skills/learned/cascade-merge-pattern/SKILL.md`
- Modify: `.github/CODEOWNERS`
- Modify: `docs/STATUS.md`

- [ ] **Step 1: Update docs and helper text**

Replace raw `gh pr create --base modularize-v1.34 ...` guidance with the helper:

```bash
python scripts/create_pr.py --title "<title>" --body-file path/to/body.md
```

Keep a raw fallback that includes:

```bash
--reviewer edward-rosado
```

- [ ] **Step 2: Verify docs mention the reviewer path**

Run: `rg -n "gh pr create|scripts/create_pr.py|edward-rosado" Justfile AGENTS.md CONTRIBUTING.md docs .github scripts tests`
Expected: live PR-create guidance uses `scripts/create_pr.py` or the raw fallback includes `--reviewer edward-rosado`.

## Task 2A: Re-request Review On Existing PR Updates

**Files:**
- Modify: `scripts/create_pr.py`
- Modify: `tests/test_create_pr_script.py`
- Modify: `Justfile`
- Modify: `AGENTS.md`
- Modify: `CONTRIBUTING.md`
- Modify: `docs/AGENT_TASK_RECIPES.md`
- Modify: `docs/STATUS.md`

- [ ] **Step 1: Write the failing test**

```python
def test_review_request_command_readds_eddie_to_existing_pr():
    create_pr = _load_create_pr()
    options = create_pr.ReviewRequestOptions(
        pull_request="92",
        reviewers=("buzzijose-hub",),
    )

    command = create_pr.build_review_request_command(options)

    assert command == [
        "gh",
        "pr",
        "edit",
        "92",
        "--add-reviewer",
        "edward-rosado",
        "--add-reviewer",
        "buzzijose-hub",
    ]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_create_pr_script.py -n 0 -vv`
Expected: FAIL because `ReviewRequestOptions` and `build_review_request_command` do not exist yet.

- [ ] **Step 3: Write minimal implementation**

Add `ReviewRequestOptions`, `build_review_request_command`, and `--request-review-for <PR#>` handling that prints or runs `gh pr edit <PR#> --add-reviewer edward-rosado`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_create_pr_script.py -n 0 -vv`
Expected: PASS.

## Task 3: Verify, Commit, Push, And Open PR

**Files:**
- All changed files above.

- [ ] **Step 1: Focused verification**

Run:

```bash
python -m pytest tests/test_create_pr_script.py -n 0
python -m pytest tests/architecture/ -q
python -m pytest -m fast
```

- [ ] **Step 2: Full/review gates**

Run:

```bash
python -m pytest
python -m pytest --cov=rytm_randomizer --cov-branch --cov-report=term-missing
python scripts/code_review_gate.py --mode cli
```

- [ ] **Step 3: Exact-path stage only intended files**

Run:

```bash
git add scripts/create_pr.py tests/test_create_pr_script.py Justfile AGENTS.md CLAUDE.md CONTRIBUTING.md docs/AGENT_TASK_RECIPES.md docs/CODEX_CONTRIBUTING.md docs/AUTONOMOUS_RUN_PLAYBOOK.md docs/PLAN_REQUIREMENTS.md docs/SIMPLIFICATION_PLAN.md docs/SIMPLIFICATION_STATE.schema.json .claude/rules/pr-body-conformance-checklist.md .claude/rules/skill-routing.md .claude/skills/learned/cascade-merge-pattern/SKILL.md .github/CODEOWNERS docs/STATUS.md docs/superpowers/plans/2026-05-22-pr-reviewer-request-automation.md
git commit -m "chore: automate PR reviewer requests"
```

- [ ] **Step 4: Push and open PR using the helper**

Run:

```bash
git push -u origin codex/pr-reviewer-request-automation-pr30
python scripts/create_pr.py --title "chore: automate PR reviewer requests" --body-file docs/superpowers/plans/2026-05-22-pr-reviewer-request-automation-pr-body.md
```

Expected: GitHub PR review requests include `edward-rosado` immediately after creation.
