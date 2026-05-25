# RytmRandomizer Code Review
*Date: 2026-05-25*
*Reviewer: Staff Engineer (Adversarial Read)*

## TL;DR

The codebase is unusually disciplined for its size — 225 modules, 237 test files, an enforced 18-gate plan-requirements regime, and a real architecture-test suite that pins the wire format of the Phase 3 export. The Phase 1–3 cockpit subpackage is the strongest code in the tree: pure functions where possible, frozen dataclasses everywhere, a stdlib-only HMAC signing envelope with timing-safe compare, atomic writes with `os.replace` + `fsync`, and a verifier that returns categorized results without raising. The biggest risks are concentrated in **three places**: (1) the cockpit WebSocket sidecar has no authentication, no origin check, and no CSRF/handshake token — anything on `localhost` can drive it, including DNS-rebinding attacks via a browser tab; (2) the wizard's file-path inputs (`location`) are fed straight to `Path.read_bytes()` / `iterdir()` over the WebSocket with no canonicalisation, allowing a hostile WS peer to enumerate or fingerprint any file the sidecar user can read; (3) the cockpit-export CLI ships a 60-line fallback re-implementation of `atomic_write` that has subtly different error taxonomy and now duplicates the very surface WS-B (`writer.py`) merged — dead code that masquerades as live. Beyond those: the package has structural maintainability debt (a 4,759-line `reports/style_performance_arcs.py`, a 3,394-line `help_text.py`, 41 `live_gui_*` report files most of which exceed 800 lines), and the `cli.py` dispatcher is a 213-arm `if args == [...]` ladder that the team has already started to retire via `cli_registry` but has not finished.

The mutation engine, the parity-fixture discipline, the signing envelope, the verifier, and the architecture-test suite are excellent and worth preserving line-for-line.

**Verdict: ship-quality for Phase 3 as an offline export pipeline. Not ship-quality as a multi-user or browser-reachable sidecar. The WS layer is the next thing that has to grow up before Phase 4.**

## Methodology

What I actually read (full):

- `README.md`, `pyproject.toml`, `docs/ARCHITECTURE.md`, `docs/PLAN_REQUIREMENTS.md`
- All of `rytm_randomizer/cockpit/export/` (`signing.py`, `verifier.py`, `writer.py`, `cli.py`, `serialize.py`, `model_format.py`, `__init__.py`)
- All of `rytm_randomizer/cockpit/engine/` (`mutate.py`, `send_plan.py`)
- All of `rytm_randomizer/cockpit/wizard/` core (`state.py`, `builder.py`, `analyze.py`, `sysex_analyzer.py`, `reference_analyzer.py`)
- `rytm_randomizer/cockpit/ws/` (`server.py`, `handlers.py`, `wizard_handlers.py`, `session.py`, partial `protocol.py`)
- `rytm_randomizer/cockpit/__main__.py`, `rytm_randomizer/cockpit/profiles/registry.py`
- `rytm_randomizer/app.py`, `rytm_randomizer/cli.py` (skimmed — 913 lines), `rytm_randomizer/cli_registry.py`
- `rytm_randomizer/observability/errors.py`
- `tests/architecture/test_export_pipeline_invariants.py`, `tests/architecture/test_no_any_escape_hatches.py`
- Directory listings + size histograms of `rytm_randomizer/` and `tests/`

What I sampled, not exhaustively:

- `rytm_randomizer/cockpit/data/profile_model.py` (round-trip + invariants)
- `rytm_randomizer/reports/cockpit_export_rehearsal.py` (first 150 of 1172 lines)
- `rytm_randomizer/cli.py` (head + middle + tail)

What I skipped and why:

- The 685 V1.34 parity JSON fixtures and the engines they pin. The parity contract is byte-frozen by `tests/_parity_worker.py`; auditing them isn't useful without hardware. I trust the gate.
- All `desktop/` TypeScript. Out of scope for this Python-side staff review; I looked only at the WS contract from the Python side.
- 41 `reports/live_gui_*.py` files past their first ~150 lines. They are auto-generated-looking declarative report builders following one pattern; I sampled `cockpit_export_rehearsal.py` to confirm the pattern and treated the rest as "follows the same shape, same maintainability concern."
- The 4,759-line `reports/style_performance_arcs.py`. Read its presence as a *finding*, not its body — see the maintainability section.

## Findings by Severity

### CRITICAL (data corruption, security, broken invariants)

#### C1 — Cockpit WebSocket sidecar has no authentication, no origin check, no handshake token
**File:** `rytm_randomizer/cockpit/ws/server.py:75-99`, `rytm_randomizer/cockpit/__main__.py:103-108`

`create_app` registers `@app.websocket("/ws")` with `await websocket.accept()` as the entire handshake. There is no `Origin:` header check, no shared-secret bearer token, no first-message authentication frame, and no CSRF cookie. The server binds to `127.0.0.1:4317` — but **any browser tab on the user's machine can open a WebSocket to `ws://localhost:4317/ws`**. Same-origin policy does not protect WebSockets: a malicious page can issue `new WebSocket("ws://localhost:4317/ws")` and drive every command including `send` (when `--arm`), `wizard_save` (writes JSON to disk), and `export_profile_model` (returns base64-encoded `ProfileModel` bytes to the page).

This is the classic localhost-sidecar exposure pattern. The mitigation in `__main__.py:32-33` is a docstring saying "Loopback only — never expose the cockpit to a routable interface in Phase 1." That is a comment, not a check. DNS rebinding can also reach `127.0.0.1`. **The default install ships an unauthenticated remote-control surface for the user's MIDI hardware.**

The README claims "Passive by default — nothing touches MIDI unless you explicitly `--arm`." That is true of the Python CLI but **not** of the sidecar, which routes through `DeviceAdapter` and will drive a real port the moment `--arm` is wired in.

**Fix.** Two options, in increasing rigour:
1. Require the Tauri shell to inject a per-launch random token into the sidecar env (`RYTM_RAND_WS_TOKEN`), require the first WS frame to be `{type: "hello", token: ...}` with `hmac.compare_digest`, and refuse all other commands until the handshake succeeds.
2. Bind to a Unix domain socket on POSIX / a named pipe on Windows instead of TCP loopback. This is what most modern sidecar designs do (e.g. Vite HMR over UDS on macOS). FastAPI/Uvicorn supports `uds=` natively.

Either fix is < 100 LOC and must land before any `--arm` integration of the cockpit ships.

---

#### C2 — Wizard `location` strings are passed to `Path.read_bytes()` / `Path.iterdir()` without canonicalisation
**Files:** `rytm_randomizer/cockpit/ws/wizard_handlers.py:172-187` → `rytm_randomizer/cockpit/wizard/analyze.py:122-129` → `rytm_randomizer/cockpit/wizard/sysex_analyzer.py:55-100` (and `analyze.py:149-165`)

`_handle_wizard_add_source` reads `location = str(cmd.get("location", ""))` straight off the wire and stores it in the wizard state. On `wizard_analyze`, the dispatcher routes to either `extract_kit_traits(Path(source.location))` or `_analyze_audio_path(Path(source.location))`. Both call `path.read_bytes()` / `path.iterdir()` with **no path canonicalisation, no allow-list root, no symlink resolution, no enforcement that the path is within an operator-blessed directory**.

Combined with C1 above, this means: any browser tab can ask the cockpit "please read `/etc/passwd` for me as a SysEx kit." `extract_kit_traits` will happily read the file and compute byte statistics on it. The traits then come back on the wire encoded as four floats — that's a fingerprinting / oracle vector for files the page has no business touching. The audio path will throw `extract_from_audio` errors that leak the path back to the caller via the `error` field on the `AnalysisJob` (`wizard_handlers.py:251-256` — `error=str(exc)`).

Even *without* C1, a hostile `.rymp` file or a malicious WS client could enumerate the entire filesystem the cockpit user has read access to.

