"""Cross-language wire-format parity check for the wizard protocol.

PR #102 surfaced a latent bug where the Python sidecar emitted
``analysis_progress`` events as ``{"type", "job"}`` while the TypeScript type +
reducer expected top-level ``{source_id, progress, status}`` — every event was
silently dropped on the client.

This test is a lightweight, AST-free parity guard that reads both source files
as text and asserts the two sides describe the same wire shape. It deliberately
avoids spinning up a TypeScript toolchain — a regex over the interface body is
enough to catch the next drift early, and it keeps the test in the ``fast``
suite (no Node, no compiler, no fixtures).

Concretely:

* The TS ``AnalysisProgressEvent`` interface body must contain a ``job`` field
  typed as ``AnalysisJobDict`` (the Python ``AnalysisJob.to_dict()`` mirror).
* The TS interface body must NOT carry top-level ``source_id`` / ``progress`` /
  ``status`` — those keys live inside the nested job object.
* The Python ``_build_analysis_progress`` helper must build the event as
  ``{"type": EVENT_ANALYSIS_PROGRESS, "job": <...>}``.
* The Python ``AnalysisJobDict`` (TS) field set must match the Python
  ``AnalysisJob.to_dict()`` keys.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from rytm_randomizer.cockpit.wizard.state import AnalysisJob

pytestmark = pytest.mark.fast

REPO_ROOT = Path(__file__).resolve().parents[2]
TS_PROTOCOL = REPO_ROOT / "desktop" / "web" / "src" / "types" / "wizard_protocol.ts"
PY_HANDLERS = REPO_ROOT / "rytm_randomizer" / "cockpit" / "ws" / "wizard_handlers.py"

# Match `export interface AnalysisProgressEvent { ... }` non-greedily up to the
# matching brace. The interface body is single-level (no nested braces today),
# so a flat `[^}]*` is sufficient and avoids pulling a full TS parser.
_TS_ANALYSIS_PROGRESS_RE = re.compile(
    r"export\s+interface\s+AnalysisProgressEvent\s*\{(?P<body>[^}]*)\}",
    re.MULTILINE,
)

_TS_ANALYSIS_JOB_DICT_RE = re.compile(
    r"export\s+interface\s+AnalysisJobDict\s*\{(?P<body>[^}]*)\}",
    re.MULTILINE,
)


def _read_ts_protocol() -> str:
    assert TS_PROTOCOL.is_file(), f"TS protocol file missing: {TS_PROTOCOL}"
    return TS_PROTOCOL.read_text(encoding="utf-8")


def _read_py_handlers() -> str:
    assert PY_HANDLERS.is_file(), f"Python handlers file missing: {PY_HANDLERS}"
    return PY_HANDLERS.read_text(encoding="utf-8")


def _extract_field_names(interface_body: str) -> set[str]:
    """Extract the top-level field names from a TS interface body.

    Strips ``//`` line comments and ``/* ... */`` block comments first so we
    don't accidentally match field names mentioned in JSDoc.
    """

    no_block = re.sub(r"/\*.*?\*/", "", interface_body, flags=re.DOTALL)
    no_line = re.sub(r"//[^\n]*", "", no_block)
    names: set[str] = set()
    for match in re.finditer(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*\??\s*:", no_line, re.MULTILINE):
        names.add(match.group(1))
    return names


def test_ts_analysis_progress_event_is_nested_job_shape() -> None:
    """The TS event MUST carry `job` and MUST NOT carry top-level job fields."""

    source = _read_ts_protocol()
    match = _TS_ANALYSIS_PROGRESS_RE.search(source)
    assert match is not None, (
        "Could not locate `export interface AnalysisProgressEvent { ... }` in "
        f"{TS_PROTOCOL}. Did the interface name or formatting change?"
    )
    body = match.group("body")
    fields = _extract_field_names(body)
    assert "type" in fields, f"AnalysisProgressEvent missing `type` field; got {sorted(fields)}"
    assert "job" in fields, (
        "AnalysisProgressEvent MUST nest the analysis state under a `job` field "
        "to match the Python `_build_analysis_progress` emit shape. "
        f"Got fields: {sorted(fields)}"
    )
    # The pre-fix top-level fields must NOT come back.
    for forbidden in ("source_id", "progress", "status"):
        assert forbidden not in fields, (
            f"AnalysisProgressEvent leaked top-level field `{forbidden}`; this is "
            "the exact wire-shape drift the parity guard exists to catch. Nest "
            "it inside the `job` object instead."
        )
    # The `job` field must reference the dedicated mirror type so downstream
    # readers know the shape without spelunking.
    assert "AnalysisJobDict" in body, (
        "AnalysisProgressEvent.job must be typed as `AnalysisJobDict` so the "
        "Python `AnalysisJob.to_dict()` mirror is grep-able from the type "
        f"definition. Body was: {body!r}"
    )


def test_ts_analysis_job_dict_mirrors_python_to_dict() -> None:
    """The TS `AnalysisJobDict` field set must equal Python `AnalysisJob.to_dict()` keys."""

    source = _read_ts_protocol()
    match = _TS_ANALYSIS_JOB_DICT_RE.search(source)
    assert match is not None, (
        "Could not locate `export interface AnalysisJobDict { ... }` in "
        f"{TS_PROTOCOL}. The TS side needs a dedicated mirror type for the "
        "Python AnalysisJob.to_dict() payload."
    )
    ts_fields = _extract_field_names(match.group("body"))
    sample_job = AnalysisJob(
        source_id="s1",
        status="ok",
        progress=1.0,
        error=None,
        extracted_traits=(),
    )
    py_fields = set(sample_job.to_dict().keys())
    assert ts_fields == py_fields, (
        "Wire-format drift: TS `AnalysisJobDict` and Python `AnalysisJob.to_dict()` "
        f"disagree. TS={sorted(ts_fields)}, Python={sorted(py_fields)}."
    )


def test_python_emit_site_uses_nested_job_payload() -> None:
    """`_build_analysis_progress` must emit `{"type": ..., "job": ...}`."""

    source = _read_py_handlers()
    assert "EVENT_ANALYSIS_PROGRESS" in source, (
        "Could not find EVENT_ANALYSIS_PROGRESS usage in wizard_handlers.py — "
        "did the emit site move? Update this parity test to point at the new "
        "location."
    )
    # The exact builder body we lock in: `{"type": EVENT_ANALYSIS_PROGRESS, "job": <...>}`.
    builder_re = re.compile(
        r"\{\s*['\"]type['\"]\s*:\s*EVENT_ANALYSIS_PROGRESS\s*,\s*" r"['\"]job['\"]\s*:\s*[^}]+\}",
        re.DOTALL,
    )
    assert builder_re.search(source) is not None, (
        "Python `_build_analysis_progress` must emit "
        '`{"type": EVENT_ANALYSIS_PROGRESS, "job": <job.to_dict()>}`. '
        "Either the emit shape changed (update the TS side to match) or the "
        "regex needs widening."
    )
    # Negative guard: the pre-fix top-level keys must not show up next to
    # EVENT_ANALYSIS_PROGRESS, which would mean both shapes are live at once.
    flat_re = re.compile(
        r"\{\s*['\"]type['\"]\s*:\s*EVENT_ANALYSIS_PROGRESS\s*,\s*"
        r"['\"](?:source_id|progress|status)['\"]",
    )
    assert flat_re.search(source) is None, (
        "Python emit site is mixing the nested-job shape with the legacy "
        "top-level shape. Pick one — the TS side is locked on nested job."
    )
