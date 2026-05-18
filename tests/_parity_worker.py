"""Shared warm-subprocess infrastructure for the Wave-4 parity test files.

The Wave-4 parity tests (``test_engines_pad{1..4}``, ``test_scene_runner``,
``test_group_runner``) prove the extracted engine/runner reproduces the V1.34
reference behavior byte-for-byte. Historically that reference was the
``rytm_hybrid_randomizer_v134.py`` monolith itself: a warm worker subprocess
imported both the monolith and the package, ran the same input through each,
and asserted equality inside the worker.

The monolith has now been retired. The same V1.34 reference behavior is frozen
as JSON goldens under ``tests/fixtures/v134_parity/`` -- one fixture per
distinct parity request -- and the worker compares the engine's output to the
fixture instead of to a live monolith run. The protocol now supports two modes:

* ``mode == "check"`` (default) -- the worker runs ``run_engine_only(...)``
  for the request and asserts its output equals the ``expected`` payload
  shipped with the request (the JSON fixture, loaded test-side).
* ``mode == "capture"`` -- the worker runs ``capture_reference(...)`` and
  returns its output so the test-side wrapper can write a new fixture. Only
  invoked when ``PARITY_CAPTURE_MODE=1`` is set in the environment. When the
  monolith was retired this code path was used to regenerate every fixture in
  one pass; with the monolith gone, capture mode now calls the engine itself,
  so capture and check produce the same bytes -- regenerating a fixture is
  only meaningful when the engine's reference output is intentionally being
  updated.

The transport is still one warm subprocess per test file: each
:class:`ParityWorker` cold-imports the package once at startup and then
services one JSON request per stdin line. Reads/writes have timeouts; a worker
that dies or hangs surfaces as a clear test failure (with the worker's stderr)
instead of an infinite hang.

Usage from a test file::

    from tests._parity_worker import make_parity_subprocess

    _HARNESS = '''...defines run_engine_only(seed, steps, ...) and
                  capture_reference(seed, steps, ...) and
                  assert_engine_matches(seed, steps, expected, ...)...'''

    _parity_worker, _run_parity = make_parity_subprocess(_HARNESS, __name__)

    def _parity_subprocess(steps_repr, seed=12345):
        _run_parity({"seed": seed, "steps": parse_steps(steps_repr)})

The wrapper transparently handles fixture lookup / capture / comparison; tests
keep calling ``_parity_subprocess(...)`` exactly as before.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any

# ``ast.literal_eval`` parses *only* Python literal structures (lists, tuples,
# dicts, strings, numbers, booleans, ``None``) and never executes code -- it is
# the safe, recommended alternative to the builtin code evaluator. It is bound
# here under a plain name so call sites read clearly and so a literal-only
# parse is never confused with arbitrary code execution.
_parse_python_literal = ast.literal_eval

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = PROJECT_ROOT / "tests" / "fixtures" / "v134_parity"

# Hard caps mirroring the original ``timeout=120`` backstop. ``STARTUP_TIMEOUT``
# covers the one-time cold import of the package; ``REQUEST_TIMEOUT`` bounds
# a single parity check (each is far quicker than a cold interpreter).
STARTUP_TIMEOUT = 120.0
REQUEST_TIMEOUT = 120.0
SHUTDOWN_TIMEOUT = 10.0

CAPTURE_ENV_VAR = "PARITY_CAPTURE_MODE"


def _capture_mode_enabled() -> bool:
    """``True`` when ``PARITY_CAPTURE_MODE=1`` is set in the environment."""

    return os.environ.get(CAPTURE_ENV_VAR, "").strip() not in ("", "0", "false", "False")


# The protocol loop appended after each file's ``_HARNESS``. The harness has
# already imported the package and defined three functions:
#
#   * ``run_engine_only(seed, steps, **kwargs)`` -- run the engine for one
#     request and return a JSON-serializable dict (stdout text, MIDI list, state
#     dict). Used internally by the other two.
#   * ``capture_reference(seed, steps, **kwargs)`` -- return the dict that the
#     test-side wrapper will write to a fixture file. Same shape as
#     ``run_engine_only``'s output; harnesses that need an out-of-band setup
#     baseline (Pad-3 / Pad-4) include it in this dict so check-mode can
#     re-seed the engine identically.
#   * ``assert_engine_matches(seed, steps, expected, **kwargs)`` -- run the
#     engine for one request and assert its output equals ``expected`` (loaded
#     from a fixture). Raises ``AssertionError`` with a diff message on a
#     mismatch.
#
# The loop reads one JSON request per stdin line; ``mode`` selects between
# ``capture`` and ``check`` (default). All other request keys are forwarded as
# keyword arguments to the harness function.
_WORKER_LOOP = r"""