**Fix.** Validate every `location` against:
1. A configured allow-list root (e.g. `~/.rytm-randomizer/wizard-sources/` plus user-blessed roots in a config file).
2. `Path(location).resolve()` must `is_relative_to(root)` (Python 3.9+).
3. Reject symlinks (`p.is_symlink()`) at validation time.
4. Sanitize errors so the message does not echo the input path back over the wire.

This is on the order of a 30-line `_validate_source_path()` helper + tests.

---

#### C3 — Export CLI ships a 60-LOC fallback re-implementation of `atomic_write` that has now diverged from `writer.py`
**File:** `rytm_randomizer/cockpit/export/cli.py:57-122`

The CLI carries a `try/except ImportError` block that re-implements `atomic_write`, `WriteResult`, and `default_export_dir` inline. The comment on line 57 says: *"WS-B fallback: remove at integration time once WS-B merges its writer."* WS-B has merged — `writer.py` exists, is fully tested, and ships its own canonical surface. The fallback is **dead code that runs only if `writer.py` is missing**, which now means "never in a shipping build." But it is not dead-dead: the fallback's behaviour disagrees with `writer.py` on three observable points:

| Behaviour | `writer.py` | CLI fallback |
|---|---|---|
| Overwrite refusal | raises `FileExistsError` (line 196) | raises `ValueError` (line 102) |
| OSError wrap | raises `WriteError` subclass of `DataError + OSError` (line 221) | re-raises raw `OSError` (line 116) |
| Default dir | `~/.config/rytm-randomizer/exports` on POSIX, `%APPDATA%/...` on Windows (line 127-134) | `~/.rytm-randomizer/exports` everywhere (line 85) |

The handler at `cli.py:405` catches `(ValueError, TypeError, OSError)` so both raise paths are swallowed — but the *exit message strings* differ ("refusing to overwrite ..." vs. "atomic_write failed for ..."), which means the operator's ack JSON changes shape depending on whether WS-B's import succeeded. This is the exact silent-divergence pattern Gate 17 (abstraction reuse) was lifted to prevent.

**Fix.** Delete lines 57-122. Replace with the hard import:

```python
from .writer import WriteResult, atomic_write, default_export_dir
```

If `writer.py` is missing the import error should fail loudly at module load, not silently switch behaviour. This is a < 80-LOC removal.

---

#### C4 — `_handle_wizard_set_metadata` cannot clear `name` or `description` via the wire
**Files:** `rytm_randomizer/cockpit/ws/wizard_handlers.py:141-156`, `rytm_randomizer/cockpit/wizard/state.py:240-260`

`with_metadata`'s contract is documented (state.py:248-252): pass `None` → "leave unchanged," pass `""` → "clear." But the WS handler does:

```python
name_raw = cmd.get("name")           # missing OR explicit JSON null both → None
description_raw = cmd.get("description")
name = None if name_raw is None else str(name_raw)
```

So a client that sends `{name: null}` to clear the name gets "leave unchanged" semantics — the documented contract is inverted at the wire. The wizard UI today probably always sends a string (so the bug is latent), but anyone reading the wire spec and writing a second client will hit this. Worse, there is no way over the wire to express "clear" — `""` from the UI side would have to be sent literally, and the empty-string-means-cleared convention only exists inside `with_metadata`'s docstring, not the WS protocol's TypedDict.

**Fix.** Pick one wire semantics, document it on the command's TypedDict in `wizard_protocol.py`, and enforce it in the handler. The cleanest shape is: `name` missing from the command body → leave unchanged; `name: null` → clear; `name: "<str>"` → set. This requires distinguishing missing from `None` in the handler (use a sentinel or check `"name" in cmd`).

---

### HIGH (correctness, hard-to-debug bugs, architectural drift)

#### H1 — `handle_command` smuggles events through a private attribute on `CockpitSession`, with type-ignore comments
**File:** `rytm_randomizer/cockpit/ws/handlers.py:533-563`

```python
session._pending_events = list(result.events)  # type: ignore[attr-defined]
...
pending = getattr(session, "_pending_events", None)
...
session._pending_events = []  # type: ignore[attr-defined]
```

The 32-line block of comments above explains why ("ack first then events, can't await before returning, so stash the events on the session and drain after"). The reasoning is sound; the implementation is not. The session dataclass has no `_pending_events` field. Both writes use `# type: ignore[attr-defined]` to suppress the obvious mypy/pyright complaint. This is a side-channel: a future contributor who adds a real field with that name overrides it without warning; concurrent connections (when multi-tenant lands) clobber each other's pending events; tests that inject a fake session must remember to add the attribute manually.

This is exactly the duck-typed boundary leakage the codebase claims to ban (Gate 6, `test_no_any_escape_hatches.py`). It evades the check because `_pending_events` is `list[dict]` not bare `Any`, but the spirit of the rule is identical.

**Fix.** Make `_pending_events: list[dict] = field(default_factory=list)` a proper field on `CockpitSession`, then delete every `type: ignore` here. ~10 LOC.

---

#### H2 — Wizard `_handle_wizard_add_source` lies in its type signature
**File:** `rytm_randomizer/cockpit/ws/wizard_handlers.py:178-187`

```python
source = InspirationSource(
    source_id=source_id,
    kind=kind,  # type: ignore[arg-type]
    mode=mode,  # type: ignore[arg-type]
    location=location,
    display_name=display_name,
    added_at=datetime.now(timezone.utc),
)
```

`kind` and `mode` are typed as `Literal[...]` on `InspirationSource`, but the handler passes raw `str` from the wire with a `# type: ignore[arg-type]`. The `__post_init__` does validate the value at runtime — but the type-ignore tells the type checker "trust me, this string is one of the literals" when in fact it might not be. The right idiom is to call a `_parse_kind(s: str) -> Kind` helper that does the `in KIND_VALUES` check and either returns the narrowed type or raises. The `Literal` is then earned, not asserted.

This is a recurring pattern in `from_dict` constructors throughout `cockpit/data/` (e.g. `profile_model.py:159` `kind=str(data["kind"])  # type: ignore[arg-type]`). Same fix applies everywhere: a `_narrow_kind` helper.

---

#### H3 — `verify_signed_blob` short-circuits the inner CRC check when `key=None`
**File:** `rytm_randomizer/cockpit/export/verifier.py:126-154`

When no key is provided, the verifier still walks the inner payload's magic / format-version / CRC. That part is fine. But step 3 (`if key is not None`) is the only thing protecting against payload tampering. So calling `verify_signed_blob(data, key=None)` on a signed envelope whose **payload** was swapped — but whose **CRC was correctly recomputed for the swap** — returns `ok=True, reason="unsigned_payload"`. That is technically what the docstring says ("everything we *could* verify is fine, but you didn't ask us to verify the signature"), but the wire format carries a signature explicitly to prevent CRC-only attacks. A receiver that ignores the signature is observing a CRC, which only protects against accidental corruption, not deliberate substitution.

This is not necessarily a bug — the docstring does warn — but the "unsigned_payload" branch is **the only thing the CLI's read-back integrity check uses when `--unsigned` is set** (`cli.py:259`). The post-write verification on an unsigned export therefore only proves CRC, not provenance, and the operator-facing ack `ok=True` doesn't distinguish "CRC clean, signed correctly" from "CRC clean, no signature provided."

**Fix.** Either: (a) make `verify_signed_blob` refuse to silently ignore the signature when the envelope carries one — require the caller to call `verify_unsigned_payload(blob.payload)` if they truly want to skip signature verification, or (b) bubble the `signed_envelope_present: bool` field into `VerificationResult` so the caller can spot the discrepancy. Today the result has no way to say "I parsed a signed envelope but ignored the signature."

---

#### H4 — The wizard analyzer surfaces analyzer exception messages straight back over the wire
**File:** `rytm_randomizer/cockpit/ws/wizard_handlers.py:247-256`

