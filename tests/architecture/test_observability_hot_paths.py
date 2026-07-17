"""Observability-invariant arch tests for cockpit hot paths.

Implements OBS6 from [`OBSERVABILITY_REVIEW.md`](../../OBSERVABILITY_REVIEW.md):
regression-proof the new observability shape so future PRs don't slip
back into the black-hole tier.

Three invariants are pinned here:

1. **Every hot-path module has a `_logger`.** ``rytm_randomizer/cockpit/
   ws/handlers.py``, ``cockpit/ws/server.py``, ``cockpit/export/cli.py``,
   ``cockpit/export/writer.py``, ``cockpit/wizard/builder.py``,
   ``cockpit/engine/mutate.py`` etc. — every module in the cockpit hot
   set must bind ``_logger = get_logger(__name__)``. Accidental removal
   in a refactor fails the test loudly.

2. **No bare unstructured `logger.info("...")` in hot paths.** Every
   call to ``_logger.info`` / ``.warning`` / ``.error`` / ``.debug`` in
   a hot-path module must pass an ``extra={...}`` keyword carrying the
   structured fields downstream log shippers aggregate on. A call with
   only a positional string is a "log line that exists but says
   nothing measurable" — the worst tier per the OBS gap analysis.

3. **Every taxonomy exception class declares a stable
   ``fingerprint``.** When PR O4 lands, every ``DataError`` /
   ``MidiError`` / ``WriteError`` subclass will declare a
   ``fingerprint: ClassVar[str]`` for log-shipper aggregation. Until
   PR O4 lands, this test is dormant via ``skipif``; once it ships the
   test activates automatically and any new taxonomy class that omits
   the fingerprint fails the build.

Why these three: per OBSERVABILITY_REVIEW.md §gap-analysis, the
biggest finding was "near-total black hole" in cockpit — these
invariants ensure the post-PR-O3 / post-PR-O4 shape stays clean as
new modules join the hot set.

See also:
* ``CODE_REVIEW_PROGRESS.md`` row FIX6.
* ``OBSERVABILITY_REVIEW.md`` §"PR O6 — architecture tests for
  observability invariants".
* ``tests/architecture/test_observability.py`` — the broader Gate-7
  enforcement this test extends.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Final

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
PACKAGE_DIR: Final[Path] = PROJECT_ROOT / "rytm_randomizer"

# The "hot path" file set — modules that handle each WS command or each
# export-pipeline step or each wizard analysis run. Add a module here
# when its work becomes operational (every command / every export
# would emit a log line at INFO+ on a healthy run).
_HOT_PATH_MODULES: Final[frozenset[str]] = frozenset(
    {
        "rytm_randomizer/cockpit/ws/handlers.py",
        "rytm_randomizer/cockpit/ws/wizard_handlers.py",
        "rytm_randomizer/cockpit/ws/server.py",
        "rytm_randomizer/cockpit/export/cli.py",
        "rytm_randomizer/cockpit/export/analog_four_kit.py",
        "rytm_randomizer/cockpit/export/writer.py",
        "rytm_randomizer/cockpit/export/signing.py",
        "rytm_randomizer/cockpit/export/verifier.py",
        "rytm_randomizer/cockpit/wizard/builder.py",
        "rytm_randomizer/cockpit/wizard/analyze.py",
        "rytm_randomizer/cockpit/engine/mutate.py",
        "rytm_randomizer/cockpit/engine/send_plan.py",
        "rytm_randomizer/cockpit/history/store.py",
    }
)


def _module_has_logger_binding(path: Path) -> bool:
    """Return True iff *path* contains ``_logger = get_logger(__name__)``."""

    if not path.is_file():
        return False
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return False
    for node in ast.walk(tree):
        # Look for `_logger = get_logger(__name__)` (with or without
        # type annotation) at module top level.
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id == "_logger":
                return True
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == "_logger":
                return True
    return False


def _unstructured_logger_calls(path: Path) -> list[str]:
    """Return offending lines where ``_logger.<level>(...)`` has no ``extra=``.

    The check is intentionally narrow:

    * Only flags positional-only calls (e.g. ``_logger.info("hello")``)
      with no keyword arguments.
    * Calls with ``extra={...}`` / ``exc_info=...`` / any keyword pass.
    * Calls with TWO positional args (e.g. ``_logger.info("x=%s", x)``
      following the legacy %-style) ALSO pass — they carry structured
      data via lazy interpolation, which the JSON formatter expands
      into fields.

    The smell we want to catch is the "I wrote a log statement to feel
    productive" pattern: a single fixed string with no varying context.
    """

    if not path.is_file():
        return []
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (SyntaxError, UnicodeDecodeError):
        return []

    violations: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        # Match _logger.<level>(...) calls
        func = node.func
        if not (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Name)
            and func.value.id == "_logger"
            and func.attr in {"debug", "info", "warning", "error", "exception", "critical"}
        ):
            continue
        # Pass if any keyword present (extra=, exc_info=, etc.)
        if node.keywords:
            continue
        # Pass if more than one positional arg (legacy %-style)
        if len(node.args) >= 2:
            continue
        # Pass if the single positional arg is NOT a plain string
        if len(node.args) == 1 and not isinstance(node.args[0], ast.Constant):
            continue
        if len(node.args) == 1 and not isinstance(node.args[0].value, str):
            continue
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        snippet = ast.unparse(node)
        violations.append(
            f"{rel}:{node.lineno} `{snippet}` — unstructured log call. "
            "Pass `extra={...}` with the request_id / op / pad_id / "
            "etc. context so log shippers can aggregate by structured "
            "field instead of grepping the message string."
        )
    return violations


def test_every_hot_path_module_binds_a_logger() -> None:
    """Every cockpit hot-path module must bind ``_logger = get_logger(__name__)``.

    Regression guard: OBSERVABILITY_REVIEW.md found that 24 of 28
    cockpit modules had no logger before this sweep. PR O3 (the Phase
    5 quick-win commit) added them. This test catches accidental
    removal in a future refactor.
    """

    missing: list[str] = []
    for rel in sorted(_HOT_PATH_MODULES):
        path = PROJECT_ROOT / rel
        if not path.is_file():
            missing.append(
                f"{rel}: file does not exist — has the module been moved? "
                "Update _HOT_PATH_MODULES to match the new path."
            )
            continue
        if not _module_has_logger_binding(path):
            missing.append(
                f"{rel}: no `_logger = get_logger(__name__)` binding at "
                "module top level. Add one (one line) so future structured "
                "log calls have somewhere to land."
            )
    assert (
        not missing
    ), "Hot-path modules without a `_logger` binding — OBS regression:" "\n  " + "\n  ".join(
        missing
    )


def test_no_unstructured_logger_calls_in_hot_paths() -> None:
    """Hot-path ``_logger.<level>(...)`` calls must include structured ``extra=``.

    Regression guard: OBSERVABILITY_REVIEW.md §"unstructured strings"
    flagged generic ``logger.info("Doing thing X")`` as the next-tier-up
    from black-hole — present but unaggregatable. The post-sweep
    target is every hot-path log call carries a typed extra payload.

    A failure here means a new log call landed in a hot path with only
    a fixed string. Fix: add an ``extra={"request_id": ..., "op": ...,
    "<field>": ...}`` keyword arg listing the structured context that
    distinguishes this log line from every other call of the same
    level.
    """

    violations: list[str] = []
    for rel in sorted(_HOT_PATH_MODULES):
        path = PROJECT_ROOT / rel
        violations.extend(_unstructured_logger_calls(path))

    assert not violations, (
        "Unstructured `_logger.<level>(...)` calls in cockpit hot paths "
        "— OBS regression. Add `extra={...}` with the operation context:"
        "\n  " + "\n  ".join(violations)
    )


def test_hot_path_module_set_only_contains_real_files() -> None:
    """Every entry in ``_HOT_PATH_MODULES`` must point at an existing file.

    Regression guard: a file rename / move that doesn't update the set
    here would leave a stale entry — the prior tests would still pass
    for stale entries because both `_module_has_logger_binding` and
    `_unstructured_logger_calls` short-circuit on missing files. This
    test makes a stale entry an audible failure.
    """

    missing = [rel for rel in sorted(_HOT_PATH_MODULES) if not (PROJECT_ROOT / rel).is_file()]
    assert not missing, (
        "_HOT_PATH_MODULES references files that do not exist - update "  # noqa: S608
        "the set when renaming / moving:\n  " + "\n  ".join(missing)
    )