import json as _json
import sys as _sys


def _parity_worker_main():
    _out = _sys.stdout
    for _line in _sys.stdin:
        _line = _line.strip()
        if not _line:
            continue
        try:
            _request = _json.loads(_line)
        except Exception as _exc:  # pragma: no cover - defensive
            _out.write(_json.dumps({"ok": False, "error": "bad request: "
                                    + repr(_exc)}) + "\n")
            _out.flush()
            continue
        _mode = _request.pop("mode", "check")
        try:
            if _mode == "capture":
                _captured = capture_reference(**_request)
                _response = {"ok": True, "captured": _captured}
            elif _mode == "check":
                assert_engine_matches(**_request)
                _response = {"ok": True}
            else:
                _response = {"ok": False, "error": "unknown mode: " + repr(_mode)}
        except AssertionError as _exc:
            _response = {"ok": False, "error": str(_exc)}
        except Exception as _exc:  # pragma: no cover - defensive
            _response = {"ok": False, "error": "worker error: " + repr(_exc)}
        _out.write(_json.dumps(_response) + "\n")
        _out.flush()


_parity_worker_main()
"""


def parse_steps(steps_repr: str) -> Any:
    """Parse a ``steps`` source repr into the real Python object.

    The Wave-4 ``test_parity_*`` functions build their ``steps`` argument as a
    *source repr* string (e.g. ``"[('load_pad1_bd_profile', ('2',))]"``) and
    the original code string-concatenated it straight into the subprocess
    program text: ``assert_parity(seed, <steps_repr>)``. With the warm-worker
    transport the steps travel as structured JSON, so this turns that same
    literal into the actual list/tuple object up front.

    ``_parse_python_literal`` is :func:`ast.literal_eval` -- it parses *only*
    Python literals and never executes code, so it is the safe, exact
    equivalent of how the literal was previously consumed.
    """

    return _parse_python_literal(steps_repr)


def _fixture_digest(module_id: str, payload: dict[str, Any]) -> str:
    """Stable 16-char hex digest of ``(module_id, payload)``.

    ``module_id`` (typically the importing test module's ``__name__``) is
    folded into the digest so two test files that happen to send the same
    ``{"seed": ..., "steps": ...}`` request still resolve to distinct fixture
    files -- prevents accidental collisions if e.g. Pad 1 and Pad 2 reuse the
    same seed.
    """

    canonical = json.dumps(
        {"module": module_id, "payload": payload},
        sort_keys=True,
        separators=(",", ":"),
        default=_json_default,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def _json_default(obj: Any) -> Any:
    """Coerce stray tuples to lists for stable JSON serialization."""

    if isinstance(obj, tuple):
        return list(obj)
    raise TypeError(f"object of type {type(obj).__name__} is not JSON-serializable")


def _fixture_path(module_id: str, payload: dict[str, Any]) -> Path:
    safe_module = module_id.rsplit(".", 1)[-1]
    digest = _fixture_digest(module_id, payload)
    return FIXTURE_ROOT / f"{safe_module}__{digest}.json"


class ParityWorkerError(AssertionError):
    """Raised when the warm worker dies, hangs, or misbehaves.

    Subclasses ``AssertionError`` so a worker-transport failure fails the
    triggering test (never deadlocks or silently passes), exactly as the
    original ``assert result.returncode == 0`` did.
    """


class FixtureMissingError(AssertionError):
    """Raised when a parity fixture is required but does not exist.

    The remedy is documented in the message: re-run pytest with
    ``PARITY_CAPTURE_MODE=1`` set in the environment to regenerate the
    fixture from the current engine output. ``AssertionError`` lineage keeps
    the failure inside pytest's normal failure path so the diagnostic is
    surfaced in the report.
    """


class ParityWorker:
    """A lazily-launched, long-lived parity subprocess reused across a file.

    The worker imports the package once, then services one parity request per
    ``request()`` call over a stdin/stdout JSON line protocol. Thread-safe at
    the request level via an internal lock (pytest runs tests serially, but
    the lock keeps the protocol honest regardless).
    """

    def __init__(self, harness: str) -> None:
        self._source = harness + _WORKER_LOOP
        self._proc: subprocess.Popen[str] | None = None
        self._lock = threading.Lock()

    # -- lifecycle ---------------------------------------------------------

    def _ensure_started(self) -> subprocess.Popen[str]:
        if self._proc is not None:
            return self._proc
        proc = subprocess.Popen(
            [sys.executable, "-c", self._source],
            cwd=PROJECT_ROOT,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self._proc = proc
        return proc

    def close(self) -> None:
        """Tear the worker down: close stdin (EOF -> clean exit), then wait."""

        proc = self._proc
        if proc is None:
            return
        self._proc = None
        try:
            if proc.stdin is not None and not proc.stdin.closed:
                proc.stdin.close()
        except (OSError, ValueError):  # pragma: no cover - defensive
            pass
        try:
            proc.wait(timeout=SHUTDOWN_TIMEOUT)
        except subprocess.TimeoutExpired:  # pragma: no cover - defensive
            proc.kill()
            proc.wait()

    # -- request/response --------------------------------------------------

    def _read_stderr(self, proc: subprocess.Popen[str]) -> str:
        try:
            return proc.stderr.read() if proc.stderr is not None else ""
        except (OSError, ValueError):  # pragma: no cover - defensive
            return ""

    def request(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Send one parity request; return the worker's response dict.

        On a successful ``check`` returns ``{"ok": True}``; on a successful
        ``capture`` returns ``{"ok": True, "captured": {...}}``. A parity
        mismatch (or any other in-worker error) raises ``AssertionError``
        with the worker's message. A dead/hung worker raises
        :class:`ParityWorkerError`.

        Wrapped in a :func:`~rytm_randomizer.observability.tracing.operation`
        span at DEBUG so a developer running pytest with ``RYTM_DEBUG_LOG=1``
        gets a per-request timing breadcrumb.
        """

        # Lazy import to keep this module independent of package import order
        # in fresh interpreters that probe ``_parity_worker.py`` directly.
        from rytm_randomizer.observability.tracing import operation as _operation

        with self._lock, _operation("parity_round_trip"):
            proc = self._ensure_started()

            # Worker already dead before we even wrote? Surface its stderr.
            if proc.poll() is not None:
                stderr = self._read_stderr(proc)
                raise ParityWorkerError(
                    "parity worker exited before request "
                    f"(returncode={proc.returncode}):\n{stderr}"
                )

            request_line = json.dumps(payload, default=_json_default) + "\n"
            try:
                assert proc.stdin is not None
                proc.stdin.write(request_line)
                proc.stdin.flush()
            except (BrokenPipeError, OSError, ValueError) as exc:
                stderr = self._read_stderr(proc)
                raise ParityWorkerError(
                    f"parity worker stdin failed ({exc!r}); " f"worker stderr:\n{stderr}"
                ) from exc

            response_line = self._read_line_with_timeout(proc)

        # -- parse + assert (outside the lock; pure-local work) ------------
        try:
            response = json.loads(response_line)
        except json.JSONDecodeError as exc:
            raise ParityWorkerError(
                "parity worker returned non-JSON response: " f"{response_line!r}"
            ) from exc

        if response.get("ok") is True:
            return response
        # A parity mismatch (or worker-side error) -- re-raise with the
        # worker's message so the diff shows up in the failing test.
        raise AssertionError(response.get("error", "unknown parity failure"))

    def _read_line_with_timeout(self, proc: subprocess.Popen[str]) -> str:
        """Read one response line, bounded by ``REQUEST_TIMEOUT``.

        ``readline()`` on a pipe blocks with no native timeout, so it runs on a
        helper thread. If the read does not complete in time the worker is
        presumed hung -- it is killed and a :class:`ParityWorkerError` is
        raised. A read that returns ``""`` means EOF: the worker died
        mid-request, so its stderr is surfaced.
        """

        result: dict[str, str] = {}

        def _reader() -> None:
            try:
                assert proc.stdout is not None
                result["line"] = proc.stdout.readline()
            except (OSError, ValueError) as exc:  # pragma: no cover
                result["error"] = repr(exc)

        thread = threading.Thread(target=_reader, daemon=True)
        thread.start()
        thread.join(REQUEST_TIMEOUT)

        if thread.is_alive():
            # Worker is hung: kill it so the next test gets a fresh worker
            # instead of inheriting a wedged process, then fail this test.
            proc.kill()
            proc.wait()
            self._proc = None
            raise ParityWorkerError(
                f"parity worker timed out after {REQUEST_TIMEOUT}s "
                "(no response line); worker killed"
            )

        if "error" in result:  # pragma: no cover - defensive
            raise ParityWorkerError(f"parity worker stdout read failed: {result['error']}")

        line = result.get("line", "")
        if line == "":
            # EOF: the worker process died while handling the request.
            stderr = self._read_stderr(proc)
            returncode = proc.poll()
            self._proc = None
            raise ParityWorkerError(
                "parity worker died mid-request "
                f"(returncode={returncode}); worker stderr:\n{stderr}"
            )
        return line


def parity_worker_fixture(harness: str):
    """Build a *module-scoped* pytest fixture yielding a :class:`ParityWorker`.

    Each parity test file calls this once at module scope with its own
    ``_HARNESS`` string and binds the result to a fixture name. The worker is
    created when the fixture is first used, launched lazily on its first
    ``request()``, and closed at module teardown.
    """

    @pytest.fixture(scope="module")
    def _parity_worker():
        worker = ParityWorker(harness)
        try:
            yield worker
        finally:
            worker.close()

    return _parity_worker


def _load_fixture(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _save_fixture(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True, default=_json_default)
        fh.write("\n")


def make_parity_subprocess(harness: str, module_id: str):
    """Return ``(autouse_fixture, parity_subprocess)`` for a parity test file.

    ``module_id`` is folded into the fixture digest (typically the importing
    test module's ``__name__``) so two test files that happen to send the same
    request dict still resolve to distinct fixture files. Without this
    bookkeeping a Pad 1 and a Pad 2 file that both passed e.g. ``{"seed": 1,
    "steps": []}`` would clobber each other's fixtures.

    The returned ``autouse_fixture`` is a module-scoped, autouse pytest fixture:
    binding it at module scope launches/owns the warm worker for that file and
    tears it down at module teardown. It stashes the live worker in a closure
    cell that the returned ``parity_subprocess`` callable reads.

    The returned ``parity_subprocess(payload)`` callable performs the
    fixture-vs-engine dance:

    1. Compute the deterministic fixture path for ``(module_id, payload)``.
    2. If the fixture is missing and ``PARITY_CAPTURE_MODE`` is set, ship
       a capture request to the worker and write the result to disk.
    3. If the fixture is still missing, raise :class:`FixtureMissingError`
       with a clear ``PARITY_CAPTURE_MODE=1`` remedy.
    4. Load the fixture and ship a check request to the worker carrying the
       expected output; a mismatch raises ``AssertionError`` with the diff.
    """

    holder: dict[str, ParityWorker] = {}

    @pytest.fixture(scope="module", autouse=True)
    def _parity_worker():
        worker = ParityWorker(harness)
        holder["worker"] = worker
        try:
            yield worker
        finally:
            holder.pop("worker", None)
            worker.close()

    def parity_subprocess(payload: dict[str, Any]) -> None:
        worker = holder.get("worker")
        if worker is None:  # pragma: no cover - misuse guard
            raise ParityWorkerError(
                "parity worker fixture is not active; ensure the autouse "
                "fixture from make_parity_subprocess() is bound at module "
                "scope in this test file"
            )

        fixture_path = _fixture_path(module_id, payload)

        if not fixture_path.exists() and _capture_mode_enabled():
            capture_payload = dict(payload)
            capture_payload["mode"] = "capture"
            response = worker.request(capture_payload)
            captured = response.get("captured")
            if captured is None:  # pragma: no cover - defensive
                raise ParityWorkerError(f"capture mode returned no payload for {fixture_path.name}")
            _save_fixture(fixture_path, captured)

        if not fixture_path.exists():
            raise FixtureMissingError(
                f"parity fixture missing: {fixture_path.relative_to(PROJECT_ROOT)}\n"
                "  Run with PARITY_CAPTURE_MODE=1 to regenerate the fixture from "
                "the current engine output, then commit it."
            )

        fixture = _load_fixture(fixture_path)
        check_payload = dict(payload)
        check_payload["mode"] = "check"
        check_payload["expected"] = fixture
        worker.request(check_payload)

    return _parity_worker, parity_subprocess
