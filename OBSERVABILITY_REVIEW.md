# Observability Review

> Code-review fan-out OBS1-6. Audit of the RytmRandomizer package's current
> observability posture against a "world-class" target, with prioritized
> remediation PRs. Drop-in companion to `docs/OBSERVABILITY.md` (which
> documents the *current* shape) — this document scopes what's *missing*.

## TL;DR

The package has a solid **observability spine** — structured/JSON logger
formatter, `op_id` context propagation via `contextvars`, an exception
taxonomy with `context` payloads, and a metrics singleton — but the
**cockpit subsystem (the WS sidecar + export pipeline + wizard) is a near
black hole**: 24 of 28 cockpit modules have no module logger, the WS
command dispatcher emits zero log calls, and the per-request correlation
ID (`request_id`) never crosses into the structured logging field set.
The hot paths the operator drives every day — `select_profile`, `regen`,
`prepare_send_plan`, `send`, `wizard_*`, `cockpit-export-profile-model`
— are not observable.

The metrics surface (`observability/metrics.py`) is defined but **never
incremented** anywhere in the package today. RED metrics (Rate / Errors /
Duration) per WS command and per export are missing.

**Top 3 fixes (highest leverage, smallest blast radius):**

1. **PR O1 — `request_id` propagation through WS handlers.** Wire each
   command envelope's `request_id` into `operation()` as the `op_id`
   prefix so every log line emitted while processing a command carries
   the same correlator. This is a ~30-line change in `ws/handlers.py` +
   `ws/server.py` and lights up the entire WS command surface for free.
2. **PR O2 — RED metrics for WS commands + the export pipeline.** The
   counter dataclass already exists. Extend it with histograms for
   `ws_command_duration_ms{command}` + `ws_command_errors{command,kind}`
   + `export_duration_ms` and increment from `handle_command` /
   `cockpit-export-profile-model`. Five new counters, one increment
   site per command.
3. **PR O3 — bind module loggers in every cockpit module that does work
   (handlers, server, history, profiles, export pipeline, wizard
   internals).** A `_logger = get_logger(__name__)` one-liner per file
   — zero risk, lights up future structured log calls without churn.
   *(Phase 5 of this review adds them as a low-hanging-fruit batch.)*

---

## Methodology

What I read:

- `rytm_randomizer/observability/{logging,tracing,errors,metrics,__init__}.py`
  — the full current observability surface.
- `rytm_randomizer/cockpit/ws/{server,handlers,session,protocol,wizard_handlers}.py`
  — every WS-facing handler in the package.
- `rytm_randomizer/cockpit/export/{cli,writer,signing,serialize,verifier,model_format}.py`
  — the export pipeline (the other major operator-facing CLI flow).
- `rytm_randomizer/cockpit/__main__.py` — the sidecar entrypoint that
  spawns the FastAPI/uvicorn process.
- `docs/OBSERVABILITY.md` — the current operator-facing guide.
- `tests/architecture/test_observability.py` — the existing
  observability conformance suite (Rules 1-4 plus per-module
  `_EXPECTED_LOGGER_FILES` allow-list).

Greps run:

- `_logger = logging.getLogger` / `logger = logging.getLogger` /
  `get_logger(__name__)` — 17 file matches across the whole package,
  10 in the V1.34 runtime core, **4** in `cockpit/` (`device/real.py`,
  `device/mock.py`, `ws/wizard_handlers.py`, `profiles/registry.py`).
- `logger\.(debug|info|warning|error|exception)` — 29 call sites
  package-wide, **3 in the entire cockpit** (all in `wizard_handlers`).
- `print\(|sys\.stderr|sys\.stdout` in `cockpit/` — 2 files
  (`__main__.py` for the dev-mode token print, `export/cli.py` for the
  passive ack on stdout). Both are intentional operator UI, allow-listed
  by the arch test.
- Logger presence audited file-by-file across all 28 cockpit modules —
  see the gap-analysis table below.

---

## Current state inventory

### Logging infrastructure (`observability/logging.py`)

