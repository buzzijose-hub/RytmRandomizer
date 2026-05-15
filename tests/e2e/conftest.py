"""Shared fixtures for the WS-R end-to-end test suite.

The fixtures here let every E2E test drive the **real entry point**
(:func:`rytm_randomizer.app.main`) programmatically with a scripted list of
operator commands, then capture the :class:`MockMidiSender` for assertions.

Determinism contract
====================

Every E2E run seeds Python's stdlib :mod:`random` with the project-wide E2E
seed :data:`E2E_RANDOM_SEED` (``12345``). The randomization core in
:mod:`rytm_randomizer.randomization` defaults to the same stdlib ``random``
module when no explicit RNG is injected (see :func:`build_shell`), so seeding
once at the start of each test makes the entire interactive flow
deterministic. Tests that depend on RNG outputs (mutation values, scene
intensity plans) therefore produce identical message sequences across runs.

Recording-sender shim
=====================

The app's ``--dry-run`` mode wires a :class:`MockMidiSender` into
:mod:`rytm_randomizer.shell`'s engines, runners, and MIDI helpers. Those
helpers build native :class:`mido.Message` objects -- not the package's own
:class:`MidiMessage` -- before calling ``out.send(...)``. To capture the
ordered MIDI stream for assertions without touching production code, the
:func:`recording_dry_run` fixture monkey-patches
:meth:`MockMidiSender.send` to ACCEPT either message type and record both
forms (the original mido message under ``.raw_sent`` plus an immutable
:class:`MidiMessage` projection under ``.sent_messages`` / ``.messages``).
This keeps the existing MockMidiSender contract intact for unit tests while
giving the E2E suite a uniform, immutable view of what would have hit the
real Rytm.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
import json
import random
import sys
from typing import Any, Callable, Iterable, Iterator, Sequence
from unittest import mock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# The project-wide E2E random seed. Picked once, committed, and used by every
# E2E test so the canonical golden file is reproducible across machines and
# CI runners. If a future test needs a different seed, override it inside the
# test -- never silently change this constant.
E2E_RANDOM_SEED: int = 12345

# Directory where the canonical golden expectation file lives. Committed.
GOLDEN_DIR: Path = Path(__file__).resolve().parent / "_golden"

# The documented V1.34 operator validation flow, used by the centerpiece
# canonical-flow test and several guardrail tests. Spelled here once so any
# future doc-driven additions stay co-located with the rest of the E2E
# infrastructure.
CANONICAL_VALIDATION_COMMANDS: tuple[str, ...] = (
    "SCN",
    "GM",
    "S1A",
    "S3A",
    "S3B",
    "S4B",
    "S5",
    "1",
    "Z",
    "Q",
)


@dataclass(frozen=True)
class CapturedMessage:
    """Immutable, JSON-stable projection of a single MIDI message.

    The E2E suite asserts on this rather than on native ``mido.Message``
    objects because (a) it is hashable / serializable and (b) every field
    that matters for V1.34 validation (channel, control, value) is captured
    explicitly. Equality with a stored golden dict is straightforward.
    """

    message_type: str
    channel: int
    control: int
    value: int

    @classmethod
    def from_any(cls, message: Any) -> "CapturedMessage":
        """Project a mido message OR a MidiMessage into a CapturedMessage."""

        if hasattr(message, "control") and hasattr(message, "value"):
            return cls(
                message_type=getattr(message, "type", "cc")
                or getattr(message, "message_type", "cc"),
                channel=int(getattr(message, "channel", 0)),
                control=int(message.control),
                value=int(message.value),
            )
        raise TypeError(
            f"Unsupported MIDI message object for E2E capture: {type(message)!r}"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "message_type": self.message_type,
            "channel": self.channel,
            "control": self.control,
            "value": self.value,
        }


@dataclass(frozen=True)
class E2EResult:
    """Outcome of a scripted ``--dry-run`` invocation.

    Holds the entry-point exit code, the recorded MIDI stream, and the
    captured stdout/stderr text for assertion in tests.
    """

    exit_code: int
    captured: tuple[CapturedMessage, ...]
    stdout: str
    stderr: str


# Dotted import paths that resolve directly to a callable whose ``sleep``
# default arg should be replaced for the duration of an E2E run.
#
# Functions: every helper that defaults ``sleep: SleepFunc = time.sleep``.
# Classes: every constructor that captures ``sleep`` into instance state and
# then passes that captured callable to the helpers above (so patching the
# helpers alone is not enough -- the class default already snapshotted the
# real ``time.sleep``).
#
# Canonical search: ``grep -rn "sleep: SleepFunc = time.sleep" rytm_randomizer/``.
_SLEEP_PATCH_FUNCTIONS: tuple[str, ...] = (
    "rytm_randomizer.midi_io.send_cc",
    "rytm_randomizer.midi_io.send_machine",
    "rytm_randomizer.midi_io.send_param",
    "rytm_randomizer.midi_io.apply_state",
    "rytm_randomizer.randomization.mutate_zone",
    "rytm_randomizer.randomization.random_waveform",
    "rytm_randomizer.shell.build_shell",
)

# Classes that capture ``sleep`` into ``self.sleep`` at construction time.
_SLEEP_PATCH_CLASS_INITS: tuple[str, ...] = (
    "rytm_randomizer.group_runner.GroupRunner",
    "rytm_randomizer.engines.pad1.Pad1Engine",
    "rytm_randomizer.engines.pad2.Pad2Engine",
    "rytm_randomizer.engines.pad3.Pad3Engine",
    "rytm_randomizer.engines.pad4.Pad4Engine",
    "rytm_randomizer.shell.InteractiveShell",
)


def _resolve_dotted(path: str) -> Any:
    """Import ``a.b.c.Name`` and return the attribute ``Name`` on module ``a.b.c``."""

    import importlib

    module_path, _, attr = path.rpartition(".")
    module = importlib.import_module(module_path)
    return getattr(module, attr)


def _set_sleep_kwdefault(func: Any, value: Callable[[float], None]) -> Any:
    """Mutate ``func.__kwdefaults__['sleep']`` and return the prior value.

    ``sleep`` lives in :attr:`__kwdefaults__` because every target declares
    it as a keyword-only argument (after ``*``). Returns whatever ``sleep``
    was set to before the swap so :func:`_no_op_sleep_defaults` can restore
    it on exit.
    """

    kwdefaults = dict(func.__kwdefaults__ or {})
    prior = kwdefaults.get("sleep")
    kwdefaults["sleep"] = value
    func.__kwdefaults__ = kwdefaults
    return prior


@contextmanager
def _no_op_sleep_defaults(no_op_sleep: Callable[[float], None]) -> Iterator[None]:
    """Temporarily replace the ``sleep`` default arg of every MIDI helper.

    Both module-level helper functions and class ``__init__`` methods that
    capture ``sleep`` into instance state are patched so the entire send
    pipeline runs without inter-CC delays. The originals are restored on
    exit so the rest of the test suite (and any unit tests that explicitly
    assert on production timing) is unaffected.
    """

    restores: list[tuple[Any, str, Any]] = []
    try:
        for func_path in _SLEEP_PATCH_FUNCTIONS:
            func = _resolve_dotted(func_path)
            prior = _set_sleep_kwdefault(func, no_op_sleep)
            restores.append((func, "func", prior))

        for class_path in _SLEEP_PATCH_CLASS_INITS:
            cls = _resolve_dotted(class_path)
            init = cls.__init__
            prior = _set_sleep_kwdefault(init, no_op_sleep)
            restores.append((init, "init", prior))

        yield
    finally:
        for target, kind, prior in restores:
            kwdefaults = dict(target.__kwdefaults__ or {})
            if prior is None:
                # Defensive: never seen in practice, but if the target had no
                # prior sleep default, drop the key so we don't introduce one.
                kwdefaults.pop("sleep", None)
            else:
                kwdefaults["sleep"] = prior
            target.__kwdefaults__ = kwdefaults


def _make_recording_send(captured: list[CapturedMessage]) -> Callable[..., None]:
    """Build a replacement ``MockMidiSender.send`` that records both message
    types and stores their canonical projections in ``captured``.
    """

    def send(self: Any, message: Any) -> None:
        cap = CapturedMessage.from_any(message)
        captured.append(cap)
        # Keep the underlying MockMidiSender contract working for any
        # incidental consumer that reads .sent_messages on the sender itself.
        try:
            from rytm_randomizer.mock_midi import MidiMessage, build_cc_message

            if isinstance(message, MidiMessage):
                self._messages.append(message)
            else:
                self._messages.append(
                    build_cc_message(
                        channel=cap.channel,
                        control=cap.control,
                        value=cap.value,
                    )
                )
        except Exception:  # pragma: no cover - defensive: never fail recording
            pass

    return send


def run_canonical_dry_run(
    commands: Sequence[str],
    *,
    seed: int = E2E_RANDOM_SEED,
    capsys: pytest.CaptureFixture[str] | None = None,
) -> E2EResult:
    """Drive :func:`rytm_randomizer.app.main` through a scripted command flow.

    Steps:

    1. Seed :func:`random.seed` with ``seed`` so the randomization core
       (which falls back to the stdlib ``random`` module by default) is
       deterministic for the entire run.
    2. Build the full input queue: the shell prompts for target pad (``1``)
       and profile (``1`` = My BD Hard, the primary default) on entry,
       then reads one line per dispatched command.
    3. Patch :func:`builtins.input` to drain that queue.
    4. Patch :meth:`MockMidiSender.send` to record every outgoing message
       (mido or :class:`MidiMessage`) as a :class:`CapturedMessage`.
    5. Invoke ``app.main(["--dry-run"])`` and return the captured stream.
    """

    full_inputs: list[str] = ["1", "1", *commands]
    inputs_iter = iter(full_inputs)

    def feed_input(prompt: str = "") -> str:
        try:
            return next(inputs_iter)
        except StopIteration:
            # The interactive loop is still asking but our script is empty.
            # Mirror a closed stdin -- the shell catches EOFError and exits.
            raise EOFError("E2E input queue exhausted")

    captured: list[CapturedMessage] = []
    recording_send = _make_recording_send(captured)

    random.seed(seed)

    from rytm_randomizer import app
    from rytm_randomizer.mock_midi import MockMidiSender

    # The MIDI helpers default their inter-CC settle to ``time.sleep(0.02)``
    # (and a 0.4 s machine-switch settle in ``send_machine``). Those exist
    # to give the real Rytm time to ingest messages; in-memory recording
    # does not need them and they would push canonical-flow tests past
    # any sane CI timeout. ``app.py`` builds the shell without injecting a
    # sleep override, so each helper's *captured default argument* is the
    # ``time.sleep`` object resolved at module import time. We override
    # those captured defaults via :data:`_SLEEP_PATCH_TARGETS` so every
    # send-path uses a no-op while the patch is active. Production code is
    # untouched: the patch only lives for the duration of this run.
    no_op_sleep: Callable[[float], None] = lambda _seconds: None  # noqa: E731

    with _no_op_sleep_defaults(no_op_sleep), mock.patch(
        "builtins.input", feed_input
    ), mock.patch.object(MockMidiSender, "send", recording_send):
        try:
            exit_code = app.main(["--dry-run"])
        except SystemExit as exc:
            exit_code = int(exc.code) if isinstance(exc.code, int) else 0

    if capsys is not None:
        capture = capsys.readouterr()
        stdout, stderr = capture.out, capture.err
    else:
        stdout, stderr = "", ""

    return E2EResult(
        exit_code=int(exit_code),
        captured=tuple(captured),
        stdout=stdout,
        stderr=stderr,
    )


def load_golden(name: str) -> list[dict[str, Any]] | None:
    """Load the named golden JSON file from :data:`GOLDEN_DIR`.

    Returns ``None`` when the file does not exist yet -- the first run of a
    new canonical flow test bootstraps the golden by writing it out, then
    every subsequent run asserts against it.
    """

    golden_path = GOLDEN_DIR / f"{name}.json"
    if not golden_path.exists():
        return None
    with golden_path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def save_golden(name: str, messages: Iterable[CapturedMessage]) -> Path:
    """Write the given canonical message sequence to the golden directory."""

    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
    golden_path = GOLDEN_DIR / f"{name}.json"
    payload = [msg.to_dict() for msg in messages]
    with golden_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=False)
        fh.write("\n")
    return golden_path


@pytest.fixture(autouse=True)
def _isolate_midi_modules_from_other_tests() -> Iterator[None]:
    """Cleanup ``mido`` / ``rtmidi`` / ``pythonrtmidi`` from :data:`sys.modules`
    after every E2E test runs.

    The E2E suite exercises :func:`rytm_randomizer.midi_io.send_cc`, which
    imports :mod:`mido` lazily. Once imported, ``mido`` stays in
    :data:`sys.modules` for the rest of the worker process. Several legacy
    tests (e.g. ``test_mock_only_active_candidate.py``) assert that
    ``mido`` is **not** in :data:`sys.modules` after importing only the
    mock-only modules -- that assertion is order-sensitive when xdist
    schedules an E2E test into the same worker process first.

    To keep both contracts honored, this fixture pops the MIDI backend
    modules out of :data:`sys.modules` after every E2E test runs. Each new
    test then sees a clean module table just as if it had run first in
    its worker.
    """

    yield
    for module_name in ("mido", "rtmidi", "pythonrtmidi"):
        sys.modules.pop(module_name, None)
    # The rytm_randomizer.midi_io module captured ``mido`` lazily; clearing
    # it from sys.modules forces a re-import on the next E2E run, which
    # keeps the determinism contract intact across tests.


@pytest.fixture
def deterministic_seed() -> int:
    """Seed :mod:`random` with :data:`E2E_RANDOM_SEED` and return the seed.

    Tests that call into the randomization core directly (without going
    through :func:`run_canonical_dry_run`) use this fixture so the seeding
    contract is enforced uniformly.
    """

    random.seed(E2E_RANDOM_SEED)
    return E2E_RANDOM_SEED


@pytest.fixture
def run_e2e(
    capsys: pytest.CaptureFixture[str],
) -> Callable[[Sequence[str]], E2EResult]:
    """Return a callable that runs ``app.main(['--dry-run'])`` with scripted
    commands and captures the resulting MIDI stream + stdout/stderr.

    Example::

        def test_something(run_e2e):
            result = run_e2e(["SCN", "Q"])
            assert result.exit_code == 0
    """

    def _run(commands: Sequence[str], *, seed: int = E2E_RANDOM_SEED) -> E2EResult:
        return run_canonical_dry_run(commands, seed=seed, capsys=capsys)

    return _run
