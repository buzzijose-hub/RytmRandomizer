# Observability

> Practical guide to the RytmRandomizer package's logging, error taxonomy, and
> operation tracing. Pair this with `docs/ARCHITECTURE.md` for the layered
> module map.

## Why a separate observability layer?

The package keeps a clean separation between two channels of output:

| Channel       | Audience          | Owner                              |
|---------------|-------------------|-------------------------------------|
| **stdout**    | The human operator | The interactive shell + V1.34-parity engines. They print menus, prompts, and the line-by-line "  X: CC42 -> 64" banners that mirror the byte-frozen monolith. |
| **stderr / log** | The troubleshooter | The package logger. Structured, level-filtered, grep-friendly. |

The two never get mixed. A change to the interactive UI does not bleed into the
log; a debug session does not pollute the operator's terminal.

## Turning on debug logging

```sh
python -m rytm_randomizer.app --debug
python -m rytm_randomizer.app --debug --log-json
python -m rytm_randomizer.app --arm --debug   # real MIDI, full diagnostics
```

- Without `--debug`, the package logger runs at `INFO` and only emits at
  meaningful operation boundaries.
- With `--debug`, it runs at `DEBUG`: every `operation()` span (scene runs,
  group mutations, engine loads, port opens) logs entry / exit / elapsed
  time, and every CC sent via `midi_io.send_cc` is logged with channel,
  control number, and value.
- With `--log-json`, the formatter switches from the structured human-readable
  layout to one JSON object per line so a log shipper or a tool like `jq`
  can ingest the stream.

## Structured log format

The default formatter produces:

```
<asctime> <levelname> <logger_name> <op_id> <message>
```

- `asctime` -- ISO-ish local timestamp, e.g. `2026-05-15 09:14:02,317`.
- `levelname` -- `DEBUG` / `INFO` / `WARNING` / `ERROR`.
- `logger_name` -- the dotted package path, e.g.
  `rytm_randomizer.scene_runner`. A `__name__` from any package module is
  what you get back from
  [`get_logger`](../rytm_randomizer/observability/logging.py).