| Capability                                            | Status   |
|-------------------------------------------------------|----------|
| Named per-module loggers via `get_logger(__name__)`   | ✅ shipped |
| Structured human-readable formatter (`<ts> <level> <name> <op_id> <msg>`) | ✅ shipped |
| JSON-line formatter (`--log-json`)                    | ✅ shipped |
| `extra={...}` keys flow through to JSON               | ✅ shipped |
| Library-author NullHandler (import-time silence)      | ✅ shipped |
| Package-root logger isolation (`propagate=False`)     | ✅ shipped |
| Sampling / rate-limiting at hot paths                 | ❌ missing |
| Per-handler context binding (`logger.bind(...)`-style) | ❌ missing (stdlib `logging.LoggerAdapter` could provide it) |
| External shipper integration (Sentry / OTLP / loki)   | ❌ missing |

### Tracing infrastructure (`observability/tracing.py`)

| Capability                                            | Status   |
|-------------------------------------------------------|----------|
| `operation()` context manager with `op_id` + elapsed_ms | ✅ shipped |
| `@trace(...)` decorator equivalent                    | ✅ shipped |
| Context propagation via `contextvars` (re-entrant safe) | ✅ shipped |
| `_OpIdFilter` re-installs on `configure_logging` re-call | ✅ shipped |
| Per-operation `kwargs` captured as `extra={...}`      | ✅ shipped |
| Spans on V1.34 runtime core (`scene_run`, `pad{N}.*`, `mido.open_output`) | ✅ shipped |
| Spans on **any cockpit handler**                      | ❌ missing |
| Spans on the export pipeline (`pack` / `sign` / `atomic_write` / `verify`) | ❌ missing |
| `request_id` from WS envelope wired into `op_id`      | ❌ missing |
| OpenTelemetry / W3C TraceContext interop              | ❌ missing |

### Error taxonomy (`observability/errors.py`)

| Capability                                            | Status   |
|-------------------------------------------------------|----------|
| `RytmRandomizerError` base + 5 leaf families (`MidiError`, `StateError`, `DataError`, `BoundaryError`, `ConfigError`) | ✅ shipped |
| `context: Mapping` attached per-instance              | ✅ shipped |
| Re-homed legacy errors via multi-inheritance (idiomatic `except OSError` etc. still works) | ✅ shipped |
| `__str__` renders `[context: k=v, ...]` tail          | ✅ shipped |
| Stable error code / "fingerprint" (Sentry-style)      | ❌ missing — `type(exc).__name__` is the only aggregator today |
| Mapping from exception → log fields + metric increment | ❌ missing — every `except` block invents its own message |

### Metrics (`observability/metrics.py`)

| Capability                                            | Status   |
|-------------------------------------------------------|----------|
| `MidiMetrics` dataclass + singleton + `reset_metrics` for tests | ✅ shipped |
| `cc_sent_by_channel`, `cc_blocked_by_guardrail_by_pad`, `errors_by_kind` counters | ✅ shipped |
| `format_summary()` for shell-exit dump                | ✅ shipped |
| **Anywhere in the package that increments these counters today** | ❌ **0 call sites** |
| Per-WS-command counters (RED)                         | ❌ missing |
| Per-export-pipeline counters / timings                | ❌ missing |
| Histogram / percentile latency                        | ❌ missing |
| Prometheus / StatsD export                            | ❌ missing |

### Logger coverage map

Module logger present (✅ = `get_logger(__name__)` or
`logging.getLogger(__name__)`):

