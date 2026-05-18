# Implementation Plan: WS-S1 — MidiSender Protocol

## Overview

Replace the 7 module-level `Sender = Any` escape-hatch aliases with a single `@runtime_checkable` `MidiSender(Protocol)` exposing one method (`send(message: object) -> None`). Annotation-only change: zero runtime-behavior delta, V1.34 parity fixtures stay byte-identical. The lone runtime change is the cosmetic flattening of the `__class__.__name__ == "MockMidiSender"` string-sniff at `midi_io.py:96-109` (the inner `isinstance` was already the semantic guard; the outer string check is redundant).

**Per docs/PLAN_REQUIREMENTS.md** — all 16 gates apply. WS-S1 is the founding instance of Gate 6 (type-system hygiene).

## Architecture Changes

| File | Change | Risk |
|---|---|---|
| `rytm_randomizer/midi_io.py:50` | Add `MidiSender(Protocol)` class; rebind `Sender = MidiSender`; add `MidiSender` to `__all__`. | Low |
| `rytm_randomizer/midi_io.py:96-109` | Flatten: drop the outer `out.__class__.__name__ == "MockMidiSender"` test; keep the inner `isinstance(out, MockMidiSender)` block. Hoist the `from .mock_midi import MidiMessage, MockMidiSender` lazy import. | Low |
| `rytm_randomizer/shell.py:58` | Delete `Sender = Any`; add `from .midi_io import Sender`. | Low |
| `rytm_randomizer/group_runner.py:59` | Delete `Sender = Any`; add `from .midi_io import Sender`. | Low |
| `rytm_randomizer/engines/pad1.py:50` | Delete `Sender = Any`; add `from ..midi_io import Sender`. | Low |
| `rytm_randomizer/engines/pad2.py:45` | Delete `Sender = Any`; add `from ..midi_io import Sender`. | Low |
| `rytm_randomizer/engines/pad3.py:60` | Delete `Sender = Any`; add `from ..midi_io import Sender`. | Low |
| `rytm_randomizer/engines/pad4.py:60` | Delete `Sender = Any`; add `from ..midi_io import Sender`. | Low |
| `rytm_randomizer/randomization.py:30` | UNCHANGED — already imports `Sender` from `.midi_io`. Verification site. | None |
| `tests/test_midi_sender_protocol.py` | New file: 7 tests covering Protocol export, `@runtime_checkable`, three implementor conformance (MockMidiSender, RealMidiSender, fake mido), negative case, and both branches of the formerly-class-name-sniff site in `send_cc`. | Low |

## Exact Protocol definition

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class MidiSender(Protocol):
    """Anything with ``send(message)`` accepts a CC message.

    Satisfied structurally by:
      * :class:`mido.ports.BaseOutput` (hardware path),
      * :class:`rytm_randomizer.mock_midi.MockMidiSender` (in-process tests),
      * :class:`rytm_randomizer.real_midi_adapter.RealMidiSender` (fake-provider tests).

    Runtime-checkable because ``midi_io.send_cc`` switches on
    ``isinstance(out, MockMidiSender)`` to record an inert
    :class:`~rytm_randomizer.mock_midi.MidiMessage` instead of constructing
    a real ``mido.Message``. Per docs/ARCHITECTURE.md the boundary uses a
    ``Protocol`` (not an ABC) because the V1.34 codebase never owned the
    ``mido.ports.BaseOutput`` class definition; structural typing is the
    only way to admit all three implementations without monkey-patching.
    """

    def send(self, message: object) -> None: ...