- `op_id` -- the current `operation()` span id (e.g. `scene_run/12`) or empty
  if not inside a span. See [tracing](#operation-tracing) below.
- `message` -- the log call's message, including any structured fields appended
  through `logger.X(msg, extra={...})`.

The JSON formatter emits the same fields plus any caller-supplied `extra` keys:

```json
{
  "ts": "2026-05-15T09:14:02",
  "level": "DEBUG",
  "logger": "rytm_randomizer.midi_io",
  "message": "midi_send cc",
  "op_id": "scene_run/12",
  "channel": 0,
  "control": 15,
  "value": 26,
  "kind": "midi_send"
}
```

## Error taxonomy

Every exception raised by package code is a member of one base hierarchy:

| Class                    | Use when                                                      |
|--------------------------|---------------------------------------------------------------|
| `RytmRandomizerError`    | Root. Every domain error inherits from this.                  |
| `MidiError`              | MIDI-boundary failure (port discovery / open / send).         |
| `StateError`             | Invalid state transition or missing required runtime state.   |
| `DataError`              | Missing or malformed entry in `rytm_randomizer/data/`.        |
| `BoundaryError`          | Boundary / contract violation that is not MIDI- or data-shaped. |
| `ConfigError`            | CLI flag / mode / level-name misuse.                          |

The existing module-local error classes are re-homed under this hierarchy via
multi-inheritance so `isinstance(err, MidiError)` returns `True` for every
adapter error, AND existing `except RuntimeError` / `except ValueError`
callers keep working unchanged:

```python
class RealMidiDependencyError(MidiError, RuntimeError): ...
class RealMidiPortError       (MidiError, RuntimeError): ...
class RealMidiSendError       (MidiError, RuntimeError): ...
class MockMessageMappingError (DataError, ValueError): ...
class ActiveBoundaryError     (BoundaryError, ValueError): ...
```

Every taxonomy class accepts an optional `context: Mapping` so callers can
attach structured diagnostic data alongside the message:

```python
from rytm_randomizer.observability.errors import StateError

raise StateError(
    "no profile selected",
    context={"command": "m", "active_profile": None},
)
```

When stringified, an error with empty context returns just the message; an
error with non-empty context appends a deterministic `[context: ...]` tail.

## Operation tracing

The [`operation`](../rytm_randomizer/observability/tracing.py) context
manager logs entry / exit / elapsed time for any block of work:

```python
from rytm_randomizer.observability.tracing import operation

with operation("scene_run", scene_key="S1A"):
    self.group.mutate_group_intensity("balanced")
```

Output (at `--debug`):

```
2026-05-15 09:14:02,317 DEBUG rytm_randomizer.scene_runner scene_run/12 operation_start scene_run scene_key='S1A'
... (the engine prints its V1.34 banner on stdout) ...
2026-05-15 09:14:02,512 DEBUG rytm_randomizer.scene_runner scene_run/12 operation_end scene_run elapsed_ms=194.612
```

Every log record emitted from inside the `with` block inherits the same
`scene_run/12` `op_id` so a structured search like `grep "scene_run/12"`
returns every record from that one run.

There is also a decorator form for instrumenting a single method by name:

```python
from rytm_randomizer.observability.tracing import trace

class Pad1Engine:
    @trace("pad1.load_pad1_bd_profile")
    def load_pad1_bd_profile(self, profile_key: str) -> None:
        ...
```

Tracing is currently wired at the following boundaries:

- `SceneRunner.run_scene` -- one span per scene command (`S0` ... `S5`).
- `GroupRunner.mutate_group` and `mutate_group_intensity`.
- `Pad{1,2,3,4}Engine.load_*` / `rotate_*` / `mutate_current_*` -- one span
  per engine action.
- `MidoMidiPortProvider.open_output` -- one span per real-port open.
- `tests/_parity_worker.py::ParityWorker.request` -- one span per parity
  round-trip, for diagnosing slow parity checks.

## Standard log-message patterns

Two patterns occur often enough to be worth calling out:

**MIDI send breadcrumbs.** Every CC pushed through `midi_io.send_cc` logs at
`DEBUG`:

```
... DEBUG rytm_randomizer.midi_io ... midi_send cc
```

with `extra={"channel": ..., "control": ..., "value": ..., "kind":
"midi_send"}`. To reconstruct exactly what an `--arm` run wrote to the wire,
re-run with `--debug --log-json` and pipe through `jq 'select(.kind ==
"midi_send")'`.

**Operation errors.** When an `operation()`-wrapped block raises, the span
emits one `operation_error` record at `ERROR` with the elapsed time, the
exception type, and a full traceback under `exc_info`. A debug session can
correlate the failure to the most recent `operation_start` by `op_id`.

**Export RED metrics.** Profile-model and Analog Four saved-kit file exports
share `MidiMetrics.record_export`: one count, cumulative duration, and a stable
categorical error counter per invocation. The A4 path emits `validation`,
`source_read_failed`, `overwrite_refused`, or `write_failed`; success records no
error code. Its structured success log includes output path, SHA256, and
mutation count. Failure logs include source/output paths and the categorical
code. A POSIX temp-name cleanup failure after successful hard-link publication
is logged as `atomic_write_cleanup` but does not convert a valid output into a
failed export.

The audio patch-batch service uses the same export RED metric and emits
`a4_audio_patch_batch_export` structured records. Success includes output
directory, manifest SHA256, and candidate count. Failure includes audio,
source-kit, and output paths with `source_read_failed`, `overwrite_refused`,
`write_failed`, `validation`, or `inference_failed`. The CLI additionally
returns stable operator-facing `error_code` values and never emits MIDI-send
breadcrumbs because this path performs no MIDI operation.

## Adding logging to a new module

```python
# at the top of the module
from rytm_randomizer.observability.logging import get_logger

_logger = get_logger(__name__)


def do_something() -> None:
    _logger.debug("starting do_something")
    ...
```

The architecture conformance test
[`tests/architecture/test_observability.py`](../tests/architecture/test_observability.py)
fails the build if a NEW package module uses bare `print()` instead of the
logger, or raises something outside the taxonomy. The V1.34-parity stdout-UI
files (engines, runners, midi_io, randomization, shell, cli) are
explicitly allow-listed there because their `print()` output is the
operator's UI and mirrors the byte-frozen monolith.