| File                                                  | Logger? | Call density |
|-------------------------------------------------------|---------|--------------|
| `app.py`                                              | ✅       | 2 calls (port_close best-effort, configure_logging breadcrumb) |
| `midi_io.py`                                          | ✅       | 1 (per-CC `midi_send` debug) |
| `mido_provider.py`                                    | ✅       | 2 |
| `scene_runner.py`                                     | ✅       | (operation-wrapped) |
| `group_runner.py`                                     | ✅       | (operation-wrapped) |
| `engines/pad{1,2,3,4}.py`                             | ✅       | (operation-wrapped via `@trace`) |
| `guardrails/{validation,resolver,store}.py`           | ✅       | 7 total |
| `cockpit/device/mock.py`                              | ✅       | 1 |
| `cockpit/device/real.py`                              | ✅       | 2 |
| `cockpit/profiles/registry.py`                        | ✅       | 7 |
| `cockpit/ws/wizard_handlers.py`                       | ✅       | 3 |
| `cockpit/ws/handlers.py`                              | ❌       | **0** |
| `cockpit/ws/server.py`                                | ❌       | **0** |
| `cockpit/ws/session.py`                               | ❌       | 0 |
| `cockpit/ws/wizard_session.py`                        | ❌       | 0 |
| `cockpit/__main__.py`                                 | ❌       | 0 |
| `cockpit/export/cli.py`                               | ❌       | **0** |
| `cockpit/export/writer.py`                            | ❌       | **0** |
| `cockpit/export/signing.py`                           | ❌       | 0 |
| `cockpit/export/serialize.py`                         | ❌       | 0 |
| `cockpit/export/verifier.py`                          | ❌       | 0 |
| `cockpit/export/model_format.py`                      | ❌       | 0 |
| `cockpit/engine/mutate.py`                            | ❌       | 0 |
| `cockpit/engine/send_plan.py`                         | ❌       | 0 |
| `cockpit/history/store.py`                            | ❌       | 0 |
| `cockpit/profiles/builtin.py`                         | ❌       | 0 |
| `cockpit/profiles/paths.py`                           | ❌       | 0 |
| `cockpit/wizard/{analyze,builder,state,path_policy,reference_analyzer,sysex_analyzer,trait_math,pad_mapping}.py` | ❌ | 0 each |

