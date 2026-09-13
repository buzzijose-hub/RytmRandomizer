"""Tests must not write to git-tracked files.

A test that mutates a tracked file is a landmine: it passes locally, leaves
the working tree dirty, and breaks whatever test runs after it — with the
failure surfacing somewhere unrelated to the cause.

**This is not hypothetical.** PR #240 added
``tests/test_refresh_al16_evidence_manifest.py::
test_is_idempotent_when_digests_are_already_current``, which invoked a
provenance-refresh script against the *real* committed
``output/al16/AL02_LOCK_RYTM_manifest.json``. Running it rewrote tracked
evidence and broke ``tests/test_al16_rytm_export.py`` for every test ordered
after it. Every mechanical gate stayed green; it was found by running the
suite twice and noticing the tree had changed.

What this gate does
-------------------
Two complementary checks:

1. A **static scan** for the shape that causes it — a test module that
   references a repo-relative path to a tracked artifact directory and also
   calls a write API. Cheap, runs in the normal architecture job, and points
   at the specific line.
2. A **dynamic check** (``--runslow``-style, opt-in via
   ``RYTM_TEST_MUTATION_CHECK=1``) that snapshots ``git status`` for tracked
   files, runs the suite, and compares. Authoritative but expensive, so it
   is meant for CI and for local use when hunting a suspected polluter.

Writing a test that needs to exercise a real artifact
-----------------------------------------------------
Copy it into ``tmp_path`` and point the code under test at the copy —
``monkeypatch.setattr(module, "_MANIFEST_PATH", copy)`` is the pattern the
AL16 test now uses. Never let a test's success depend on, or result in,
mutating a file git tracks.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Final

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
TESTS_ROOT: Final[Path] = PROJECT_ROOT / "tests"

#: Committed-artifact directories a test might be tempted to rewrite
#: (``output/``, ``specs/``, ``docs/``). Fixture directories are deliberately
#: excluded: regenerating goldens is a script-driven act
#: (``RYTM_REPORT_GOLDEN_CAPTURE=1``), not something a test does.
#:
#: A write API applied directly to an expression naming a tracked artifact
#: directory -- e.g. ``(PROJECT_ROOT / "output" / "x.json").write_text(...)``
#: or ``open("output/x.json", "w")``. Matching the *write target* rather than
#: mere co-occurrence keeps the gate quiet: a module that only names an
#: artifact path (to assert a hash, or resolve a doc link) does not trip it.
_ARTIFACT_SEGMENT: Final[str] = r"[\"'](?:output|specs|docs)[/\"']"
_WRITE_TO_ARTIFACT_RE: Final[re.Pattern[str]] = re.compile(
    rf"""
    (?:
        # (... "output" ...).write_text(  /  .write_bytes(  /  .unlink(
        \([^()]*{_ARTIFACT_SEGMENT}[^()]*\)\s*\.\s*(?:write_text|write_bytes|unlink|rename|replace)\s*\(
      | # open("output/...", "w")
        \bopen\s*\(\s*[^)]*{_ARTIFACT_SEGMENT}[^)]*[\"'][wa]
      | # a bare "output/..." string handed to a write helper
        \.(?:write_text|write_bytes)\s*\(\s*[^)]*{_ARTIFACT_SEGMENT}
    )
    """,
    re.VERBOSE,
)

_ENV_FLAG: Final[str] = "RYTM_TEST_MUTATION_CHECK"


def _test_modules() -> list[Path]:
    return [
        path for path in sorted(TESTS_ROOT.rglob("test_*.py")) if "__pycache__" not in path.parts
    ]


def _strip_comments_and_docstrings(source: str) -> str:
    without = re.sub(r'"""(?:.|\n)*?"""', '""', source)
    without = re.sub(r"'''(?:.|\n)*?'''", "''", without)
    return re.sub(r"(?m)#.*$", "", without)


def test_no_test_module_writes_to_a_tracked_artifact_directory() -> None:
    """No test module applies a write API to a committed-artifact path.

    Matches the *write target*, not mere co-occurrence: a module that only
    names an artifact path — to assert a committed hash, or to resolve a
    documentation link — does not trip. An earlier co-occurrence version of
    this check flagged three such modules, and a gate that cries wolf gets
    ignored, which is worse than no gate.
    """

    offenders: dict[str, list[int]] = {}
    for path in _test_modules():
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        scrubbed = _strip_comments_and_docstrings(path.read_text(encoding="utf-8"))
        lines = [
            index
            for index, line in enumerate(scrubbed.splitlines(), start=1)
            if _WRITE_TO_ARTIFACT_RE.search(line) and "tmp_path" not in line
        ]
        if lines:
            offenders[rel] = lines

    assert not offenders, (
        "Test module names a committed-artifact path and also calls a write "
        "API. A test must never mutate a git-tracked file -- copy the "
        "artifact into ``tmp_path`` and point the code under test at the "
        "copy (see this module's docstring for the worked example).\n\n"
        "  Suspect sites:\n"
        + "\n".join(
            f"    {module}: line(s) {', '.join(str(n) for n in lines)}"
            for module, lines in sorted(offenders.items())
        )
    )


@pytest.mark.skipif(
    os.environ.get(_ENV_FLAG) != "1",
    reason=f"expensive whole-suite check; set {_ENV_FLAG}=1 to run",
)
def test_running_the_suite_leaves_tracked_files_unchanged() -> None:
    """Authoritative check: the suite does not dirty any tracked file.

    Opt-in because it runs the whole suite in a subprocess. The static scan
    above is the cheap always-on approximation.
    """

    def tracked_dirty() -> set[str]:
        result = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=no", "-z"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            check=True,
        )
        entries = [e for e in result.stdout.decode("utf-8").split("\0") if e]
        # Compared as a before/after delta, so any pre-existing dirt (the
        # repo's known line-ending churn, or the developer's own edits) is
        # present in both snapshots and cancels out.
        return {entry[3:] for entry in entries}

    before = tracked_dirty()
    subprocess.run(
        ["python", "-m", "pytest", "-q", "-x", "--no-header"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        check=False,
    )
    after = tracked_dirty()

    newly_dirty = sorted(after - before)
    assert not newly_dirty, (
        "Running the test suite modified git-tracked files. Some test is "
        "writing to a committed artifact instead of a tmp_path copy:\n    "
        + "\n    ".join(newly_dirty)
    )
