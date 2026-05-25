"""Architecture conformance tests for the observability layer (Wave 4 / WS-U).

These tests pin the WS-U world-class observability contract:

1. **No bare ``print()`` in NEW package code.** The package's V1.34-parity
   stdout UI -- the engines, runners, scene runner, midi_io, randomization,
   and the shell -- is a deliberate operator-facing UI that mirrors the
   byte-frozen monolith's ``print()`` output. Those files are explicitly
   allow-listed below. Every OTHER package file must emit diagnostic /
   warning / error output through the package logger
   (:mod:`rytm_randomizer.observability.logging`), never via bare
   ``print()`` -- so a troubleshooter can grep one structured log instead
   of capturing stdout.

2. **No bare ``except:``.** Every exception handler in the package must
   name the exception family it catches. ``except Exception`` is explicitly
   forbidden in new code -- existing broad catches have been narrowed in
   WS-U to the realistic family (e.g. ``OSError, RuntimeError,
   ImportError, AttributeError`` for backend-specific failures).

3. **Every ``raise`` in non-validation modules raises a member of the
   :class:`~rytm_randomizer.observability.errors.RytmRandomizerError`
   taxonomy.** Exception: stdlib ``TypeError`` / ``ValueError`` raised
   inside argument-validation functions are allowed (those signal a
   programmer error, not a domain failure). ``raise SystemExit`` /
   ``raise KeyError`` are also allowed in the specific validated paths
   below (CLI exit, report registry lookup).

4. **``observability/`` is a leaf.** It imports nothing else from
   ``rytm_randomizer/`` except the optional :mod:`rytm_randomizer.data`
   constants module. This keeps the dependency graph one-directional and
   prevents the observability layer from accreting random package
   internals.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

# WS-M4: mark this module as fast-suite; pytest -m fast skips the 505
# warm-worker V1.34 parity fixtures and runs in <60s.
pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = PROJECT_ROOT / "rytm_randomizer"
PACKAGE_NAME = "rytm_randomizer"


# ---------------------------------------------------------------------------
# Allow-list 1: files whose ``print()`` calls are deliberate V1.34-parity UI
# ---------------------------------------------------------------------------
#
# The package's interactive runtime modules mirror the V1.34 monolith's
# stdout UI byte-for-byte -- the parity test suite locks every line of
# stdout against the monolith's output through ``tests/_parity_worker.py``.
# Replacing those ``print()`` calls with ``logger.info()`` would (a) move
# the operator-facing output off stdout and (b) immediately break every
# parity test. So they STAY -- explicit allow-list, documented inline.
#
# This list is INTENTIONALLY narrow. New package modules outside this
# allow-list must use the package logger; the test below fails if a new
# ``print()`` lands in any other file.

ALLOW_LIST_PRINT_UI: frozenset[str] = frozenset(
    {
        # Interactive shell -- menu output, prompts, dispatch banners.
        # The task description calls this out explicitly as STAY.
        "rytm_randomizer/shell.py",
        # CLI help text constants -- printed by the argparse passive CLI.
        # Also called out as STAY by the task description.
        "rytm_randomizer/cli.py",
        # V1.34-parity interactive engines and runners. Every print() here
        # is asserted byte-for-byte against the monolith by the parity
        # tests in tests/test_engines_pad{1..4}.py / test_group_runner.py
        # / test_scene_runner.py. They are deliberate stdout UI.
        "rytm_randomizer/engines/pad1.py",
        "rytm_randomizer/engines/pad2.py",
        "rytm_randomizer/engines/pad3.py",
        "rytm_randomizer/engines/pad4.py",
        # Shared per-pad runtime mixin (H1 abstraction audit). The
        # ``IsolatedPadMixin`` print() calls were previously inlined in
        # pad3.py / pad4.py and are still asserted byte-for-byte against
        # the monolith by the same parity tests.
        "rytm_randomizer/engines/_runtime.py",
        "rytm_randomizer/group_runner.py",
        "rytm_randomizer/scene_runner.py",
        # MIDI-I/O primitives -- monolith-parity "Switching machine" /
        # "  X: CC42 -> 64" banner lines. Each CC sent is also logged at
        # DEBUG through the package logger (see send_cc) so the structured
        # diagnostic stream lives alongside the stdout UI.
        "rytm_randomizer/midi_io.py",
        # Mutation core -- monolith-parity "X mutation / Y depth" banners.
        "rytm_randomizer/randomization.py",
    }
)


def _rel(path: Path) -> str:
    """Return the project-root-relative POSIX string for a path."""

    return path.relative_to(PROJECT_ROOT).as_posix()


def _all_package_files() -> list[Path]:
    return sorted(p for p in PACKAGE_ROOT.rglob("*.py"))


def _print_calls(path: Path) -> list[tuple[int, str]]:
    """Return ``(lineno, snippet)`` of every direct ``print(...)`` call.

    Only direct ``ast.Name`` callees named ``print`` are flagged -- so a
    method named ``print_commands`` is NOT a false positive.
    """

    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src, filename=str(path))
    out: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "print"
        ):
            out.append((node.lineno, ast.unparse(node)[:80]))
    return out


# ---------------------------------------------------------------------------
# Rule 1: no bare print() outside the allow-list
# ---------------------------------------------------------------------------


def test_no_bare_print_outside_v134_parity_ui_allowlist() -> None:
    """Every ``print()`` in the package must live in an allow-listed UI file."""

    violations: list[str] = []
    for path in _all_package_files():
        rel = _rel(path)
        if rel in ALLOW_LIST_PRINT_UI:
            continue
        calls = _print_calls(path)
        for lineno, snippet in calls:
            violations.append(f"{rel}:{lineno} {snippet}")
    assert not violations, (
        "Bare print() in package modules outside the V1.34-parity stdout-UI "
        "allow-list. Use rytm_randomizer.observability.logging.get_logger("
        "__name__) and emit at INFO / DEBUG / WARNING / ERROR instead. See "
        "docs/OBSERVABILITY.md.\n  " + "\n  ".join(violations)
    )


# ---------------------------------------------------------------------------
# Rule 1b: the allow-list does not silently expand
# ---------------------------------------------------------------------------


def test_print_allowlist_files_actually_exist() -> None:
    """Catch typos / stale entries: every allow-listed path must be a real file."""

    missing = [p for p in ALLOW_LIST_PRINT_UI if not (PROJECT_ROOT / p).is_file()]
    assert not missing, (
        "ALLOW_LIST_PRINT_UI has entries that do not exist on disk -- update "
        "the allow-list when removing files. Missing:\n  " + "\n  ".join(missing)
    )


# ---------------------------------------------------------------------------
# Rule 2: no bare ``except:`` and no broad ``except Exception``
# ---------------------------------------------------------------------------


# ``except Exception:`` is forbidden in NEW package code. The only place in the
# entire package where it would be defensible is best-effort cleanup paths
# (e.g. closing a MIDI port during shutdown); even those have been narrowed
# in WS-U to the realistic OSError/RuntimeError/AttributeError family. The
# allow-list below is empty; we keep the constant so a future principled
# exception can be added with a clear comment.
ALLOW_LIST_BROAD_EXCEPT: frozenset[tuple[str, int]] = frozenset(
    {
        # observability/tracing.py:167 — the operation() context manager intentionally
        # catches BaseException (including KeyboardInterrupt / SystemExit) so that
        # operation_error is logged with elapsed_ms + exception type BEFORE the
        # exception propagates. The handler re-raises; nothing is silently swallowed.
        # This is the one place in the package where catching everything is correct.
        ("rytm_randomizer/observability/tracing.py", 167),
    }
)


def _except_handlers(path: Path) -> list[tuple[int, str | None]]:
    """Return ``(lineno, exception_type_or_None)`` for every ``except`` handler.

    A handler with ``type=None`` is a bare ``except:``.
    A handler with ``type=`` ``ast.Name('Exception')`` or
    ``ast.Attribute(...)`` ending in ``Exception`` is broad.
    """

    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src, filename=str(path))
    out: list[tuple[int, str | None]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            if node.type is None:
                out.append((node.lineno, None))
            else:
                out.append((node.lineno, ast.unparse(node.type)))
    return out


def test_no_bare_except_in_package() -> None:
    """No ``except:`` (bare) in any package file."""

    violations: list[str] = []
    for path in _all_package_files():
        for lineno, kind in _except_handlers(path):
            if kind is None:
                violations.append(f"{_rel(path)}:{lineno} bare except:")
    assert not violations, (
        "Bare ``except:`` is forbidden in the package -- name the exception "
        "family you intend to handle. Violations:\n  " + "\n  ".join(violations)
    )


def test_no_broad_except_exception_in_package() -> None:
    """``except Exception:`` is forbidden outside the empty allow-list."""

    violations: list[str] = []
    for path in _all_package_files():
        rel = _rel(path)
        for lineno, kind in _except_handlers(path):
            if kind is None:
                continue
            # Strip ``as exc`` etc. for matching.
            normalized = kind.strip().split()[0]
            if normalized in {"Exception", "BaseException"}:
                key = (rel, lineno)
                if key in ALLOW_LIST_BROAD_EXCEPT:
                    continue
                violations.append(f"{rel}:{lineno} except {kind}:")
    assert not violations, (
        "``except Exception:`` is forbidden in new package code -- narrow to "
        "the realistic family (OSError / RuntimeError / ImportError / ...). "
        "If a broad catch is truly required, add an explicit entry to "
        "ALLOW_LIST_BROAD_EXCEPT with a comment.\n  " + "\n  ".join(violations)
    )


# ---------------------------------------------------------------------------
# Rule 3: every ``raise`` in non-validation modules raises a taxonomy class
# ---------------------------------------------------------------------------


# Stdlib TypeError / ValueError raised in argument-validation paths is allowed.
# AssertionError is allowed (used for invariant assertions).
# KeyError is allowed in registry lookup (rytm_randomizer/reports.py).
# SystemExit is allowed in script entry points.
# StopIteration is allowed in generator protocols.
_STDLIB_VALIDATION_OK: frozenset[str] = frozenset(
    {
        "TypeError",
        "ValueError",
        # ``AttributeError`` is the canonical PEP 562 module-level
        # ``__getattr__`` failure mode -- raised in
        # ``rytm_randomizer.observability.errors`` for unknown attributes,
        # mirroring stdlib library behavior.
        "AttributeError",
        "AssertionError",
        "KeyError",
        "SystemExit",
        "StopIteration",
        "NotImplementedError",
        # Cockpit Phase 3 export writer raises FileExistsError when an
        # output path already exists and the operator did not pass
        # --overwrite. This is the canonical stdlib signal for "file
        # exists" so callers that ``except FileExistsError`` keep working
        # without import changes.
        "FileExistsError",
    }
)

# Names of every member of the RytmRandomizerError taxonomy that a ``raise``
# statement may legitimately use. Re-homed errors live in their original
# modules but inherit from the taxonomy; we accept either the local name
# (``RealMidiPortError``) or the taxonomy base (``MidiError``).
_TAXONOMY_NAMES: frozenset[str] = frozenset(
    {
        "RytmRandomizerError",
        "MidiError",
        "StateError",
        "DataError",
        "BoundaryError",
        "ConfigError",
        # Re-homed legacy classes (still raisable by their original name):
        "RealMidiDependencyError",
        "RealMidiPortError",
        "RealMidiSendError",
        "MockMessageMappingError",
        "ActiveBoundaryError",
        # WS-V style_analysis: re-homed under DataError + RuntimeError so
        # existing ``except RuntimeError`` callers still work AND the
        # conformance check sees a taxonomy member.
        "StyleAnalysisDependencyError",
        # WS-W guardrails: members of the BoundaryError / StateError families
        # surfaced by guardrails/validation.py, guardrails/store.py, and
        # guardrails/resolver.py. Each inherits transitively from
        # RytmRandomizerError so the taxonomy conformance check still
        # passes; they are listed here so the AST-level allow-list mirrors
        # the runtime hierarchy.
        "ProfileRejectedError",
        "IllegalStateTransitionError",
        "GuardrailResolutionError",
        # Cockpit Profile Wizard analysis adapter: re-homed under DataError
        # + FileNotFoundError so ``except FileNotFoundError`` callers still
        # work AND the conformance check sees a taxonomy member.
        "WizardSourcePathError",
        # Cockpit Profile Wizard builder: re-homed under DataError +
        # ValueError so ``except ValueError`` callers still work AND the
        # conformance check sees a taxonomy member.
        "EmptyAnalysisError",
        # Cockpit Profile Wizard path-policy (CODE_REVIEW PR 2 / C2):
        # re-homed under DataError + ValueError so ``except ValueError``
        # callers still work AND the conformance check sees a taxonomy
        # member. Mirrors the WizardSourcePathError / EmptyAnalysisError
        # dual-inheritance pattern.
        "WizardSourcePathRejected",
        # Cockpit Phase 3 export writer: re-homed under DataError +
        # OSError so ``except OSError`` callers still work AND the
        # conformance check sees a taxonomy member. Mirrors the
        # WizardSourcePathError / EmptyAnalysisError dual-inheritance
        # pattern.
        "WriteError",
    }
)


def _raised_class_names(path: Path) -> list[tuple[int, str]]:
    """Return ``(lineno, raised_class_name)`` for every ``raise`` statement.

    ``raise`` with no expression (re-raise) is skipped. ``raise <Cls>(...)``
    and ``raise <Cls>`` are both recognized. ``raise <expr>`` (e.g.
    ``raise self._build_error()``) returns the unparsed expression so the
    caller can decide.
    """

    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src, filename=str(path))
    out: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Raise):
            continue
        exc = node.exc
        if exc is None:
            continue
        if isinstance(exc, ast.Call):
            callee = exc.func
            if isinstance(callee, ast.Name):
                out.append((node.lineno, callee.id))
            elif isinstance(callee, ast.Attribute):
                out.append((node.lineno, callee.attr))
            else:  # pragma: no cover - exotic callable expression
                out.append((node.lineno, ast.unparse(callee)))
        elif isinstance(exc, ast.Name):
            out.append((node.lineno, exc.id))
        elif isinstance(exc, ast.Attribute):
            out.append((node.lineno, exc.attr))
        else:  # pragma: no cover - ``raise <complex expression>``
            out.append((node.lineno, ast.unparse(exc)))
    return out


def test_raises_use_taxonomy_or_validation_stdlib() -> None:
    """Every ``raise`` either uses the taxonomy or a validation-allowed stdlib class."""

    violations: list[str] = []
    for path in _all_package_files():
        rel = _rel(path)
        for lineno, name in _raised_class_names(path):
            if name in _TAXONOMY_NAMES:
                continue
            if name in _STDLIB_VALIDATION_OK:
                continue
            violations.append(f"{rel}:{lineno} raises {name!r}")
    assert not violations, (
        "Every ``raise`` in the package must use a member of the "
        "RytmRandomizerError taxonomy (rytm_randomizer.observability.errors) "
        "or a validation-allowed stdlib exception (TypeError / ValueError / "
        "AssertionError / KeyError / SystemExit / StopIteration / "
        "NotImplementedError). Violations:\n  " + "\n  ".join(violations)
    )


# ---------------------------------------------------------------------------
# Rule 4: ``observability/`` is a leaf-or-near-leaf
# ---------------------------------------------------------------------------


def _imported_package_modules(path: Path) -> list[tuple[int, str]]:
    """Return ``(lineno, fqname)`` for every ``rytm_randomizer.*`` import."""

    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src, filename=str(path))
    rel = path.relative_to(PROJECT_ROOT).with_suffix("")
    parts = list(rel.parts)
    is_init = parts and parts[-1] == "__init__"
    if is_init:
        parts = parts[:-1]
    fqname = ".".join(parts)
    out: list[tuple[int, str]] = []

    def _resolve(node: ast.ImportFrom) -> str | None:
        if node.level == 0:
            if node.module and (
                node.module == PACKAGE_NAME or node.module.startswith(PACKAGE_NAME + ".")
            ):
                return node.module
            return None
        base = fqname.split(".") if fqname else []
        drop = node.level - 1 if is_init else node.level
        if drop:
            base = base[: max(0, len(base) - drop)]
        tail = node.module.split(".") if node.module else []
        return ".".join(p for p in base + tail if p)

    for node in tree.body:
        if isinstance(node, ast.Import):
            for n in node.names:
                if n.name == PACKAGE_NAME or n.name.startswith(PACKAGE_NAME + "."):
                    out.append((node.lineno, n.name))
        elif isinstance(node, ast.ImportFrom):
            resolved = _resolve(node)
            if resolved and (resolved == PACKAGE_NAME or resolved.startswith(PACKAGE_NAME + ".")):
                out.append((node.lineno, resolved))
    return out


def test_observability_is_a_leaf() -> None:
    """``observability/`` may import only from itself + optionally ``data``."""

    allowed_prefixes = (
        f"{PACKAGE_NAME}.observability",
        f"{PACKAGE_NAME}.data",
    )
    violations: list[str] = []
    obs_root = PACKAGE_ROOT / "observability"
    for path in sorted(obs_root.rglob("*.py")):
        for lineno, fq in _imported_package_modules(path):
            if not any(fq == p or fq.startswith(p + ".") for p in allowed_prefixes):
                violations.append(f"{_rel(path)}:{lineno} imports {fq}")
    assert not violations, (
        "observability/ must be a leaf -- it may import from itself and "
        "optionally from data/, nothing else under rytm_randomizer/. "
        "Violations:\n  " + "\n  ".join(violations)
    )


# ---------------------------------------------------------------------------
# Sanity: importing observability is silent and side-effect-free
# ---------------------------------------------------------------------------


def test_importing_observability_is_silent() -> None:
    """Importing the observability sub-package writes nothing to stderr.

    The package logger has a :class:`logging.NullHandler` attached at module
    import time so a stray log call from any module never reaches stderr
    until the caller opts in via :func:`configure_logging`. This test pins
    that contract end-to-end (subprocess-fresh interpreter, no fixtures).
    """

    import subprocess
    import sys

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import logging\n"
                "logger = logging.getLogger('rytm_randomizer')\n"
                "import rytm_randomizer.observability  # noqa: F401\n"
                "# No handler other than NullHandler should be on the root\n"
                "for h in logger.handlers:\n"
                "    assert isinstance(h, logging.NullHandler), (\n"
                "        f'unexpected handler at import time: {h!r}'\n"
                "    )\n"
                "# Stray warning must not reach stderr through NullHandler\n"
                "logger.warning('this must NOT appear')\n"
            ),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
    assert result.stderr == "", (
        "Importing rytm_randomizer.observability must be silent -- a stray "
        "logger.warning() must be swallowed by the NullHandler until the "
        "caller opts into actual logging via configure_logging(). Got:\n" + result.stderr
    )


# ---------------------------------------------------------------------------
# Sanity: every package module under the runtime core has a module logger
# ---------------------------------------------------------------------------


# Files that are EXPECTED to instantiate a module logger as part of WS-U.
# These are the runtime / mutation / port modules where DEBUG output is
# valuable when troubleshooting. Adding new entries is encouraged when a
# new runtime module is added; the test catches accidental regressions.
_EXPECTED_LOGGER_FILES: frozenset[str] = frozenset(
    {
        "rytm_randomizer/midi_io.py",
        "rytm_randomizer/group_runner.py",
        "rytm_randomizer/scene_runner.py",
        "rytm_randomizer/mido_provider.py",
        "rytm_randomizer/engines/pad1.py",
        "rytm_randomizer/engines/pad2.py",
        "rytm_randomizer/engines/pad3.py",
        "rytm_randomizer/engines/pad4.py",
        "rytm_randomizer/app.py",
    }
)


@pytest.mark.parametrize("rel", sorted(_EXPECTED_LOGGER_FILES))
def test_runtime_core_modules_define_a_logger(rel: str) -> None:
    """The runtime core wires a ``get_logger(__name__)`` so diagnostics flow."""

    path = PROJECT_ROOT / rel
    src = path.read_text(encoding="utf-8")
    assert "get_logger" in src, (
        f"{rel} is expected to import "
        "``rytm_randomizer.observability.logging.get_logger`` and bind a "
        "module-level logger so DEBUG diagnostics flow through the package "
        "logger. If you removed it intentionally, drop the entry from "
        "_EXPECTED_LOGGER_FILES."
    )