**Pure-data / pure-protocol modules** (don't need a logger):
`cockpit/data/*.py`, `cockpit/ws/protocol.py`, `cockpit/ws/wizard_protocol.py`,
`cockpit/device/adapter.py`, `cockpit/wizard/errors.py`,
`cockpit/wizard/traits.py`, `cockpit/engine/prng.py`. These are pure
types / TypedDicts / `xorshift32` / Protocol stubs with no executable
logic that would emit a log.

---

## Target state — "world-class" on a CLI + WS sidecar app

The aspirational shape, scoped honestly to a localhost-only Python
sidecar (we are not running 1000 RPS to justify OTLP):

1. **Structured JSON logs with correlation IDs.** Every log line emitted
   while handling a WS command carries the same `request_id` field, so
   `jq 'select(.request_id == "<uuid>")'` returns the full trace of one
   user interaction across handlers, the engine, the device adapter, and
   the history store.
2. **RED metrics per endpoint.**
   - **R**ate: `ws_command_total{command}` and `export_total`.
   - **E**rrors: `ws_command_errors{command,kind}` and
     `export_errors{kind}`.
   - **D**uration: `ws_command_duration_ms{command}` and
     `export_duration_ms` (histogram if budget allows, otherwise
     min/p50/p95/max from a small in-memory ring).
3. **Distributed-trace-friendly spans.** Every WS command runs inside an
   `operation(name=cmd_type, request_id=...)` span; the export CLI runs
   inside an `operation("cockpit_export_profile_model", profile_id=..., signed=...)`
   span with child spans for `pack`, `sign`, `atomic_write`, `verify`.
   No OTLP needed for the localhost case — the structured `op_id` is
   already trace-like.
4. **Alert-ready error categorization.** Every taxonomy exception carries
   a stable, short "fingerprint" string (e.g. `WriteError::disk_full`,
   `MidiError::port_open_failed`) usable as a metric label and groupable
   in a future Sentry tier. The existing `context` payload becomes the
   tag set for the span / Sentry breadcrumb.
5. **Log sampling at hot paths.** The V1.34 parity engines emit per-CC
   log lines that are useful at DEBUG but would flood at INFO. Add a
   tiny rate-limiting filter (drop ≥99% of identical-key INFO records
   within a 1s bucket) so a noisy hot path stays readable.
6. **No PII / no filesystem-path leakage.** Already enforced for the
   wizard error surface by PR 2/9 (`H4` categorical reason set —
   `path_not_found` / `unsupported_format` / `read_failed` /
   `analysis_failed`). Extend the same discipline to the export pipeline
   error path.

---

## Gap analysis

Per module — classification using the four-tier rubric (Black hole →
Unstructured → Has logger but no context → Structured + correlated):

| Path                                              | Status                  | Why it matters |
|---------------------------------------------------|-------------------------|----------------|
| `cockpit/ws/handlers.py` (the dispatcher)         | **Black hole**          | Top-of-funnel for every user action; **0** log emits today |
| `cockpit/ws/server.py` (auth + size cap + loop)   | **Black hole**          | Auth failures + size-cap rejections + disconnects are invisible — the user-visible reason for "the cockpit dropped me" is unknowable |
| `cockpit/export/cli.py`                           | **Black hole**          | The export pipeline is the only on-disk-write surface; every failure mode (FileExists, write fail, sign fail, verify fail) currently reaches the operator only as a printed `error:` line |
| `cockpit/export/writer.py`                        | **Black hole**          | Hides the durability story (tempfile path, fsync timing, atomic-rename outcome) — vital when a user reports "the file is corrupt" |
| `cockpit/history/store.py`                        | **Black hole**          | Snapshot append / undo / load — diagnosing a "wrong state on load" requires the chain mutations to leave breadcrumbs |
| `cockpit/profiles/registry.py`                    | Has logger + 7 calls    | OK but bare strings, no `extra={...}` payload — upgrade to structured + bind module |
| `cockpit/ws/wizard_handlers.py`                   | Has logger + 3 calls    | Best-in-class today (analyzer-failure categorical reason set); use as the **template** for handlers.py |
| `cockpit/device/{mock,real}.py`                   | Has logger + 1-2 calls  | Adequate; add operation-spans on `apply_send_plan` / `commit_kit` |
| `cockpit/engine/{mutate,send_plan}.py`            | **Black hole**          | The mutation algorithm itself; 0 visibility into why a candidate came out the way it did |
| `cockpit/wizard/{analyze,builder,...}.py`         | **Black hole**          | Wizard analysis pipeline; failures bubble up as `WizardSourcePathError` etc. without breadcrumbs to where they originated |

### Highest-leverage fixes (5-10, ranked by gap × traffic)

1. **WS command dispatcher (`ws/handlers.py`)** — every user interaction
   passes through `handle_command`; 0 log emits today; ack-with-error
   strings are never aggregated.
2. **WS server loop (`ws/server.py`)** — auth handshake, size-cap
   rejection, disconnects all silent.
3. **Export CLI (`export/cli.py`)** — operator-facing failure modes
   surface only on stdout; no structured trace.
4. **Atomic write (`export/writer.py`)** — the only persistence surface
   in the cockpit. Disk-full / permission-denied / cross-FS rename =
   total black hole.
5. **History store (`history/store.py`)** — snapshot chain mutations
   are the basis for every "load" and "undo"; debugging a wrong-state
   load is currently grep-impossible.
6. **Metrics adoption** — `observability/metrics.py` exists but has 0
   increment sites. Adopting RED counters at the dispatcher is one
   line per handler.
7. **Cockpit `__main__.py`** — port resolution, token provisioning,
   uvicorn boot. A wrong port / token-write failure is invisible
   beyond a stderr stack trace.
8. **Wizard analyze pipeline (`wizard/analyze.py` + `wizard/builder.py`)**
   — already has categorical reason set in `wizard_handlers.py`; push
   the breadcrumbs down into the analyzers themselves.
9. **Engine mutation (`engine/mutate.py` + `engine/send_plan.py`)** —
   the algorithmic core; spans + sampled debug help diagnose
   "why is this candidate so different from the last one".
10. **Profiles registry (`profiles/registry.py`)** — already has logging,
    upgrade unstructured `_logger.info("loaded N profiles")` → `extra={"profile_count": N, "profiles_dir": ...}`.

---

## Recommended PRs (priority-ordered)

Each PR is scoped to land in a single change set under ~500 LOC including
tests. Each is independently mergeable; PR O3 (logger binding) is a
prerequisite for PR O1's full effect but the two can land in either order.

### PR O1 — `request_id` propagation through cockpit WS handlers

Goal: every log line emitted while processing a WS command carries the
same `request_id` (the client's correlator) in the structured `extra`
payload. Operators correlating a "the cockpit hung when I hit SEND" bug
report can grep `select(.request_id == "<uuid>")` in JSON-mode logs.

Mechanism: wrap the handler call in `server.py` (not in `handlers.py`,
so the dispatcher stays pure) with an `operation()` span keyed on
`f"ws.{cmd_type}/{request_id}"`. Pass `request_id` as an `operation()`
kwarg so the existing `extra` payload picks it up automatically. The
`op_id` field on every log line becomes `ws.send/<uuid>` etc. for the
duration of the handler call.

Scoping: ~30 LOC in `server.py`; 0 changes to `handlers.py`; 2-3 new
tests in `tests/cockpit/test_ws_observability.py` (currently
non-existent) asserting the `op_id` shows up on a synthetic log record
captured during a fixture handler call.

### PR O2 — RED metrics for WS commands + the export pipeline

Goal: per-command rate / error / duration metrics so the operator can
ask "which command is slowest?" and "which command fails most?".

Mechanism: extend `MidiMetrics` (or fork a sibling `CockpitMetrics`
class — taxonomy decision: keep one singleton OR carve `cockpit` out as
its own surface) with:

- `ws_command_total: Counter[str]` keyed by command type.
- `ws_command_errors: Counter[tuple[str, str]]` keyed by (command type,
  exception fingerprint).
- `ws_command_duration_ms: dict[str, list[float]]` (small ring buffer
  per command — last 100 samples).
- `export_total: Counter[bool]` keyed by `signed`.
- `export_errors: Counter[str]` keyed by exception fingerprint.

Increment sites: one in `handle_command` (around the dispatch); one in
`handle_export_profile_model` (around the pipeline). Wire `metrics.py`'s
`format_summary()` to render the new counters with stable ordering for
diffable test snapshots.

Scoping: ~150 LOC; 2-3 unit tests + 1 integration test under
`tests/cockpit/test_metrics_adoption.py`.

### PR O3 — bind `_logger = get_logger(__name__)` in every cockpit module

Goal: zero-cost provisioning of named loggers everywhere so any future
log call (from any PR including the four above) lands in the structured
stream.

Mechanism: one-liner import + module-level `_logger` in 24 cockpit
modules. **This PR is partially landed by Phase 5 of this review** (see
below) — the highest-traffic modules get loggers immediately as
low-hanging fruit.

Scoping: ~50 LOC across ~12 hot-path modules in Phase 5; remaining
~10 modules deferred to PR O3 proper for the wizard internals + engine
core.

### PR O4 — error-taxonomy → log-event mapping with fingerprinting

Goal: every taxonomy exception has a stable, short "fingerprint"
(`"WriteError::disk_full"`, `"MidiError::port_busy"`,
`"DataError::profile_corrupt"`) usable as a metric label, in a Sentry
breadcrumb, and as the dedup key in any future alerting tier.

Mechanism: add a `fingerprint: ClassVar[str] | None = None` class
attribute on every taxonomy class + a `fingerprint(exc)` helper that
returns either the class attribute or a derived
`f"{type(exc).__name__}::{root_cause_type}"` fallback. Wire
`fingerprint` into the existing `operation_error` log event in
`tracing.py` (`extra={"fingerprint": ..., "exc_type": ...}`).

Scoping: ~100 LOC + per-exception fingerprint table; arch test in
`tests/architecture/test_observability.py` to enforce every taxonomy
member declares a `fingerprint`.

### PR O5 (optional) — OpenTelemetry shim

Only if the project wants distributed traces alongside the structured
`op_id`. Add an `observability/otel.py` module gated behind an
`opentelemetry-api`/`opentelemetry-sdk` optional dependency, wire the
existing `operation()` context manager to also start an OTel span when
the optional dep is present. Zero impact when the dep is absent. ~200
LOC + a smoke test.

Defer unless: the team starts shipping cockpit traces to a Tempo /
Jaeger backend. The structured `op_id` already covers 80% of the
"correlate records from one operation" need without the OTel
runtime dependency.

### PR O6 — architecture tests for observability invariants

Goal: regression-proof the new shape so future PRs don't slip back
into the black-hole tier.

New tests under `tests/architecture/test_observability.py`:

1. `test_every_ws_handler_runs_inside_an_operation_span` — AST scan
   the handler dispatcher to assert it's wrapped in `operation(...)`.
2. `test_every_taxonomy_class_declares_a_fingerprint` — enforce PR
   O4's contract.
3. `test_no_unstructured_logger_calls_in_hot_paths` — every
   `logger.info(msg)` in `cockpit/ws/handlers.py`,
   `cockpit/ws/server.py`, `cockpit/export/cli.py`,
   `cockpit/export/writer.py` must include an `extra={...}` payload.
4. `test_request_id_propagates_to_log_records` — fixture-driven
   integration test that handles one synthetic WS command, captures
   the log records via `caplog`, and asserts every record carries
   the expected `request_id`.
5. Expand `_EXPECTED_LOGGER_FILES` to include the cockpit hot-path
   set so accidental logger removal is caught.

Scoping: ~200 LOC of pure tests.

---

## Architecture test recommendations (OBS6)

Concrete additions to `tests/architecture/test_observability.py`:

```python
# Add to _EXPECTED_LOGGER_FILES (PR O3 then drop entries that prove out):
_EXPECTED_LOGGER_FILES_COCKPIT_ADDITIONS = frozenset({
    "rytm_randomizer/cockpit/ws/handlers.py",
    "rytm_randomizer/cockpit/ws/server.py",
    "rytm_randomizer/cockpit/ws/session.py",
    "rytm_randomizer/cockpit/__main__.py",
    "rytm_randomizer/cockpit/export/cli.py",
    "rytm_randomizer/cockpit/export/writer.py",
    "rytm_randomizer/cockpit/history/store.py",
    "rytm_randomizer/cockpit/engine/mutate.py",
    "rytm_randomizer/cockpit/engine/send_plan.py",
    "rytm_randomizer/cockpit/wizard/analyze.py",
    "rytm_randomizer/cockpit/wizard/builder.py",
})
```

The Phase 5 instrumentation in this PR adds the loggers to **most** of
the entries above, so the arch test can be tightened immediately
(`_EXPECTED_LOGGER_FILES` extension) without churning the architecture
gate ahead of the per-module work.

Future tests to add when each PR lands:

- **PR O1 lands** → `test_ws_handler_span_carries_request_id`
- **PR O2 lands** → `test_ws_command_metric_incremented_once_per_dispatch`
- **PR O4 lands** → `test_every_taxonomy_class_declares_fingerprint`
- **PR O6 itself** → `test_hot_path_logger_calls_carry_extra_payload`
  (AST scan: `logger.info(...)` with a single string positional arg
  and no `extra=...` keyword is a violation in the hot-path file set).

---

## Appendix — quick wins this PR ships (Phase 5)

The Phase 5 instrumentation in this PR is the **minimum-viable
foundation** for PRs O1-O6: it binds `_logger = get_logger(__name__)` at
module top-level in every cockpit module that does executable work. This
is a one-line-per-file change with zero behaviour impact (the logger is
defined but never called yet) and unblocks every subsequent PR from
having to do the binding work as a prelude.

Files touched in Phase 5 (12 modules):

- `rytm_randomizer/cockpit/ws/handlers.py`
- `rytm_randomizer/cockpit/ws/server.py`
- `rytm_randomizer/cockpit/ws/session.py`
- `rytm_randomizer/cockpit/__main__.py`
- `rytm_randomizer/cockpit/export/cli.py`
- `rytm_randomizer/cockpit/export/writer.py`
- `rytm_randomizer/cockpit/export/signing.py`
- `rytm_randomizer/cockpit/export/verifier.py`
- `rytm_randomizer/cockpit/history/store.py`
- `rytm_randomizer/cockpit/engine/mutate.py`
- `rytm_randomizer/cockpit/engine/send_plan.py`
- `rytm_randomizer/cockpit/wizard/analyze.py`
- `rytm_randomizer/cockpit/wizard/builder.py`

Files **NOT** touched (pure data / protocol shells; no logic, no logger
needed):

- `rytm_randomizer/cockpit/data/*.py` — frozen dataclasses + TypedDicts
- `rytm_randomizer/cockpit/ws/protocol.py` /
  `rytm_randomizer/cockpit/ws/wizard_protocol.py` — TypedDict + constant
  declarations
- `rytm_randomizer/cockpit/device/adapter.py` — `Protocol` only
- `rytm_randomizer/cockpit/wizard/errors.py` /
  `rytm_randomizer/cockpit/wizard/traits.py` — exception classes /
  trait constants
- `rytm_randomizer/cockpit/engine/prng.py` — pure `xorshift32` function
- `rytm_randomizer/cockpit/profiles/{builtin,paths}.py` — constants /
  path helpers (low-value but eligible if PR O3 wants to be exhaustive)
- `rytm_randomizer/cockpit/wizard/{state,path_policy,reference_analyzer,
  sysex_analyzer,trait_math,pad_mapping,traits}.py` — deferred to PR O3
  proper alongside per-module call-site work
