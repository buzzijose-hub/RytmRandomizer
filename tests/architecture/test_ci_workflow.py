"""Enforce structural invariants on the GitHub Actions workflow files.

The CI pipeline has a few non-obvious rules that, if violated, produce
subtle and high-impact breakage: lint passes locally but fails in CI, pip
downloads on every run, branch protection silently lets a new job slip
through. These tests check those rules so the contributor finds out at
commit time, not after they have pushed.

Rules checked here:

1. **Lint-tool versions are pinned in lockstep.** The `lint` job in
   ``.github/workflows/test.yml`` installs explicit ``ruff==``, ``black==``,
   and ``isort==`` versions. Those exact versions must match the
   ``rev:`` lines in ``.pre-commit-config.yaml`` so a contributor's
   ``pre-commit run`` produces the same verdict as CI.

2. **Every ``actions/setup-python`` step caches pip.** Any setup-python
   without ``cache: pip`` and ``cache-dependency-path: pyproject.toml``
   is a CI-minute leak -- pip re-downloads the dep set on every run.

3. **The ``required-checks`` aggregate ``needs:`` every other job.**
   Branch protection requires only the aggregate; a new job that is not
   listed in ``required-checks.needs:`` silently bypasses the gate.

The first run of these tests caught real bugs: lint-tool version drift
between workflow and pre-commit (would only surface as CI failure with
no local repro), and a freshly-added job that the aggregate did not
``needs:`` (a merge would pass even if the new job failed).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS_DIR = PROJECT_ROOT / ".github" / "workflows"
TEST_WORKFLOW = WORKFLOWS_DIR / "test.yml"
PRECOMMIT_CONFIG = PROJECT_ROOT / ".pre-commit-config.yaml"


# Map a pre-commit `repo:` URL to the pip distribution name that the CI
# lint job installs. The mapping is needed because pre-commit hooks
# reference upstream repos by URL but pip installs by package name. When
# adding a new lint hook to the workflow, add the matching upstream-URL
# entry here.
_LINT_REPO_TO_PIP_NAME: dict[str, str] = {
    "https://github.com/psf/black": "black",
    "https://github.com/pycqa/isort": "isort",
    "https://github.com/astral-sh/ruff-pre-commit": "ruff",
}


def _read_workflow_text(path: Path) -> str:
    """Return the workflow file's text with a clear error if missing."""

    if not path.exists():
        pytest.fail(f"Missing workflow file: {path.relative_to(PROJECT_ROOT)}")
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Rule 1: lint-tool version lockstep between CI workflow and pre-commit.
# ---------------------------------------------------------------------------


def _extract_workflow_lint_pins() -> dict[str, str]:
    """Parse the `pip install "ruff==X" "black==Y" "isort==Z"` step.

    Returns ``{"ruff": "0.15.13", "black": "26.3.1", "isort": "8.0.1"}``
    (or whatever versions are currently pinned). The step text is matched
    with a regex rather than YAML-parsed because the version strings live
    inside a shell command string, not as structured workflow fields.
    """

    text = _read_workflow_text(TEST_WORKFLOW)
    # Find the `Install lint tools` step's `run:` line.
    match = re.search(
        r"name:\s*Install lint tools\s*\n\s*run:\s*(.+)\n",
        text,
    )
    if match is None:
        pytest.fail(
            "Could not find the 'Install lint tools' step in "
            ".github/workflows/test.yml. If the step was renamed, update "
            "this test's regex."
        )
    install_line = match.group(1)
    pins = dict(re.findall(r'"?([a-z][a-z0-9-]*)==([0-9][^"\s]+)"?', install_line))
    if not pins:
        pytest.fail(
            f"Could not parse any ==-pinned packages from the install line: " f"{install_line!r}"
        )
    return pins


