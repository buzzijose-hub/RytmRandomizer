"""Shared warm-subprocess infrastructure for the Wave-4 parity test files.

The Wave-4 parity tests (``test_engines_pad{1..4}``, ``test_scene_runner``,
``test_group_runner``) each prove an extracted engine/runner reproduces the
V1.34 monolith byte-for-byte. Every parity check has to run *inside a
subprocess* because the monolith does ``import mido`` at module scope and the
package's import-safety tests depend on real ``mido`` never landing in the test
interpreter's ``sys.modules``.

The original design spawned a *fresh* interpreter per parity check
(``subprocess.run([sys.executable, "-c", code], ...)``). Each spawn cold-imports
the monolith (a C extension via ``mido``) plus the whole ``rytm_randomizer``
package -- ~1-2s of pure startup, paid ~149 times across the suite.

This module replaces that with **one long-lived warm worker per test file**:
the monolith + package are imported *once* at worker startup, then the worker
loops reading one JSON request per line from stdin and writing one JSON
response per line to stdout. The per-check transport changes; the assertions
do not -- each request still runs that file's ``assert_parity(...)``, which
does the exact same byte-for-byte stdout / MIDI / state comparisons as before.
A parity mismatch is caught as an ``AssertionError`` in the worker and reported
back as ``{"ok": false, "error": "<assertion message>"}`` so the corresponding
test still fails with the diff.

Usage from a test file::

    from tests._parity_worker import ParityWorker, parity_worker_fixture

    _HARNESS = '''...defines assert_parity(seed, steps)...'''

    parity_worker = parity_worker_fixture(_HARNESS)  # module-scoped fixture

    def _parity_subprocess(steps_repr, seed=12345):
        # ``parity_worker`` is injected by pytest into the test, which passes
        # it down; or the thin wrapper closes over the fixture value.
        ...

The worker is launched lazily on first request and torn down at module
teardown. Reads/writes have timeouts; a worker that dies or hangs surfaces as a
clear test failure (with the worker's stderr) instead of an infinite hang --
preserving the spirit of the original ``timeout=120`` + ``stdin=DEVNULL``
safety.
"""

from __future__ import annotations

import ast
import json
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

# Hard caps mirroring the original ``timeout=120`` backstop. ``STARTUP_TIMEOUT``
# covers the one-time cold import of the monolith + package; ``REQUEST_TIMEOUT``
# bounds a single parity check (each is far quicker than a cold interpreter).
STARTUP_TIMEOUT = 120.0
REQUEST_TIMEOUT = 120.0
SHUTDOWN_TIMEOUT = 10.0


# The protocol loop appended after each file's ``_HARNESS``. The harness has
# already imported the monolith + package and defined ``assert_parity``; this
# loop just turns stdin/stdout into a request/response channel. ``assert_parity``
# is called with ``**request`` so a request dict of ``{"seed": ..., "steps":
# ...}`` maps onto ``assert_parity(seed, steps)`` and a dict that also carries
# ``"answers"`` maps onto ``assert_parity(seed, steps, answers)`` -- each file
# supplies whichever signature it needs, no per-file loop code required.
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
        try:
            assert_parity(**_request)
            _response = {"ok": True}
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
    transport the steps must instead travel as structured JSON, so this turns
    that same literal into the actual list/tuple object up front.

    ``_parse_python_literal`` is :func:`ast.literal_eval` -- it parses *only*
    Python literals and never executes code, so it is the safe, exact
    equivalent of how the literal was previously consumed.
    """

    return _parse_python_literal(steps_repr)


class ParityWorkerError(AssertionError):
    """Raised when the warm worker dies, hangs, or misbehaves.

    Subclasses ``AssertionError`` so a worker-transport failure fails the
    triggering test (never deadlocks or silently passes), exactly as the
    original ``assert result.returncode == 0`` did.
    """


class ParityWorker:
    """A lazily-launched, long-lived parity subprocess reused across a file.

    The worker imports the monolith + package once, then services one parity
    request per ``request()`` call over a stdin/stdout JSON line protocol.
    Thread-safe at the request level via an internal lock (pytest runs tests
    serially, but the lock keeps the protocol honest regardless).
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

    def request(self, payload: dict[str, Any]) -> None:
        """Send one parity request; raise ``AssertionError`` on any failure.

        ``payload`` is forwarded verbatim as the JSON request and unpacked into
        the harness's ``assert_parity(**payload)``. Returns ``None`` on a clean
        parity pass. On a parity *mismatch* the worker's assertion message is
        re-raised here as an ``AssertionError`` -- identical failure semantics
        to the per-call version. On a dead/hung/garbled worker a
        :class:`ParityWorkerError` (also an ``AssertionError``) is raised with
        the worker's stderr so the test fails loudly instead of hanging.

        Wrapped in a :func:`~rytm_randomizer.observability.tracing.operation`
        span at DEBUG so a developer running pytest with
        ``RYTM_DEBUG_LOG=1`` (which hooks the package logger -- see
        ``docs/OBSERVABILITY.md``) gets a per-request timing breadcrumb
        without altering the bytewise parity assertions inside the worker.
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

            request_line = json.dumps(payload) + "\n"
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
            return
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


def make_parity_subprocess(harness: str):
    """Return ``(autouse_fixture, parity_subprocess)`` for a parity test file.

    This is the turnkey entry point used by all six Wave-4 parity files. It
    wraps :func:`parity_worker_fixture` so that the existing ``test_parity_*``
    functions need *no* changes -- they keep calling a plain
    ``_parity_subprocess(...)`` helper, and only its implementation (the
    transport) changes from "spawn a fresh interpreter" to "send one JSON line
    to the warm worker".

    The returned ``autouse_fixture`` is a module-scoped, autouse pytest fixture:
    binding it at module scope launches/owns the warm worker for that file and
    tears it down at module teardown. It stashes the live worker in a closure
    cell that the returned ``parity_subprocess`` callable reads.

    The returned ``parity_subprocess(payload)`` callable takes the request dict
    (e.g. ``{"seed": 12345, "steps": [...]}``) -- whatever keyword arguments the
    file's ``assert_parity`` expects -- forwards it to the worker, and asserts
    the parity check passed. A parity mismatch raises ``AssertionError`` with
    the worker's diff message; a dead/hung worker raises
    :class:`ParityWorkerError`.
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
        worker.request(payload)

    return _parity_worker, parity_subprocess