Sender = MidiSender  # canonical re-name; single binding in the package
```

## Implementation phases

### Phase 1 — TDD RED (tdd-guide writes failing tests first)

New file `tests/test_midi_sender_protocol.py` with 7 tests:

1. **Protocol export and shape** — assert `MidiSender` exists, is `@runtime_checkable`, in `__all__`.
2. **`MockMidiSender` conforms** — `assert isinstance(MockMidiSender(), MidiSender)`.
3. **`RealMidiSender` conforms** — build with fake provider, assert isinstance.
4. **`mido.ports.BaseOutput`-shaped object conforms** — local `_FakeMidoOutput` with `def send(self, message: object) -> None`.
5. **Non-conforming object rejected** — class with no `send` method → False.
6. **`isinstance(out, MockMidiSender)` branch in `send_cc` records to mock** — install fake mido, pass MockMidiSender, assert recorded message.
7. **`send_cc` falls through to `mido.Message` for non-mock sender** — install fake mido, pass RecordingOut, assert mido.Message constructed.

Verify RED: `pytest tests/test_midi_sender_protocol.py -q` → ImportError (no MidiSender symbol).

### Phase 2 — Implementation

1. Add Protocol block to `midi_io.py` at line 50.
2. Rebind `Sender = MidiSender`.
3. Export `MidiSender` in `__all__`.
4. Flatten `send_cc` class-name sniff (lines 96-109).
5. Drop six `Sender = Any` lines from shell.py, group_runner.py, engines/pad{1-4}.py; add `from .midi_io import Sender` (or `from ..midi_io import Sender` for the four engines).
6. Verify `randomization.py:30` already imports correctly.

Verify GREEN: `pytest tests/test_midi_sender_protocol.py -q` + `pytest tests/test_engines_pad*.py tests/test_group_runner.py tests/test_scene_runner.py -q`.

### Phase 3 — Dead-code purge (Gate 4)

```powershell
$touched = @(
  "rytm_randomizer/midi_io.py",
  "rytm_randomizer/shell.py",
  "rytm_randomizer/group_runner.py",
  "rytm_randomizer/engines/pad1.py",
  "rytm_randomizer/engines/pad2.py",
  "rytm_randomizer/engines/pad3.py",
  "rytm_randomizer/engines/pad4.py",
  "tests/test_midi_sender_protocol.py"
)
python -m vulture $touched --min-confidence 80
python -m ruff check --select F401,F811,F841,ARG001,ARG002,ERA001 $touched
```

### Phase 4 — Coverage gate (Gate 1: 100% branch)

```powershell
python -m pytest `
  --cov=rytm_randomizer.midi_io `
  --cov=rytm_randomizer.shell `
  --cov=rytm_randomizer.group_runner `
  --cov=rytm_randomizer.engines.pad1 `
  --cov=rytm_randomizer.engines.pad2 `
  --cov=rytm_randomizer.engines.pad3 `
  --cov=rytm_randomizer.engines.pad4 `
  --cov-branch --cov-fail-under=100 --cov-report=term-missing
```

### Phase 5 — Lint / type (Gate 3)

```powershell
python -m ruff check <touched paths>
python -m black --check <touched paths>
python -m isort --profile black --check-only <touched paths>
python -m pyright --strict <touched paths>
```

### Phase 6 — Review (parallel)

- `python-reviewer` — Protocol choice over ABC; canonical alias rationale.
- `code-reviewer` — boundary discipline; no Sender exported from other modules.
- `security-reviewer` — `@runtime_checkable` safety note.

### Phase 7 — Docs (Gate 5)

- `docs/STATUS.md` — Recent Cleanup entry for WS-S1.
- `docs/ARCHITECTURE.md` — MIDI boundary table gets `MidiSender(Protocol)` row.
- `docs/ARCHITECTURE_DIAGRAMS.md` — mock/real adapter diagram updated.

### Phase 8 — PR open

`gh pr create` with conformance checklist citing PLAN_REQUIREMENTS.md.

## Risks & mitigations

- **Removing outer `__class__.__name__` guard:** the inner `isinstance` was already the semantic gate; outer was redundant. Parity suite + Test 7 (non-mock fallthrough) is the safety net.
- **`@runtime_checkable` permissiveness:** accepts any class with `.send`. Actual safety comes from `RealMidiSender._port.send(...)` inside `real_midi_adapter._translate_message`. Documented in module docstring.
- **Pre-existing untyped consumers surfaced by pyright `--strict`:** scope gate is touched-files-only; pre-existing gaps outside scope. If inside touched files, fix in this PR (a WS-S1 win).
- **New cross-module import edges from engines to midi_io:** edges already exist via `from .. import midi_io as _midi_io`; this is a narrowing, not a new cycle. `tests/architecture/test_import_direction.py` is the safety net.

## Success criteria

- [ ] `from rytm_randomizer.midi_io import MidiSender` succeeds; `@runtime_checkable`.
- [ ] `Sender = MidiSender` exists exactly once in the package.
- [ ] `Sender = Any` exists zero times (verified by grep).
- [ ] All three implementations conform: `MockMidiSender`, `RealMidiSender`, `_FakeMidoOutput`.
- [ ] Class-name string sniff gone from `send_cc`.
- [ ] All 505 V1.34 parity fixtures byte-identical.
- [ ] 100% branch coverage on 7 touched source files.
- [ ] `ruff` + `black --check` + `isort --check-only` + `pyright --strict` clean.
- [ ] `docs/STATUS.md` + `docs/ARCHITECTURE.md` updated.

## File path inventory (for orchestrator)

Source files touched: `rytm_randomizer/midi_io.py`, `shell.py`, `group_runner.py`, `engines/pad{1,2,3,4}.py`. New test: `tests/test_midi_sender_protocol.py`. Verification site (no change): `rytm_randomizer/randomization.py`.