def _extract_precommit_pins() -> dict[str, str]:
    """Parse `.pre-commit-config.yaml` for `rev:` lines under each repo.

    Returns ``{"ruff": "0.15.13", "black": "26.3.1", "isort": "8.0.1"}``.
    The leading ``v`` prefix on ruff's rev (e.g. ``v0.15.13``) is stripped
    so the comparison is apples-to-apples with the workflow's
    ``ruff==0.15.13`` form.
    """

    text = _read_workflow_text(PRECOMMIT_CONFIG)
    pins: dict[str, str] = {}
    # Walk repo: ... rev: ... blocks. The two lines are not always
    # adjacent, so capture them within a single block by anchoring at
    # `- repo:` and grabbing the next `rev:` before the next `- repo:`.
    block_pattern = re.compile(
        r"-\s*repo:\s*(\S+)\s*\n(?:.*?\n)*?\s*rev:\s*(\S+)",
        re.MULTILINE,
    )
    for repo_url, rev in block_pattern.findall(text):
        pip_name = _LINT_REPO_TO_PIP_NAME.get(repo_url)
        if pip_name is None:
            # Hook for a project we are not asserting on (e.g.
            # pre-commit-hooks). Skip.
            continue
        # Strip a leading "v" from semantic-version-style revs (ruff uses
        # "v0.15.13"; black uses "26.3.1" without v). Both must compare
        # against the workflow's ==X form.
        pins[pip_name] = rev.lstrip("v")
    return pins


def test_lint_tool_versions_match_between_workflow_and_precommit() -> None:
    """The CI lint job and pre-commit must pin identical tool versions.

    When they drift, ``pre-commit run --all-files`` passes locally but
    the CI ``lint`` job fails (or vice versa) -- a frustrating
    no-local-repro bug. Bumping a tool means updating BOTH files.
    """

    workflow = _extract_workflow_lint_pins()
    precommit = _extract_precommit_pins()

    # Both should mention the same set of pinned tools.
    common = set(workflow) & set(precommit)
    assert common, (
        "No common lint tools found between workflow and pre-commit. "
        "Either the workflow's install line was renamed or the "
        "pre-commit config no longer references black/isort/ruff."
    )

    mismatches = []
    for tool in sorted(common):
        if workflow[tool] != precommit[tool]:
            mismatches.append(
                f"  {tool}: workflow pins {workflow[tool]!r}, "
                f"pre-commit pins {precommit[tool]!r}"
            )

    assert not mismatches, (
        "Lint-tool version drift between .github/workflows/test.yml and "
        ".pre-commit-config.yaml. CI and local pre-commit must agree, "
        "otherwise contributors get conflicting verdicts. Sync both files "
        "and re-run.\n" + "\n".join(mismatches)
    )


# ---------------------------------------------------------------------------
# Rule 2: every actions/setup-python step caches pip.
# ---------------------------------------------------------------------------


def _iter_setup_python_blocks(workflow_text: str) -> list[str]:
    """Return each `uses: actions/setup-python@vN` block as one text chunk.

    The block runs from ``- name: ... uses: actions/setup-python@...``
    through the indented ``with:`` mapping that follows. We collect the
    text by line-scanning rather than YAML-parsing so we can preserve the
    exact text for the assertion's error message.
    """

    blocks: list[str] = []
    lines = workflow_text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if "uses: actions/setup-python@" in line:
            # Capture this line plus the indented ``with:`` block (if any)
            # that follows. Stop at the next step (a line that introduces a
            # new ``- name:`` or returns to or above the step indent).
            step_lines = [line]
            step_indent = len(line) - len(line.lstrip())
            j = i + 1
            while j < len(lines):
                nxt = lines[j]
                if not nxt.strip():
                    # blank line ends the step's text in YAML-as-text terms.
                    step_lines.append(nxt)
                    j += 1
                    continue
                nxt_indent = len(nxt) - len(nxt.lstrip())
                if nxt_indent <= step_indent and nxt.lstrip().startswith("- "):
                    break
                step_lines.append(nxt)
                j += 1
            blocks.append("\n".join(step_lines))
            i = j
        else:
            i += 1
    return blocks