```python
except _ANALYZER_FAILURE_EXCEPTIONS as exc:
    terminal_job = AnalysisJob(
        ...,
        error=str(exc),
        ...,
    )
```

`extract_from_audio` and the SysEx analyzer both produce exception messages containing the full input path (e.g. `"audio path does not exist: C:\Users\Edward.Rosado\Documents\private\..."`). The terminal job is broadcast as `analysis_progress` to every connected client. Given C1 and C2 above, this is an information-disclosure path: a hostile WS peer asks for analysis of `/etc/passwd`, gets "audio path is neither a file nor a directory: /etc/passwd" back — confirmation the file exists and is not a directory.

**Fix.** Sanitize. Map analyzer exceptions to a fixed set of categorical reasons (`"path_not_found"`, `"unsupported_format"`, `"read_failed"`) and never echo the path. Log the full detail server-side via `observability/logging.py`.

---

#### H5 — `_round_half_away_from_zero` mis-handles `value == -0.0`
**File:** `rytm_randomizer/cockpit/engine/mutate.py:231-243`

```python
if value >= 0.0:
    return int(value + 0.5)
return -int(-value + 0.5)
```

`-0.0 >= 0.0` is `True` in Python, so `-0.0` takes the first branch. `int(-0.0 + 0.5)` is `0`. That's correct for `-0.0`. The latent risk is `value == -0.5` exactly: takes the negative branch, returns `-int(0.5 + 0.5) = -1`. C's `round(-0.5)` returns `-1.0` too, so the comment "matches C" holds. So actually correct — but this is a function the *whole Phase 4 firmware port stands on*. The spec file (`engine/spec.md`) needs to call out `-0.0` explicitly with a worked example. Without that, a C-port author writing `if (value >= 0.0)` is fine but a Rust port author writing `if value.is_sign_positive()` is **not** (Rust's `f64::is_sign_positive` returns `false` for `-0.0`). The 32-bit PRNG normalization at `mutate.py:67` produces values in `[0.0, 1.0)` so `r - 0.5` is in `[-0.5, 0.5)` — `-0.5` is reachable. Add a test fixture.

This is borderline LOW but escalated because Phase 4 will port this to a language not yet chosen.

---

#### H6 — The "passive" `cockpit-export-rehearsal-report` actually packs the profile
**File:** `rytm_randomizer/reports/cockpit_export_rehearsal.py:38-39`

The module docstring claims (line 18-23): *"never invokes the signer/verifier or writer modules, never instantiates a real export CLI. It only *reads* the ``ProfileRegistry`` plus ``pack_profile_model`` to compute what *would* be emitted."*

But it imports `from ..cockpit.export import FORMAT_VERSION, pack_profile_model`. **`pack_profile_model` is not a passive read — it MessagePack-encodes the entire profile and computes a CRC32.** That's compute, not I/O, and it has no side effects, so the claim "passive" is true in the no-disk-no-network sense. But the word "passive" elsewhere in the codebase means "imports nothing that touches MIDI." Here it's being used for two different things at once: "no I/O" *and* "no irreversible action." The docstring quietly conflates them.

More concretely: the `_SIGNED_ENVELOPE_OVERHEAD_BYTES = 256` constant (line 61) is described as a code-reviewed estimate of the signing envelope overhead. The actual signing envelope size is computable exactly from `signing.py` (4 + 2 + 1 + len("hmac-sha256") + 1 + len(key_id) + 1 + 32 + 4). Hard-coding 256 is wrong by anywhere from 0 to ~190 bytes depending on `key_id` length — the rehearsal-surface JSON says "this is the file you'd write" but reports a size that's off by a measurable amount when the actual writer runs. Pre-Phase-4, that's a Gate-18 doc-freshness drift waiting to happen.

**Fix.** Either delete `_SIGNED_ENVELOPE_OVERHEAD_BYTES` and import `signing.pack_signed` for a real-bytes calculation (which then makes the report's "doesn't invoke the signer" claim false — fine, update the claim), or document the constant's exact upper bound and assert it in `test_export_pipeline_invariants.py`.

---

#### H7 — `cli.py` `main()` is a 213-arm `if/elif` ladder with a half-finished extraction
**File:** `rytm_randomizer/cli.py:698-909`

The CLI has 5 layers of dispatch jammed together:
1. Inline `if args == ["--help"]` arms (lines 702-708).
2. The `_registered_command_exit_code(args)` registry lookup (line 710) — the right pattern.
3. Inline `if args == ["report"]` etc. — ~30 hand-written arms (lines 714-906).
4. Two-element `if len(args) == 2 and args[0] == "..."` arms.
5. The hard-coded `lazy_commands` dict inside `_registered_command_exit_code` (lines 14-700 — yes, ~686 lines of literal `(module_name, attribute_name)` tuples).

The team has correctly identified the problem (`cli_registry.py` is the seam) and started the refactor, but **stopped halfway**. The result is the worst-of-three-worlds: a partial registry that the dispatcher *manually* enumerates against, layered under the literal-equality ladder. The registry was supposed to obviate both.

Operationally: adding a new CLI command today means choosing one of (a) `_COMMANDS.register(...)` + the lazy-tuple registry list, (b) an `if args == [...]` arm, (c) both. The path of least resistance is (b). The architectural goal (Gate 17, abstraction reuse) is to make (a) the only path. That fix is real work — probably the largest single follow-up PR in this list.

---

#### H8 — `RealMidiSender.send_messages` cannot be unit-tested without `mido` because of `_rehome`'s lazy module import
**File:** `rytm_randomizer/observability/errors.py:141-188`

The `_rehome` mechanism is clever — it preserves class identity by leaving the original class in its module and re-importing on first attribute access. But it imports `rytm_randomizer.real_midi_adapter`, which in some build environments lazily checks `mido` (or its absence) and emits a warning. The architecture test sweep already had to add carve-outs for this exact pattern (`pyproject.toml:228`). A simpler design: define the new bases (`MidiError`, `DataError`, …) in this module and let the original modules inherit from them at class definition. That's the "documentation for future maintainers" the file already says is the design intent, but the runtime mechanism is `importlib.import_module`, not declarative.

This is a HIGH not a CRITICAL only because the architecture test catches the import-direction violations explicitly.

---

### MEDIUM (cleanliness, naming, error handling, type hints)

#### M1 — `Mapping[str, object]` in 11 `from_dict` constructors is Gate 6's anti-pattern in `object` clothing
**Files:** `rytm_randomizer/cockpit/data/*.py`, `rytm_randomizer/cockpit/wizard/state.py`

Gate 6 says: *"Every new record-shaped value is a `@dataclass(frozen=True)` or `TypedDict`. No new `Mapping[str, Any]` DTOs at module boundaries."* The codebase has dutifully avoided `Mapping[str, Any]` — but uses `Mapping[str, object]` in every `from_dict` signature. `object` is `Any` with a hat on. Callers must `str(data["x"])` to widen back, then `# type: ignore[arg-type]` to narrow to `Literal`. The TypedDicts in `protocol.py` exist for exactly this — `from_dict` should consume the matching TypedDict.

This is consistent across `profile_model.py`, `mutation_candidate.py`, `history.py`, `send_plan.py`, `snapshot.py`, `state.py`. Single fix pattern, many files.

---

#### M2 — Wizard `description` parameter accepted-and-discarded with `del`
**File:** `rytm_randomizer/cockpit/wizard/builder.py:151`

```python
del description  # accepted for API symmetry; no ProfileModel field today.
```

This is a smell. `description` exists on `WizardState` but not on `ProfileModel`. The handler unpacks it, hands it down, the builder throws it away. Either the field belongs on `ProfileModel` (looks like it should — the README and product copy talk about user profiles with descriptions), or the builder's signature should not accept it. Today it's the worst of both: a parameter the caller has to supply that does nothing.

---

#### M3 — `reference_analyzer` matching rule doesn't match its own docstring
**File:** `rytm_randomizer/cockpit/wizard/reference_analyzer.py:18-23`, `:115-118`

Docstring: *"Prefix-matched against the lookup keys: ``"birmingham techno"`` matches the ``"birmingham"`` entry because the entry's text starts the user's text"*

Code: `if needle.startswith(key)` (line 116). So `needle="birmingham techno"` and `key="birmingham"` does match. ✓. The docstring sentence is awkwardly phrased — "the entry's text starts the user's text" is correct, but the natural reading "the entry's text *is a prefix of* the user's text" inverts what `startswith` does at first glance. Either rewrite for clarity ("the user's text begins with the lookup key") or invert to `key.startswith(needle)` if the docstring's first read is the intent. Pick one.

---

#### M4 — `pack_profile_model` allows `format_version` kwarg that violates the file's own constraints
**File:** `rytm_randomizer/cockpit/export/serialize.py:29-63`

The function accepts `format_version: int = 1`, presumably so tests can pass `2` to exercise rejection. But `build_header` only validates the field width (≤ uint16), not membership in `SUPPORTED_FORMAT_VERSIONS`. So `pack_profile_model(p, format_version=999)` produces a blob that `unpack_profile_model` will immediately reject. Test-only seam in production code, with no `# pragma: no cover` or `_for_testing` suffix. Either restrict to `Literal[1]`, or rename to `_pack_with_version_override` and put it behind an underscore.

---

#### M5 — `sysex_analyzer._traits_from_bytes` derives "metallic_tension" from byte mean
**File:** `rytm_randomizer/cockpit/wizard/sysex_analyzer.py:103-134`

The function maps four byte statistics onto four "musical" trait names. The byte mean of a SysEx kit dump has *zero* musical meaning — it's a function of the encoding, the kit-record format, and the presence of name strings vs. sample data. Calling that "metallic_tension" gives the operator a number that looks meaningful and is not.

The docstring acknowledges this (line 10-12: *"Phase 3+ will parse the kit envelope properly … For Phase 2 this module ships a deterministic byte-statistics analyzer"*) but the variable names lie about the analysis. The wizard's "review" step will show a "metallic_tension" bar that has no relationship to metallic tension. **The user experience is a fake.**

Suggested rename until the real parser lands: emit traits named `_bytes_mean`, `_bytes_stddev`, `_bytes_density`, `_bytes_distinct` with a docstring banner saying "phase-2 placeholder, not musically meaningful." Or, make the kit path fail loudly with "kit analysis is not yet implemented" until Phase 3+ lands. The current shape is the worst option.

---

#### M6 — `ProfileRegistry._safe_load_profile` masks every error class under one log line
**File:** `rytm_randomizer/cockpit/profiles/registry.py:163-200`

The function catches `(OSError, json.JSONDecodeError)` then later catches `(KeyError, TypeError, ValueError)` and treats each as "skip with warning." That's intentionally tolerant of bad files. But a permission-denied `OSError` on a user-owned profile directory presents identically to a malformed JSON: both produce a warning, both yield an empty registry, neither prevents the cockpit from booting silently with no user profiles. That's confusing in production. Distinguish `PermissionError` (loud, refuse to start) from genuine "this one file is malformed" (warn, skip).

---

#### M7 — `_handle_wizard_save` silently overwrites existing profile files
**File:** `rytm_randomizer/cockpit/profiles/registry.py:101-123`

`save` does `target.write_text(...)` with no `exist_ok=False` check. Saving a wizard with a duplicated `profile_id` (which is a fresh ULID, so collision is astronomically unlikely — but `wizard_save` can be retried for any reason) silently overwrites the prior file. Given that `save` is the **only** persistence path for user content the operator has spent minutes building, this should be an atomic write (it isn't — `write_text` is not atomic on POSIX or Windows) and refuse to overwrite without an explicit flag.

The export pipeline learned this lesson and shipped `atomic_write` + `overwrite=False` default. The save path didn't get the same hardening.

**Fix.** Make `ProfileRegistry.save` go through `cockpit.export.writer.atomic_write(target, encoded, overwrite=False)`. Add a separate `save(profile, overwrite=True)` only if a real product need surfaces.

---

#### M8 — Constants named like enums but typed as bare `str`
**File:** `rytm_randomizer/cockpit/engine/mutate.py:76-90`, `rytm_randomizer/cockpit/engine/send_plan.py`

```python
def _classify_safety(depth: float) -> str:
    ...
    return "safe"
```

Return type is `str`. The caller (`mutate.py:217`) passes this into `MutationCandidate(safety_status=safety_status,  # type: ignore[arg-type] ...)` — same Literal narrowing pattern as H2. Make `_classify_safety` return `Status` (the Literal alias from `cockpit/data/types.py`), drop the `type: ignore`. Same in `send_plan.py:41` `readiness_reason: ReadinessReason = "ready" if ready else blocked_reasons[0]` — the type is already narrowed there, good; but it's a one-off, not a repeated pattern.

---

#### M9 — `cockpit/export/cli.py` exception filter swallows `AttributeError` that should be a programming bug
**File:** `rytm_randomizer/cockpit/export/cli.py:405`

```python
except (ValueError, TypeError, OSError) as exc:
```

Missed: `KeyError` (would surface for malformed argv parsing — `_parse_args` can raise it via `_pop_value` though it actually raises `ValueError`, so we're fine), `FileNotFoundError` (subclass of `OSError`, ok), `PermissionError` (also `OSError`, ok). But `RuntimeError` from `pack_profile_model` is not caught and would propagate out of `handle_export_profile_model`, violating the docstring claim (line 357: *"no exception ever escapes the handler"*). `msgpack.exceptions.PackException` is also not in the list. Either expand the catch list or document the not-actually-comprehensive behaviour.

---

#### M10 — `app.py:209` `(OSError, RuntimeError, AttributeError)` swallow on port close is too broad
**File:** `rytm_randomizer/app.py:200-211`

```python
except (OSError, RuntimeError, AttributeError):  # pragma: no cover - best-effort
    _shutdown_logger = _observability_get_logger(__name__)
    _shutdown_logger.debug("port_close_failed_best_effort")
```

`AttributeError` here would indicate the `mido` backend changed its API or our `port` object isn't what we think. That's a programming error, not a runtime fluke worth swallowing. Drop `AttributeError` from the tuple. Best-effort cleanup is fine for `OSError`/`RuntimeError`; for `AttributeError`, fail loudly.

---

#### M11 — `_handle_wizard_start` drops an in-flight wizard with no telemetry
**File:** `rytm_randomizer/cockpit/ws/wizard_handlers.py:123-138`

The docstring acknowledges the race ("the previous session is dropped"). No log line, no event. Operator-facing wizard data the user spent minutes assembling is silently destroyed. At minimum, log a `WARNING` when a wizard is replaced mid-flight, and consider returning the discarded state in the ack so the UI can offer "restore previous wizard."

---

#### M12 — `_recompute_candidate` runs `mutate(...)` unconditionally on every `set_pad_lock`
**File:** `rytm_randomizer/cockpit/ws/handlers.py:266-273`, `:203-218`

`_handle_set_pad_lock` calls `_clear_send_plan_if_needed` which clears the send plan, then returns. It does NOT recompute the candidate even though locks affect which pads get sent. That's actually correct — locks affect the send plan, not the candidate. But `_handle_select_profile`, `_handle_set_depth`, `_handle_toggle_preview`, `_handle_regen` all call `_recompute_candidate` which runs the full `mutate` over every pad. For a 12-pad device with 100+ params each, that's ~1200 PRNG draws per command. Fine for a desktop, not fine for the Phase 4 embedded target that's supposed to run the same algorithm.

Not a bug, but a constraint to consider: cache the candidate keyed by `(snapshot_id, profile_id, depth, seed)`. The whole tuple is already what makes `mutate` deterministic — a memoisation layer is trivial and obviously safe.

---

#### M13 — `compute_crc` only masks to 32 bits; doesn't normalise sign
**File:** `rytm_randomizer/cockpit/export/model_format.py:187-196`

`zlib.crc32` in Python 3 already returns an unsigned int, so the `& 0xFFFFFFFF` is defensive against "some historical platforms." Fine. But the docstring's claim "zlib returns a signed int on some historical platforms" is **wrong for Python 3** — that was a Python 2 quirk. The mask is harmless; the comment is stale. Drop the comment or correct it.

---

#### M14 — Test architecture file `test_export_pipeline_invariants.py:140-167` lazily checks for `sign_profile_model` / `verify_profile_model` that don't exist by those names
**File:** `tests/architecture/test_export_pipeline_invariants.py:154-166`

The test probes for `sign_profile_model` and `verify_profile_model`. The actual exports (after WS-A landed) are `sign_profile_blob` and `verify_signed_blob`. The test is a no-op assertion that will never fire because `getattr(export, "sign_profile_model", None)` is always `None`. The assertion that "either both or neither" exist is unreachable.

Update the symbol names or rip the lazy block out — the WS-A merge it was racing has long since landed and the optional check is now misleading dead test code.

---

#### M15 — `EmptyAnalysisError` `DataError + ValueError` multi-inheritance is clever, but adds a dependency
**File:** `rytm_randomizer/cockpit/wizard/builder.py:89-105`

The pattern (subclass both the project's taxonomy class and a stdlib exception) is documented and works. But it means `builder.py` imports from `observability.errors`, which means `cockpit.wizard` depends on `observability`. That's a fine direction in the layer graph today but worth pinning in `tests/architecture/test_import_direction.py` — I didn't see `cockpit/wizard` enumerated explicitly there. If a future contributor moves `EmptyAnalysisError` to a top-level `cockpit/wizard/errors.py` without the dual inheritance, the architecture test should fail. Add the rule.

---

### LOW (style, minor naming, doc nits)

| # | File:line | Issue |
|---|---|---|
| L1 | `rytm_randomizer/cockpit/export/signing.py:184-188` | Hand-rolled `bytes([len(algo_bytes)])` concatenation x3. Use `struct.Struct(">B")` or `bytes([n, ...])` once with a helper. Reads cleaner. |
| L2 | `rytm_randomizer/cockpit/export/cli.py:266` | `f"verification.{key}: {_json_scalar(verification[key])}"` — loop variable `key` shadows the outer `key_bytes: bytes` (kind of). Rename to `field`. |
| L3 | `rytm_randomizer/cockpit/wizard/state.py:390-400` | `_replace` wraps `dataclasses.replace` and immediately does a local `from dataclasses import replace as _dc_replace`. Move the import to module top, drop the helper indirection. The `Self` type checker workaround can be replaced by an explicit return type annotation `-> "WizardState"`. |
| L4 | `rytm_randomizer/cockpit/ws/handlers.py:307` | `from .session import _fresh_seed  # local import to keep module surface clean` — `_fresh_seed` already lives in `session.py` (line 53). Move the import to module top; the "keep module surface clean" comment doesn't apply because `_fresh_seed` is single-underscore-private. |
| L5 | `rytm_randomizer/app.py:117` | `"- --arm       open a real MIDI port and run the interactive " "randomizer",` — adjacent string concatenation across lines. Use one string. |
| L6 | `rytm_randomizer/cli.py:271` | Same adjacent-string-concat pattern. |
| L7 | `rytm_randomizer/cockpit/export/writer.py:101-103` | `WriteError(DataError, OSError)` mixin docstring mentions `WizardSourcePathError` and `EmptyAnalysisError` — explanatory but couples the docs of three modules. If one renames, the others stale. Replace with one canonical reference. |
| L8 | `rytm_randomizer/cockpit/ws/server.py:84` | `await websocket.accept()` with no `subprotocol=` argument. Pinning a subprotocol name is a cheap defence-in-depth: the client must request it explicitly, so casual browser-tab connects fail handshake before the inner protocol fires. |
| L9 | `rytm_randomizer/cockpit/export/cli.py:124` | `_COMMAND_NAME: Final[str] = "cockpit-export-profile-model"` — and the registered `CliCommand.name` derives from it (line 432). Good. But the function-level docstring at line 6 still hard-codes the string in code examples. Use the constant in the docstring via `f"..."` or update by hand. |
| L10 | `rytm_randomizer/cockpit/__main__.py:43-44` | `_DEFAULT_DEVICE` and `_DEFAULT_BPM` look like enums-of-one. Fine for now; flag if more devices land. |
| L11 | `rytm_randomizer/cockpit/wizard/sysex_analyzer.py:67` | `if not isinstance(path, Path):` — redundant: the caller in `analyze.py:67` already wraps in `Path(...)`. The defensive check exists for direct callers, which is fine, but the `TypeError` shape (`"path must be a pathlib.Path"`) clashes with the surrounding `ValueError`/`FileNotFoundError` raise pattern. Pick one error class. |
| L12 | `rytm_randomizer/cockpit/profiles/registry.py:36` | `_logger: Final[logging.Logger] = logging.getLogger(__name__)` — gold-standard. But the other cockpit modules (`engine/mutate.py`, `wizard/builder.py`) don't have a `_logger`. Inconsistent observability adoption (Gate 7 is supposed to enforce this on the hot path). |
| L13 | `rytm_randomizer/cockpit/data/profile_model.py:131-134` | `known_trait_names = {t.name for t in self.traits}` rebuilt every `__post_init__`. Cheap, but if ProfileModel construction is hot (it's used in the mutation candidate path), cache via `__init_subclass__` or pre-validate at the builder layer. |
| L14 | `tests/architecture/test_export_pipeline_invariants.py:53` | Test name `test_export_pipeline_format_magic_is_RYMP` violates snake_case — `_RYMP` looks like a constant. PEP-8-wise, `test_export_pipeline_format_magic_is_rymp` reads better. |

---

## Patterns the Codebase Gets Right

These are worth preserving and propagating to the rest of the package.

1. **The Phase 3 export wire format is exemplary.** `rytm_randomizer/cockpit/export/model_format.py` and `signing.py` together are stdlib-only, big-endian-explicit, `struct.Struct` precompiled, length-prefix-validated at every variable-length field, and the parser walks left-to-right with a buffer-overrun check at each step. This is the cleanest binary-format module I've read in a Python codebase in a while.

2. **`hmac.compare_digest` is used correctly.** `verifier.py:128` does the timing-safe compare. Many code review targets get this wrong.

3. **The `VerificationResult` "never-raises" boundary is well-designed.** Categorical `reason` strings are documented and finite (verifier.py:51-60), which is exactly the contract a hand-written C reimplementation needs. The dataclass shape carries enough information for policy decisions ("accept unsigned reads from local-disk paths but demand signed reads from elsewhere") without re-parsing.

4. **`atomic_write` does the right things in the right order.** `writer.py:142-227` — sibling temp file in the same dir, write then `fsync` then `os.replace`, best-effort cleanup that does not mask the original error. The decision tree on `overwrite=False` (raise before writing the temp) is the right ergonomics.

5. **Frozen dataclasses everywhere.** Every cockpit data type is `@dataclass(frozen=True)`. Mutation goes through `with_*` helpers (`WizardState.with_metadata`, `with_source`, etc.) that return new instances. This is the discipline most Python codebases give up on at scale; this one held the line.

6. **The architecture-test suite is real, not aspirational.** 24 files in `tests/architecture/` that actually fail CI on violations. `test_no_any_escape_hatches.py` uses `ast` to parse every module, not regex — that's a senior choice. `test_export_pipeline_invariants.py` is the model for wire-format pinning: every test docstring says *why* the test exists and what bug it prevents.

7. **The PRNG choice is honest.** `xorshift32` with a documented 8-step warmup, normalisation, and an explicit substitute for `seed == 0`. The Phase 4 C-port author can implement this in 20 lines. The PRNG choice + the `_round_half_away_from_zero` helper together demonstrate that the engine author actually thought about cross-language portability.

8. **The CLI registry pattern is the right abstraction.** `cli_registry.py` is well-shaped: `CliCommand` is a frozen dataclass, `register` rejects duplicates loudly, `all_commands()` returns a `MappingProxyType`. The shape is correct; the problem (H7) is that `cli.py` doesn't fully consume it yet.

9. **The exception taxonomy hierarchy with multi-inheritance to preserve identity** (`observability/errors.py`) is the right design pattern for retrofitting a taxonomy onto an existing codebase. The lazy `__getattr__` re-export is more clever than necessary (H8) but the **idea** — keep the original class so `isinstance` checks don't change, augment the bases — is the right one.

10. **The `cockpit/data/types.py` Literal + `_VALUES` tuple pattern** is the textbook "single source of truth for an enum-like string". `KIND_VALUES`, `TRANSITION_CURVE_VALUES`, etc., are immutable, iterable at runtime, and the matching `Literal` keeps static type checkers honest.

## Patterns the Codebase Gets Wrong (Repeatedly)

Cross-cutting smells worth fixing once rather than per-instance.

### P1 — `# type: ignore[arg-type]` is used to launder `str` into `Literal`

At least seven occurrences:

- `rytm_randomizer/cockpit/data/profile_model.py:159, 163` — `kind=str(...)  # type: ignore`
- `rytm_randomizer/cockpit/wizard/builder.py:172, 176` — `kind=_PROFILE_KIND  # type: ignore`
- `rytm_randomizer/cockpit/wizard/state.py:118-119, 178-179, 376-377` — `from_dict` constructors
- `rytm_randomizer/cockpit/ws/wizard_handlers.py:180-181` — wizard handler
- `rytm_randomizer/cockpit/engine/mutate.py:226` — `safety_status=safety_status  # type: ignore`

Every one of these is the same shape: a `str` that the runtime knows is in `Literal[...]` but the type checker doesn't. The fix is a one-line `_narrow_kind(s: str) -> Kind` helper in `cockpit/data/types.py` per literal. Once it exists, every `# type: ignore[arg-type]` here can go away.

### P2 — `Mapping[str, object]` parameters at every dataclass `from_dict`

See M1. The fix: use the matching `TypedDict` from `protocol.py`, or define one per dataclass alongside it. Then the `data["kind"]` lookup is typed correctly without the `str(...)` widening dance.

### P3 — `del cmd` / `del description` to swallow unused parameters

`_handle_wizard_analyze:228`, `_handle_wizard_review:275`, `_handle_wizard_save:303`, `_handle_wizard_cancel:331`, `builder.py:151`. The Python idiom for "I'm intentionally not using this" is to underscore-prefix the parameter or use `_` (single underscore). `del` reads like "I cleared this on purpose so a typo doesn't pick it up later" which is technically true but heavy. The convention is fine if it's a convention, but it's not — most other handlers just don't reference unused parameters.

### P4 — Bandit/ruff per-file ignores in `pyproject.toml` are a small mountain

`pyproject.toml:188-247`. Per-file ignores for tests/, tooling/, Scripts/, scripts/, etc. Each one has a one-line justification (good). But the justifications cite "false positive by name only" and "subprocess.run with a static list, no shell, no user input" — both true. Worth a periodic re-audit: today the test bucket ignores nine rules, which is a lot. Investigate whether two or three of them are now unnecessary.

### P5 — Adjacent string concatenation across lines

L5, L6. Recurs in `app.py`, `cli.py`, `senders/`. Pick the right tool (`textwrap.dedent`, an f-string, or a sequence joined by `"\n".join`). The current pattern reads like a forgotten edit.

### P6 — "Defensive against a future" comments without tests for the future

`engine/mutate.py:182-184`: *"The data model enforces ascending order at construction; re-sorting defensively keeps the algorithm portable if that contract ever loosens."* Fine. But no test pins "engine still produces the same bytes after pad order is shuffled" — so the defensive sort exists, but nothing keeps it honest. Defensive code without a test isn't defensive; it's vestigial. Add the property-based test or remove the defense.

### P7 — Module docstrings include long historical commentary that doesn't help a new reader

`observability/errors.py:1-43`, `cockpit/export/cli.py:1-39`, `cli_registry.py:1-53` all spend their first 30+ lines explaining "why this module exists" in PR-history terms. Future readers want "what this module does" first, "why it's shaped this way" second, "what shipped in which WS" last (or in `docs/`). The current ordering inverts that. The architecture tests' docstrings (`test_export_pipeline_invariants.py`) actually got this right — what, then why, then which-bug-each-test-catches.

## Naming Audit

Prioritising public API and recurring offenders.

| Current | Issue | Suggested |
|---|---|---|
| `pack_profile_model(profile, *, format_version=1)` | `format_version` kwarg only exists for tests (M4) | `pack_profile_model(profile)` + private `_pack_with_version_override` |
| `verify_signed_blob(data, key=None, expected_key_id=None)` | `data` is generic; this is specifically a signed envelope | `verify_signed_envelope(envelope_bytes, ...)` |
| `_handle_export_profile_model` (WS handler) AND `handle_export_profile_model` (CLI handler) | Same name, different layers, easy to confuse | CLI's should be `run_export_profile_model_command` (it returns exit code, not result) |
| `SignedBlob` | "blob" everywhere; "envelope" elsewhere | `SignedEnvelope` (matches `pack_signed`/`unpack_signed` which are envelope ops) |
| `WriteResult.overwrote_existing` | Past tense, but it's a flag | `replaced_existing` reads cleaner |
| `VerificationResult.reason` | Reason for what? | `outcome` (categorical) or `failure_reason` (with `ok` as discriminator) |
| `CockpitSession.depth` | "depth" of what? | `mutation_depth` |
| `CockpitSession.seed` | Could be many seeds | `mutation_seed` |
| `_pad_bias(profile, pad_id)` (engine) | "bias" is loaded; this is a weighted-mean | `_pad_trait_weighted_mean(...)` |
| `_clamp_cc(value)` | OK but unstated unit | `_clamp_to_cc_range(value)` |
| `_recompute_candidate(session)` | Recompute against what? | `_rebuild_candidate_from_session(session)` |
| `_clear_send_plan_if_needed(session)` | "if needed" hides condition | `_invalidate_send_plan_if_present(session)` |
| `EmptyAnalysisError` | Empty what? | `NoAnalyzableSourcesError` |
| `WizardSourcePathError` | Path is hidden in name | `InvalidWizardSourceLocationError` |
| `_DEFAULT_DEPTH = 0.45` | Default depth of what | `_DEFAULT_MUTATION_DEPTH` |
| `extract_kit_traits(path)` | "extract" implies parsing; this is byte stats | `kit_byte_statistics_as_traits(path)` or rename module |
| `_traits_from_bytes(data)` | "traits" is musical; this is bytewise | `_canonical_traits_from_bytes(data)` |
| `_TOTAL_WEIGHT_FLOOR = 0.001` (mutate.py) | "floor" is also a function | `_MIN_TOTAL_WEIGHT_BEFORE_FALLBACK` |
| `_BIAS_FLOOR = 0.5` | Same | `_PAD_BIAS_BASE` (it's added to the bias, not a floor on it) |
| `_PRNG_SEED_FOR_ZERO` | OK but explain in name | `_PRNG_SUBSTITUTE_SEED_WHEN_INPUT_IS_ZERO` is too long; current is acceptable |
| `Phase 2 stub` (reference_analyzer module-level) | This is a *stub* shipped to users | rename module to `reference_analyzer_phase2_stub.py` OR raise `NotImplementedError` |

## Interface Hygiene

Where implementation bleeds through the public surface.

1. **`CockpitSession._pending_events` is a private side-channel exposed as a runtime attribute.** Already covered (H1). The dispatcher and `drain_pending_events` need each other; that's a coupling that belongs in a `CommandResult` returned from `handle_command`, not on the session.

2. **`cockpit.export.__all__` exports 22 names.** Some of those are internals: `SIGNATURE_FORMAT_VERSION`, `SUPPORTED_SIGNATURE_FORMAT_VERSIONS`, `SIGNATURE_HEADER_MAGIC` are wire-format constants the embedded firmware needs, fine. `SignedBlob` is a return type, fine. But `DEFAULT_EXPORT_SUBDIR` is an implementation detail — callers should use `default_export_dir()`, not the substring. Trim `__all__` to the genuine consumer surface (~14 names).

3. **`ProfileRegistry.save` returns `Path`** but the caller (`_handle_wizard_save:312`) ignores the return value. The contract should be `save -> None` and a separate `resolve_path(profile_id) -> Path` if anyone needs the path. Otherwise the return value is dead surface.

4. **`handle_command(envelope, session, emitter)` takes an emitter it never uses** — the emitter is only used by `drain_pending_events` which is a separate call. The function signature lies about its dependencies. Either drop the parameter or actually use it.

5. **The `_HANDLERS` dict at `handlers.py:458` is module-private but the wizard-handlers module imports `WIZARD_HANDLERS` from `wizard_handlers.py` and the dispatcher does the namespace split with a string `startswith("wizard_")` check at `:513`.** The right shape is a single registry with namespace-aware keys. The current "two dicts plus a string-prefix branch in the dispatcher" is the kind of split that grows wizard_v2 / device_v1 / ... arms over time.

6. **Cockpit's `export.cli` registers itself at import time via `_registry_register(COCKPIT_EXPORT_PROFILE_MODEL_CLI_COMMAND)`** (`cli.py:439`). The dispatcher (`rytm_randomizer/cli.py:_registered_command_exit_code`) hard-codes a list of `(module_name, attribute_name)` tuples — but the registry exists. Importing `cockpit.export.cli` triggers the registration; the dispatcher then has to *also* import it manually to make the registration fire. That's an import-time side effect with the same shape as the architecture-test-forbidden pattern. Either the registry self-discovers (e.g. via `pkgutil.walk_packages`) or the dispatcher uses the registry directly.

## Security Posture

The repo claims "passive by default · offline · no MIDI port opens." For the Python CLI, that holds. For the cockpit sidecar, it doesn't.

| Risk | Status | Severity |
|---|---|---|
| WS endpoint authentication | **None** | CRITICAL (C1) |
| WS origin check | **None** | CRITICAL (C1) |
| DNS-rebinding protection | **None** (loopback bind only) | CRITICAL (C1) |
| Path traversal in wizard sources | **None** | CRITICAL (C2) |
| Information disclosure via error messages | Present (H4) | HIGH |
| HMAC timing-safe compare | ✓ `hmac.compare_digest` | OK |
| HMAC key handling | ✓ never logged, never persisted by cockpit | OK |
| Atomic file writes | ✓ for export; ✗ for profile save (M7) | MEDIUM |
| Subprocess injection | N/A (no subprocess in cockpit) | N/A |
| Deserialization safety | MessagePack default mode (`raw=False`) is safe by default | OK |
| Profile JSON deserialization | Validated through `ProfileModel.from_dict` — but consumes arbitrary JSON, so a maliciously huge `traits` list could OOM the cockpit | LOW |
| WS message size limits | **None visible** — `receive_json` will buffer unbounded payloads | MEDIUM |
| Secrets in tests | `S105` allow-listed for tests/, audited — fine | OK |
| `--key-hex` CLI arg | Passes through process argv — visible to other local users via `/proc/<pid>/cmdline` | HIGH (no finding above; flagging here) |

**Aggregate verdict.** The export and signing pipeline itself is well-built. The cockpit's transport is naked. If the user `--arm`s and the WS layer ships in this shape, **a browser tab can send MIDI to the user's Analog Rytm.** That is not a theoretical attack. Browsers reach `127.0.0.1` daily.

## Type-System Honesty

The codebase claims (Gate 6) "no `Any`, only `Protocol` and `dataclass`." Reality:

- Zero `Sender = Any` aliases (test enforces it; clean win).
- 34 `# type: ignore` comments in `rytm_randomizer/cockpit/`, of which two are `attr-defined` (H1 side-channel) and the rest are `arg-type` (P1 `str` → `Literal` laundering).
- Liberal `Mapping[str, object]` (M1) — `object` is `Any` with type-checker handcuffs.
- 22 occurrences of `Any` in the package (mostly in `handlers.py`, `protocol.py` — JSON boundary). Some are unavoidable. Most are because the TypedDicts don't get consumed downstream.
- `Protocol` adoption is excellent at the cross-layer boundary: `DeviceAdapter`, `EventEmitter`, `MidiPortProvider`, `Sender`. No ABC creep.
- `@runtime_checkable` used precisely where needed (e.g. `EventEmitter` for test substitution).
- `Self` (PEP 673) used cleanly in `from_dict` returns.

**Honest summary:** the type system has the right shape but the wire-boundary widening (P1, M1) makes the static analysis at those boundaries cosmetic. The fix is mechanical: narrow at the boundary, never widen.

## Architecture Test Coverage

The 24-file `tests/architecture/` suite is the headline asset. What's actually enforced vs. aspirational:

| Gate | Test file | Enforced? | Notes |
|---|---|---|---|
| 1 | (per-PR coverage flag) | Toolchain, not arch test | OK |
| 2 | `test_engines_pad*` golden parity | ✓ | 685 fixtures, byte-frozen |
| 3 | Ruff / black / isort / pyright | Toolchain | OK |
| 4 | Vulture | Toolchain | OK |
| 5 | `test_readme_freshness.py`, `test_plan_doc_status_truth.py` | ✓ | |
| 6 | `test_no_any_escape_hatches.py` | ✓ | Bare `Any` aliases only — doesn't catch `Mapping[str, object]` (M1, P2). **Gap.** |
| 7 | `test_observability.py` | ✓ for the hot-path module list | But `cockpit/engine/mutate.py` and `cockpit/wizard/builder.py` lack loggers (L12). Either the enforcement list is stale or those modules don't qualify as "hot path"; the gate language says "every module that performs a state transition" — `mutate` is exactly that. **Gap.** |
| 8 | `test_shared_fixtures_available.py` | ✓ | Greps for duplicates of `RecordingOut` etc. Looked at it; it's per-pattern, not behavioural. Probably fine. |
| 9 | `test_no_new_top_level_modules.py` | ✓ | Hard list of top-level modules; new ones require sign-off via test edit |
| 10 | `test_no_string_literal_mode_dispatch.py` | ✓ | Greps for the forbidden strings outside `data/modes.py` |
| 11 | (covered by Gate 8) | | |
| 12 | (no dedicated test; relies on python-reviewer agent) | **Aspirational** | A grep for top-level `X = N` without `Final[T]` annotation would mechanize this. **Gap.** |
| 13 | (no dedicated test) | **Aspirational** | Env var registration could be enforced via a fixture-based audit. **Gap.** |
| 14 | `test_maintainability_review_present.py` (WS-S8 sweep) | ✓ at PR level | Doc-existence check, not quality |
| 15 | `test_learning_phase_complete.py` (post-WS-S8) | Aspirational, with target plan | |
| 16 | `test_plan_execution_shape.py` | Aspirational, target plan | |
| 17 | (no dedicated test; code-reviewer skill) | **Aspirational** | The `cli.py` ladder (H7) and the `_handle_export_profile_model` duplicate handler (P3) demonstrate the gate's enforcement is weaker than the gate. |
| 18 | `test_readme_freshness.py` (partial), `test_readme_phase_status_truth.py` | ✓ for README, weaker for ARCHITECTURE_DIAGRAMS.md | |

**The gaps that worry me most:** Gates 6, 7, 12, 17 are the "type system honesty / abstraction reuse" gates and they rely on a `code-reviewer` agent skill, not a CI test. The cli.py ladder (H7) and the dual `atomic_write` (C3) are exactly the failures Gate 17 was created to prevent. The agent-based enforcement is not catching them.

The Phase 3 export test file (`test_export_pipeline_invariants.py`) is the *gold standard* — every assertion has a docstring explaining the bug it prevents. Use it as the template when promoting the aspirational gates to real tests.

## Test Smells

- **Massive single-file test modules.** `tests/test_cli.py` is 4,445 lines. `tests/test_style_performance_arcs_report.py` is 6,029 lines. `tests/cockpit/test_export_pipeline_integration.py` is 1,121 lines. The architecture tests are properly per-concern; the surface-level tests have not been split. A 6K-line test file is a comprehension cliff for any new contributor.

- **Test count is impressive (3,900+) but the per-file ownership is unclear.** Whose responsibility is `test_cli_coverage.py` (1,585 LOC) vs. `test_cli.py` (4,445)? The names suggest one is the canonical surface test and the other was added to chase a coverage gate. That happens; it's worth cleaning up.

- **The architecture tests skip the largest reports.** I didn't see a test that bounds report-module line count or one that enforces "no `live_gui_*` module exceeds N functions." Given 41 such files most over 800 lines, there's no mechanical brake on this shape growing further.

- **Mock-heavy areas vs. real-boundary areas.** The `cockpit/ws/` tests appear to use real `TestClient` round-trips (good). The wizard tests should similarly avoid mocking `analyze_source`. I didn't read every test, but `tests/cockpit/test_wizard_state.py` at 760 lines suggests good unit coverage of the state transitions, which is the right place to spend test effort.

- **`PARITY_CAPTURE_MODE` is documented as the only env var that disables xdist, but the readme warns against `-o addopts=''`.** Two flags for the same shape (slow-mode), one supported, one not. The README warning suggests this has bitten people. A single, well-documented `--slow` marker would replace both.

## Recommended Follow-Up PRs

Numbered, scoped, each doable in < 500 LOC of diff. Listed roughly in priority order.

### PR 1 — Lock down the cockpit WebSocket sidecar (C1)
Add a per-launch HMAC token. Generated by `__main__.py:main()` via `secrets.token_urlsafe(32)`, written to `${RYTM_RAND_WS_TOKEN_FILE}` (or returned to the Tauri spawner via stdout). Required as the first WS frame; `hmac.compare_digest` against the file contents. Refuse all other commands until handshake. Also: `await websocket.accept(subprotocol="rytm-rand-cockpit-v1")`. ~120 LOC + tests.

### PR 2 — Wizard source-path allow-list (C2 + H4)
Add `WizardPathPolicy` (frozen dataclass) with a `roots: tuple[Path, ...]` field. Validate every `InspirationSource.location` against it at `_handle_wizard_add_source` time using `Path.resolve().is_relative_to(root)`. Default policy: `~/.rytm-randomizer/wizard-sources/` plus a `WIZARD_SOURCE_ROOTS` env var (per Gate 13: documented, safe default). Sanitize analyzer exceptions to categorical reasons. ~180 LOC.

### PR 3 — Delete the `cockpit/export/cli.py` fallback (C3)
Replace lines 57-122 with a hard `from .writer import ...`. Verify integration tests still pass; verify the `writer.py` error taxonomy actually matches what the CLI assumes downstream. ~80 LOC removal + 2 LOC import + test additions for the divergent behaviours.

### PR 4 — Promote `_pending_events` to a real session field (H1)
`CockpitSession.pending_events: list[dict] = field(default_factory=list)`. Drop two `# type: ignore`. Add `clear_pending_events` method. ~30 LOC.

### PR 5 — Narrow `str` to `Literal` at every wire boundary (P1, H2)
Add `cockpit/data/types.py` helpers: `narrow_kind(s: str) -> Kind`, `narrow_mode`, `narrow_status`, `narrow_transition_curve`. Each raises `ValueError` with the canonical message on bad input. Replace every `# type: ignore[arg-type]` for these literals across `cockpit/`. ~150 LOC across many files.

### PR 6 — Replace `Mapping[str, object]` with `TypedDict` consumers (M1, P2)
Per dataclass, define a sibling `TypedDict` (e.g. `ProfileModelDict`). Make `from_dict` accept that type. Drop the `str(...)` widening. ~250 LOC across `cockpit/data/`.

### PR 7 — Atomic, no-overwrite-by-default `ProfileRegistry.save` (M7)
Route `save` through `cockpit.export.writer.atomic_write`. Add a separate `force_overwrite=True` parameter if any real caller needs it (probably none). ~60 LOC.

### PR 8 — Complete the `cli_registry` migration (H7)
Pick the 10 most-used `cli.py:main` arms; convert each to a `CliCommand` registered in its target module (mirroring `cockpit/export/cli.py`'s pattern). Delete the corresponding `if args == [...]` arm. Add an architecture test that asserts no new `if args ==` arms can land in `cli.py`. ~400 LOC across many files.

### PR 9 — Sanitize wizard analyzer error surface (H4)
Map analyzer exceptions to a categorical reason set. Sanitize `AnalysisJob.error` to never echo input paths. Log full detail via `observability/logging.py`. ~80 LOC.

### PR 10 — Replace the `cockpit-export-rehearsal-report`'s 256-byte estimate with a real calculation (H6)
Either import `signing.pack_signed` for a real-bytes call (and update the "doesn't invoke the signer" docstring) or compute the envelope size analytically from the documented wire format. Add an architecture test that pins the actual envelope size to the formula. ~50 LOC.

### PR 11 — Split `reports/style_performance_arcs.py` (4,759 LOC)
Identify the 4-5 natural concerns inside (cue sheet, runbook, rehearsal manifest, export packet). Move each into a sibling module under `reports/style_performance/`. Keep `style_performance_arcs.py` as a thin re-export façade. ~50 LOC façade + ~4,700 LOC moved. **No semantic change.** Architecture test: `assert max_module_size(reports/) < 1500`. The benefit is comprehensibility, not cleverness.

### PR 12 — Architecture test for Gate 12 (Final constants)
AST walk every `rytm_randomizer/*.py`, fail if a top-level `Assign` of a literal lacks `Final[T]` annotation. Allowlist obvious exceptions (`__all__`, `_logger`). ~100 LOC.

### PR 13 — Architecture test for Gate 17 (abstraction reuse)
Detect candidates: any new module under `rytm_randomizer/` that defines a function named `atomic_write`, `pack_signed`, `verify_*`, `MutationPlanner`, etc., when one already exists elsewhere. Probably too noisy to be a hard gate; ship as a `pytest.mark.warning` informational. ~100 LOC.

### PR 14 — Sanitize WS error envelopes (related to H4)
Today `handle_command` returns `{"ok": False, "error": str(exc)}` (handlers.py:530). Replace with categorical error codes (`{"ok": False, "code": "unknown_command", "message": "..."}`) so clients can branch deterministically and so future log shippers can aggregate. ~120 LOC.

### PR 15 — Pin the C-port engine spec with explicit `-0.0` test cases (H5)
Add `tests/cockpit/test_engine_conformance_edge_cases.py`: `mutate` with seeds and parameters that produce `r == 0.5` exactly (so `r - 0.5 == 0.0`), `r * 2.0 * scale == -0.0`. Assert `_round_half_away_from_zero` and the full `mutate` agree with the spec. ~60 LOC.

---

**End of review.** Total findings: 4 critical, 8 high, 15 medium, 14 low. Combined with the 7 "patterns the codebase gets right" and 7 cross-cutting wrong-pattern themes. The fixes that should land before the next release are PRs 1, 2, 3, 4. Everything else is house-keeping.