def test_every_setup_python_step_uses_pip_caching() -> None:
    """Every ``actions/setup-python@v6`` step must cache pip.

    Without ``cache: 'pip'`` + ``cache-dependency-path: pyproject.toml``
    the job re-downloads the full dependency set on every run --
    typically 30-60 seconds of CI-minute waste per job. A new job
    added without caching is a slow leak; this test makes it loud.
    """

    violations: list[str] = []
    for workflow_path in WORKFLOWS_DIR.glob("*.yml"):
        text = _read_workflow_text(workflow_path)
        rel = workflow_path.relative_to(PROJECT_ROOT)
        for block in _iter_setup_python_blocks(text):
            if "cache:" not in block or "pip" not in block:
                violations.append(f"{rel}: setup-python step is missing `cache: pip`:\n" f"{block}")
                continue
            if "cache-dependency-path" not in block:
                violations.append(
                    f"{rel}: setup-python step caches pip but is missing "
                    f"`cache-dependency-path: pyproject.toml`. Without "
                    f"the path, the cache key is brittle:\n{block}"
                )

    assert not violations, (
        "Every actions/setup-python step must use pip caching keyed off "
        "pyproject.toml. Add the two lines under `with:`:\n"
        '          cache: "pip"\n'
        "          cache-dependency-path: pyproject.toml\n\n"
        "Violations:\n" + "\n\n".join(violations)
    )


# ---------------------------------------------------------------------------
# Rule 3: required-checks aggregate covers every upstream job.
# ---------------------------------------------------------------------------


def _parse_test_workflow_jobs() -> tuple[list[str], list[str]]:
    """Return ``(all_job_names, required_checks_needs)`` from test.yml.

    Both lists are derived from the YAML structure. The aggregate job is
    the one named exactly ``required-checks``; ``needs:`` may be a YAML
    list (`needs: [a, b]`) or a single string (`needs: foo`) -- we
    normalize to a list of strings.
    """

    # We use PyYAML if available so the test does not depend on a custom
    # parser. PyYAML is already a transitive dependency of several tools
    # (pre-commit, briefcase, etc.) so it is installed in CI.
    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError:  # pragma: no cover - install yaml
        pytest.skip("PyYAML not installed; skipping workflow structure check.")

    data = yaml.safe_load(_read_workflow_text(TEST_WORKFLOW))
    jobs = data.get("jobs", {}) or {}
    all_names = sorted(jobs.keys())

    aggregate = jobs.get("required-checks")
    if aggregate is None:
        pytest.fail(
            ".github/workflows/test.yml has no `required-checks` job. "
            "Branch protection requires this aggregate; see "
            "docs/BRANCH_PROTECTION.md."
        )

    raw_needs = aggregate.get("needs")
    if raw_needs is None:
        needs: list[str] = []
    elif isinstance(raw_needs, list):
        needs = [str(n) for n in raw_needs]
    else:
        needs = [str(raw_needs)]

    return all_names, sorted(needs)


def test_required_checks_aggregate_covers_every_upstream_job() -> None:
    """``required-checks.needs:`` must list every other job in test.yml.

    Branch protection (see scripts/apply-branch-protection.sh) requires
    only the ``required-checks`` aggregate. If a new job is added but
    not appended to the aggregate's ``needs:`` list, the job can fail
    and the PR still merges -- a silent gap in the gate. This test
    fails if the two job sets drift apart.
    """

    all_names, needs = _parse_test_workflow_jobs()

    # The aggregate cannot need itself.
    expected_needs = sorted(name for name in all_names if name != "required-checks")
    missing = sorted(set(expected_needs) - set(needs))
    stale = sorted(set(needs) - set(expected_needs))

    error_parts: list[str] = []
    if missing:
        error_parts.append(
            "The following jobs exist but are NOT in required-checks.needs "
            "(branch protection cannot see their failures):\n  - " + "\n  - ".join(missing)
        )
    if stale:
        error_parts.append(
            "The following names are in required-checks.needs but the "
            "corresponding job no longer exists (rename or removal):\n  - " + "\n  - ".join(stale)
        )
    assert not error_parts, (
        "required-checks aggregate is out of sync with the workflow's "
        "job list. Update the `needs:` line in .github/workflows/test.yml "
        "so branch protection sees every gate.\n\n" + "\n\n".join(error_parts)
    )
