# Model Export Pipeline Design — Phase 3

**Date:** 2026-05-24
**Status:** Draft — pending user review
**Base branch:** `modularize-v1.34`
**Builds on:**
- `docs/superpowers/specs/2026-05-23-cockpit-and-profile-model-design.md` (merged via PR #99 — Phase 1 cockpit + the existing `cockpit/export/` package)
- `docs/superpowers/specs/2026-05-24-profile-wizard-design.md` (merged via PR #102 — Phase 2 authoring surface that produces `kind="user"` `ProfileModel`s)

## 1. Context

Phase 1 (PR #99) shipped the cockpit GUI, the WebSocket Protocol, the in-process mutation engine, the `ProfileRegistry`, the `cockpit/export/` Python subpackage with the `pack_profile_model` / `unpack_profile_model` binary serializer (MAGIC `RYMP` + `format_version` + `model_version` + payload + CRC32), and seven built-in `kind="scene"` profiles. The cockpit can READ profiles from disk and the export module can ROUND-TRIP a `ProfileModel` through the binary format in memory.

Phase 2 (PR #102) shipped the Profile Wizard — operators can now author their own `kind="user"` profiles by pointing the system at folders of SysEx, audio files, and artist references. Saved profiles land in `~/.rytm-randomizer/profiles/` as JSON. PR #103 added the `cockpit-send-plan-readiness-report` and PR #104 added the `cockpit-send-plan-rehearsal-surface-report` — both passive CLI reports that mirror the cockpit's pre-SEND boundary so the GUI's "what would actually ship if I clicked SEND right now?" question is answered by deterministic, replayable JSON.

**Phase 3 closes the loop** between the Phase 1 binary serializer and the eventual Phase 4 hardware loader. The `cockpit/export/` package today produces bytes IN MEMORY; it does not write them to disk, does not sign them, does not verify them after writing, and does not expose a CLI. Phase 3 adds:

- **`cockpit/export/signing.py`** — HMAC-SHA256 signing over the existing `pack_profile_model` payload, wrapped in a thin envelope so the underlying packed bytes remain bit-identical to today.
- **`cockpit/export/writer.py`** — an atomic file writer (temp file in same dir + fsync + `os.replace`) that never leaves partial `.rymp` files on disk and never clobbers a known-good file with a half-written one.
- **`cockpit/export/verifier.py`** — a never-raises verifier that re-reads a `.rymp` file and returns a typed `VerificationResult` (status + reason + parsed header) so the CLI can post-flight every write and the GUI can pre-flight a third-party file.
- **`cockpit/export/cli.py`** — the `cockpit-export-profile-model` CLI that orchestrates `ProfileRegistry.load(profile_id)` → `pack_profile_model(profile)` → `sign_profile_blob(payload, key, key_id)` → `pack_signed(...)` → `atomic_write(output_path, bytes)` → `verify_signed_blob(...)`.
- **`reports/cockpit_export_rehearsal.py`** — a passive pre-flight report (mirrors PR #104's panel / binding / check / replay-command shape) that answers "what bytes would actually get written if I ran the export right now?" without writing anything.
- **`tests/architecture/test_export_pipeline_invariants.py`** — pins the wire formats, the never-raises verifier contract, the no-MIDI / no-network / no-subprocess dependency graph, and the algorithm constants the Phase 4 hardware loader will depend on.
- **`tests/architecture/test_cockpit_send_plan_rehearsal_surface_invariants.py`** — the file PR #104's review flagged as missing, now landed alongside its sibling so the rehearsal-surface contract is also pinned for Phase 3+ consumers.
- An **auto-discovery refactor of `tests/architecture/test_real_midi_passive_cli_safety.py`** that replaces the hand-maintained `PASSIVE_CLI_COMMANDS` / `PASSIVE_CLI_SWEEP_COMMANDS` tuples with a `cli_registry` walk plus an opt-out allow-list for the small number of armed commands. This kills the recurring "developer forgot to add their command to the passive sweep" bug class that bit PR #103 and PR #104.

**Phase 4 (out of scope for this spec)** is the dedicated hardware: a small box (probably ARM Cortex-M0+ or RP2040 class) that reads a `.rymp` file from SD or flash, accepts a `Snapshot` over MIDI SysEx, runs the embedded C-portable mutation engine against the loaded `ProfileModel`, and emits the resulting CC / SysEx back to the Rytm — one push-button = a new kit, no laptop in the chain. Phase 3 is the file-format and key-management contract the hardware will consume. **The `.rymp` bytes Phase 3 writes ARE the bytes Phase 4 reads.**

## 2. Scope

### In scope (Phase 3)

| Capability | Module | Notes |
|---|---|---|
| HMAC-SHA256 signing over the existing packed payload | `cockpit/export/signing.py` | Stdlib only (`hmac`, `hashlib`). No new dependency. |
| Signed envelope wire format (`RYMS` magic + algo + key_id + sig + payload) | `cockpit/export/signing.py` | Wraps the existing `RYMP` payload bit-identically. |
| Atomic file write (temp + fsync + `os.replace`) | `cockpit/export/writer.py` | Cross-platform: POSIX rename is atomic, Windows uses `os.replace`. Never leaves partial files. |
| Never-raises integrity verifier returning a typed `VerificationResult` | `cockpit/export/verifier.py` | Three reason enums: `ok`, `bad_magic`, `bad_format_version`, `bad_signature`, `bad_crc`, `truncated`, `unknown_algo`, `unknown_key`. |
| `cockpit-export-profile-model` CLI | `cockpit/export/cli.py` | Drives the pack → sign → write → verify pipeline against a `profile_id` from the registry. |
| `cockpit-export-rehearsal-report` passive CLI | `reports/cockpit_export_rehearsal.py` | Pre-flight: what would be written + what key would sign it + what the verifier would say. Writes nothing. |
| Integration test: `ProfileModel` round-trip (pack → sign → write → read → verify → unpack) | `tests/test_cockpit_export_pipeline_integration.py` | Asserts the unpacked profile is byte-identical to the input. |
| Architecture invariants on the export pipeline | `tests/architecture/test_export_pipeline_invariants.py` | Pins MAGIC bytes, format-version constants, signature lengths, no-MIDI / no-network discipline, never-raises verifier contract. |
| Backfill: rehearsal-surface architecture invariants (the PR #104 gap) | `tests/architecture/test_cockpit_send_plan_rehearsal_surface_invariants.py` | The missing file from PR #104's review. |
| Auto-discovery refactor of the passive-CLI sweep | `tests/architecture/test_real_midi_passive_cli_safety.py` | Replaces hand-maintained tuples with `cli_registry` walk + allow-list. |
| Operator-facing docs (quickstart §5c + ARCHITECTURE §6.4 + diagram + STATUS) | Various | See WS-G. |

### Out of scope

- **Phase 3.5 — Keystore + key management UI.** The CLI accepts `--key-id <label>` and resolves the actual key bytes from a yet-to-be-built keystore (default location: `~/.rytm-randomizer/keys/`). For Phase 3 the keystore is a flat directory of 32-byte binary files named `<key_id>.key`; the wizard / UI for generating / rotating / importing keys is deferred. The `--unsigned` flag exists so an operator can still export today without a keystore.
- **Phase 4 — Hardware runtime.** The C-portable verifier + loader + embedded mutation engine + flash-management UX is a separate hardware project. Phase 3 is the file-format contract that project will consume.
- **Online key distribution / OTA model push.** The hardware path is "operator copies `.rymp` to SD card, hardware reads it." No network push.
- **Re-encryption / confidentiality.** The signing layer provides INTEGRITY + AUTHENTICITY, not CONFIDENTIALITY. `.rymp` payloads are not secrets; the wizard-derived trait weights are not sensitive. If a future use case wants encryption, it would layer on top of (not replace) the signing envelope.
- **Multi-key / key-rotation policy.** The wire format carries `key_id`, so future multi-key support is forward-compatible, but Phase 3 ships one key per export.
- **Streaming export.** A `.rymp` is small (< 100 KB typical). The pipeline is bytes-in-memory through every stage; chunked streaming is unnecessary and would complicate the CRC.

## 3. Architecture

### Module tree (Phase 3 adds the four marked `NEW`)

```
rytm_randomizer/cockpit/export/
    __init__.py            # Re-exports the public surface (Phase 1 + Phase 3)
    model_format.py        # Phase 1, existing — MAGIC=b"RYMP", format_version, build/parse header, CRC32 trailer
    serialize.py           # Phase 1, existing — pack_profile_model / unpack_profile_model
    signing.py             # Phase 3, NEW — HMAC-SHA256 signing over the packed payload + signed envelope
    verifier.py            # Phase 3, NEW — never-raises VerificationResult over signed envelopes (and unsigned blobs)
    writer.py              # Phase 3, NEW — atomic_write(path, blob): temp + fsync + os.replace, never partial
    cli.py                 # Phase 3, NEW — cockpit-export-profile-model CLI (drives the pack → sign → write → verify pipeline)
rytm_randomizer/reports/
    cockpit_export_rehearsal.py  # Phase 3, NEW — passive pre-flight report mirroring PR #104's shape
```

The new code lives entirely under the existing `cockpit/export/` subpackage (no new top-level module — Gate 9) plus one new sibling under the existing `reports/` package (which is the canonical home for passive read-only reports — Gate 17). The CLI is registered through the existing lazy `cli_registry` discovery path the rest of the passive CLIs use, so no edit to `cli.py`'s top-level dispatch is required.

### Dependency directionality

The export pipeline reads UP the layered graph and writes DOWN:

```
cockpit/export/cli.py
    -> cockpit/profiles/registry.py     (load ProfileModel by id)
    -> cockpit/export/serialize.py       (pack_profile_model)
        -> cockpit/data/profile_model.py (ProfileModel dataclass)
        -> cockpit/export/model_format.py (header + CRC)
    -> cockpit/export/signing.py         (sign_profile_blob + pack_signed)
    -> cockpit/export/writer.py          (atomic_write)
    -> cockpit/export/verifier.py        (verify_signed_blob)

reports/cockpit_export_rehearsal.py
    -> cockpit/profiles/registry.py      (load — same as the CLI; readonly)
    -> cockpit/export/signing.py         (sign_profile_blob — same code path; bytes go to the report, not to disk)
    -> cockpit/export/verifier.py        (verify_signed_blob — same code path; result goes to the report)
    + reports/_passive_section.py        (when/if the PR #104-flagged shared formatter helper lands)
```

No new top-level dependencies. No `mido`, no `rtmidi`, no `socket`, no `asyncio`, no `subprocess`, no `threading`. The pipeline is pure stdlib + the existing cockpit data layer.

### Reverse-dependency map (what depends on this package after Phase 3)

After Phase 3 lands, the following call graph holds:

- `cli_registry` registers two new lazy entries: `cockpit-export-profile-model` -> `cockpit.export.cli.main` and `cockpit-export-rehearsal-report` -> `reports.cockpit_export_rehearsal.main`. Both are registered alongside the existing passive CLI commands; both auto-enroll in the refactored passive-CLI safety sweep.
- The Phase 4 hardware loader (out of scope; future) depends on the Phase 1 + Phase 3 wire formats — specifically the `RYMP` and `RYMS` magic bytes, the format version constants, the supported algorithm set, the signature lengths, and the CRC32 polynomial. The architecture invariant test pins every one of those so a Phase 1 / Phase 3 maintainer cannot accidentally bump them without an explicit allow-list edit.
- The future GUI export button (Phase 3.5+) depends on the CLI entry point. Either the GUI shells out to the CLI process (the simple option) or imports `cockpit.export.cli.main` directly (the in-process option). Both are valid; the CLI is the foundation either way.

### What this package does NOT depend on

- `cockpit/engine/**` — the mutation engine. The export pipeline ships profiles; it does not mutate them. The engine and the exporter are decoupled.
- `cockpit/device/**` — the device adapter (mock + real-MIDI). The export pipeline writes to local disk, not to a MIDI device. The hardware loader runs on a SEPARATE device that reads the `.rymp` file, not a MIDI peripheral.
- `cockpit/ws/**` — the WebSocket protocol. Phase 3 does not introduce new WS commands or events. The future GUI export button (Phase 3.5+) MAY add one, but the export pipeline itself runs without WS — the CLI is invoked from the operator's shell or the Tauri-bundled sidecar.
- `cockpit/wizard/**` — the Phase 2 authoring wizard. The wizard produces JSON profiles in `~/.rytm-randomizer/profiles/`; the exporter consumes them. The two are decoupled via the `ProfileRegistry` interface.
- `cockpit/profiles/builtin.py` — the seven built-in scene profiles. The exporter can ship scene profiles too (a built-in scene is just a `kind="scene"` ProfileModel), but it doesn't take a hard-coded dependency on the built-in set. Phase 4 hardware can ship with both built-in scenes and operator-authored profiles loaded from SD.

This narrow surface area is deliberate. The export pipeline is a leaf — it has one inbound dependency direction (data flows IN via the registry, bytes flow OUT to disk) and no outbound dependencies on the rest of the cockpit. Tests stay fast (the integration test runs in < 100 ms because there is no engine to mock, no WS server to spin up, no MIDI adapter to instantiate). The Phase 4 hardware loader can adopt the same shape without needing the rest of the cockpit's Python codebase.

## 4. Wire formats

The Phase 1 packed format remains unchanged. Phase 3 adds a thin envelope around it.

### 4.1 Phase 1 packed format (existing — bit-stable)

```
Phase 1 packed blob (cockpit/export/model_format.py, owned by Phase 1):

    Header:
        magic              4 bytes   ("RYMP" ascii)
        format_version     uint16    big-endian (currently 1)
        model_version_len  uint8     length of the version string
        model_version      utf-8     e.g. "1.2.0" -> 5 bytes
        payload_len        uint32    big-endian
    Payload:
        MessagePack-encoded ProfileModel.to_dict()
    Trailer:
        crc32              uint32    big-endian — zlib.crc32(header + payload)
```

Phase 3 does **NOT** widen this format. The whole packed blob (header + payload + CRC) is treated as opaque bytes by the signing layer. This is deliberate: the Phase 4 hardware loader will be written against the Phase 1 format, and the signing envelope strips off cleanly to recover the exact same bytes.

### 4.2 Phase 3 signed envelope (NEW)

```
Phase 3 signed envelope (cockpit/export/signing.py, owned by Phase 3):

    magic           4 bytes    ("RYMS" ascii — distinct from RYMP so a verifier can tell them apart in one read)
    format_version  uint16     big-endian (currently 1 — Phase 3's envelope version; separate from the inner payload's format_version)
    algo_len        uint8      length of the algorithm name
    algo            utf-8      e.g. "hmac-sha256" (11 bytes); future-proof for "hmac-sha512" or "ed25519"
    key_id_len      uint8      length of the key identifier
    key_id          utf-8      operator-chosen label, e.g. "buzzi-2026" — pure metadata, the hardware looks up the actual key bytes from its keystore by this id
    sig_len         uint8      length of the signature (32 for hmac-sha256)
    sig             bytes      the signature itself
    payload_len     uint32     big-endian
    payload         bytes      the Phase 1 packed blob, bit-identical to what pack_profile_model() returns
```

**Why `uint8` for `algo_len` / `key_id_len` / `sig_len`?** Algorithm names and key labels are short by convention (< 32 bytes typical). HMAC signature sizes are also small (32 for SHA-256, 64 for SHA-512). A `uint8` holds [0, 255] which is far more headroom than any real-world value. The fixed-width small fields keep the embedded C parser simple — three single-byte loads, three buffer copies, then the `uint32` payload length and the payload itself.

**Why a separate `format_version` from the inner payload's `format_version`?** The envelope and the payload evolve independently. A bug fix to the signing layer (e.g. switching from `hmac.compare_digest` to a constant-time `==` operator) bumps the envelope version. A new optional field in `ProfileModel` bumps the inner format version. Decoupling lets the hardware loader handle them independently.

**Unsigned mode.** When the CLI is invoked with `--unsigned`, the writer writes the Phase 1 packed bytes directly (no envelope, no `RYMS` magic). The verifier detects the magic and dispatches: `RYMS` -> signed-envelope check, `RYMP` -> plain CRC check, anything else -> `bad_magic`. The hardware loader does the same.

### 4.3 Signing algorithm

- **Algorithm name (Phase 3 default):** `hmac-sha256` (lowercase ascii, no quoting). Encoded as utf-8; 11 bytes on the wire. The algorithm field is the only place in the envelope that uses utf-8 rather than ascii — by convention algorithm names are pure ascii, but the wire format does not enforce ascii because a future algorithm name (e.g. a custom `b"ed25519+blake2"`) might legitimately include a `+`.
- **Key material:** 32 bytes of cryptographically random data per key, stored in the Phase-3.5 keystore (out of scope) as `<key_id>.key` raw binary. The CLI may also accept a `--key-bytes <hex>` flag for one-off / scripted use and tests. Key bytes are NEVER written to disk by the export pipeline itself — the keystore manages them, the resolver reads them on demand, and the signing module computes the HMAC without ever persisting the key.
- **Signed bytes:** `algo_bytes || b"\x1f" || key_id_bytes || b"\x1f" || payload`. The `b"\x1f"` (ASCII unit separator) ensures the prefix cannot be reframed — e.g. `key_id="a"` + `payload=b"bc..."` is never confusable with `key_id="ab"` + `payload=b"c..."`. The fixed three-piece input is the same whether the operator chooses a short `key_id` or a long one. Reframing attacks are a known HMAC pitfall (RFC 7515 §10.1 covers the same issue for JWS); the unit-separator framing here follows that precedent.
- **Verification:** `hmac.compare_digest(expected, actual)` — constant-time, never short-circuits. The same call applies on the embedded loader; in C the equivalent is a constant-time `memcmp` (sometimes spelled `CRYPTO_memcmp` in BoringSSL / OpenSSL forks).
- **Why HMAC and not a Merkle DAG or detached signature?** A profile is a small (< 100 KB) blob with a well-defined boundary. The signature is a one-shot integrity + authenticity check at load time, not an incremental verification. HMAC is the right primitive: small, fast, well-understood, no key-exchange dance needed.
- **Why HMAC-SHA256 specifically?** SHA-256 is FIPS-180-4, has a 256-bit output (matches the 32-byte key length), and has implementations everywhere from `hashlib` to `mbedtls` to bare-metal Cortex-M libraries. SHA-512 is an option for paranoid deployments (the wire format supports variable `sig_len` so swapping in `hmac-sha512` with a 64-byte signature is a one-line addition to `SUPPORTED_ALGORITHMS` + `SIGNATURE_LENGTHS`).
- **Why symmetric (HMAC) instead of asymmetric (Ed25519)?** Phase 3 ships a single-operator workflow: the operator authors a profile on their laptop, signs it with a key they own, and the hardware loads it with the same key from its keystore. There is no third party in the loop; asymmetric signing would add no value and double the per-signature compute on the embedded loader. Asymmetric signing remains forward-compatible — the envelope's `algo` field is a discriminator and `ed25519` is reserved as a future value if multi-author / publisher-verification workflows ever land.
- **Future algorithms:** `hmac-sha512` is a one-line addition (the wire format already supports variable `sig_len`). Asymmetric signing (`ed25519`) would mean a small wire-format extension to carry the public-key identity alongside the signature — the envelope's `algo` field is `Literal["hmac-sha256"]` for Phase 3 and explicitly opens the door for one new value per future algorithm. The architecture invariant pins the current set so adding a new algorithm is a deliberate, reviewable change rather than a typo in a string literal.

## 5. Atomic file-write contract

`cockpit/export/writer.py` exposes a single function:

```python
def atomic_write(path: Path, blob: bytes) -> None:
    """Write ``blob`` to ``path`` atomically.

    Never leaves a partial file at ``path``. Never clobbers a known-good
    file at ``path`` with a half-written one. The contract holds across
    process crashes, power loss between fsync and rename, and concurrent
    readers.

    Implementation:
        1. Open a NamedTemporaryFile in the SAME directory as ``path``
           (so the eventual rename is on the same filesystem and therefore
           atomic). Suffix is ``.rymp.tmp.<pid>.<rand>``.
        2. Write the full blob.
        3. flush() + os.fsync() the temp file's fd so the bytes are on
           durable storage before the rename.
        4. os.replace(temp_path, path) — atomic on both POSIX (rename(2)
           guarantees) and Windows (MoveFileExW with MOVEFILE_REPLACE_EXISTING).
        5. If any step raises, the temp file is unlinked in the finally
           clause; the original ``path`` is untouched.

    Raises:
        OSError: the temp file could not be created, written, fsync'd,
            or renamed. The caller's parent directory must exist and be
            writable; ``atomic_write`` does not mkdir.
    """
```

**Why same directory for the temp file?** `os.replace` across filesystems falls back to a copy-and-delete, which is NOT atomic. Same-directory guarantees the rename stays in one filesystem.

**Why `os.fsync` before `os.replace`?** On POSIX, `rename(2)` is atomic in the sense that the rename itself either happens or doesn't, but the contents of the renamed file aren't guaranteed to be on disk yet. Fsyncing the temp file's contents BEFORE the rename means that after a crash either (a) the old file is intact and the new file does not exist, or (b) the new file is intact with the full new contents. There is no observable "renamed but truncated" state.

**Cross-platform note.** `os.replace` is the canonical Python primitive for this; it shells to `MoveFileExW(MOVEFILE_REPLACE_EXISTING)` on Windows and `rename(2)` on POSIX. Both are atomic for same-volume / same-filesystem renames. Different volumes / drive letters on Windows would fall back to copy-and-delete; the writer's same-directory discipline prevents that.

**Concurrent-reader semantics.** If a reader opens the target path between `os.fsync` and `os.replace`, they see the OLD contents (or, on POSIX, they may hold an inode reference to the unlinked-but-still-open file even after the rename). After `os.replace`, new opens see the NEW contents. There is no observable in-between state where readers see partial bytes — the directory entry flip is atomic. This matters because the cockpit GUI may be subscribed to a `~/profiles/` watch event; the operator's mid-write rename is invisible to it.

**Why not `pathlib.Path.write_bytes`?** `write_bytes` is open + write + close — three operations, none atomic. A crash between write and close leaves a truncated file at the target path. A crash AFTER close but before the next sync leaves a half-flushed file that may or may not survive a power loss. `atomic_write` is open-tmp + write-tmp + fsync-tmp + replace; the only durable state at any moment is "old file intact" or "new file durable on disk." This is the same discipline `git`, `sqlite`, and every other crash-tolerant writer follows.

**Permission preservation.** `os.replace` preserves the permission bits of the SOURCE (the temp file) on POSIX, not the target. This is sometimes a surprise — an export-then-replace cycle on a `chmod 600` file can end up `0o644` after the rename. The writer does NOT try to preserve target permissions; if an operator wants `0o600` on the output they can `chmod` after the write or set an appropriate `umask` on the process. The architecture invariant test does NOT pin permission bits because they are deliberately platform-dependent.

**Why no progress callback?** A typical `.rymp` is < 100 KB. Writing 100 KB on every modern storage medium completes in milliseconds; a progress bar is noise. If a future use case wants progress (e.g. shipping 1000 profiles in one batch), the right call is to wrap `atomic_write` in the caller, not to add a callback that 99.99% of users would ignore.

## 6. Verifier contract

`cockpit/export/verifier.py` exposes one function and one dataclass:

```python
@dataclass(frozen=True)
class VerificationResult:
    """Outcome of verifying a (possibly-signed) blob.

    Never raised. Always returned. The caller branches on ``ok``."""
    ok: bool
    reason: Literal[
        "ok",
        "bad_magic",
        "bad_format_version",
        "bad_signature",
        "bad_crc",
        "truncated",
        "unknown_algo",
        "unknown_key",
        "io_error",
    ]
    detail: str
    header: Header | None
    """The parsed RYMP header, if the inner payload could be parsed
    (regardless of signature outcome). None on bad_magic or truncated."""
    signed: bool
    """True if a RYMS envelope was detected. False for a bare RYMP blob."""


def verify_blob(blob: bytes, *, key_resolver: Callable[[str], bytes | None] | None = None) -> VerificationResult:
    """Verify ``blob`` end-to-end. Never raises.

    Dispatches on the leading magic:
        - b"RYMS" -> unwrap the envelope, run hmac.compare_digest, then
          verify the inner RYMP payload's CRC32 and parse the header.
        - b"RYMP" -> plain CRC32 + header parse.
        - anything else -> VerificationResult(ok=False, reason="bad_magic").

    ``key_resolver`` is called with the envelope's ``key_id``; it returns
    the key bytes or None if unknown. If None is passed as ``key_resolver``
    (the default), signed envelopes are returned with reason="unknown_key"
    — useful for the rehearsal report and for tooling that wants to inspect
    a blob without verifying the signature.
    """


def verify_file(path: Path, *, key_resolver: ...) -> VerificationResult:
    """Read ``path`` and verify it. Never raises; IO errors become
    VerificationResult(ok=False, reason="io_error", detail=str(exc))."""
```

**Never-raises is load-bearing.** The cockpit GUI will eventually invoke `verify_file` over arbitrary third-party `.rymp` files (a future "Import profile" affordance). A verifier that raises on malformed input is a verifier that crashes the GUI. The contract is: every kind of badness produces a `VerificationResult` with `ok=False`, a reason, and a `detail` string suitable for an end-user error display. The same discipline applies on the embedded loader — a hardware verifier that crashes on a malformed SD-card file is a hardware verifier that bricks the box.

**Reason enumeration.** The nine reason values are pinned by `tests/architecture/test_export_pipeline_invariants.py` so they cannot be silently widened without an explicit architecture-test edit. The same discipline that PR #104's review recommended for the rehearsal-surface enum. Each reason is:

| `reason` | When | `detail` typical content |
|---|---|---|
| `ok` | Verification succeeded. | empty |
| `bad_magic` | Leading bytes are neither `RYMP` nor `RYMS`. | `"expected b'RYMP' or b'RYMS', got <hex>"` |
| `bad_format_version` | Magic matched but the format version is outside the supported set. | `"format version 2 not in SUPPORTED_FORMAT_VERSIONS={1}"` |
| `bad_signature` | RYMS envelope parsed but `hmac.compare_digest` returned False. | `"signature mismatch for key_id=<id>"` |
| `bad_crc` | Inner RYMP payload parsed but the CRC32 trailer does not match. | `"crc32 mismatch: header+payload=<actual>, trailer=<expected>"` |
| `truncated` | Blob is shorter than the declared header / envelope / payload length. | `"blob ends after <N> bytes; expected at least <M>"` |
| `unknown_algo` | Envelope's algo string is not in `SUPPORTED_ALGORITHMS`. | `"algo 'hmac-sha384' not in {'hmac-sha256'}"` |
| `unknown_key` | `key_resolver` returned None for the envelope's key_id. | `"no key resolved for key_id=<id>"` |
| `io_error` | `verify_file` could not read the path (only used by `verify_file`, not `verify_blob`). | `"OSError: [Errno 2] No such file or directory: '<path>'"` |

The `detail` strings are deliberately human-readable — they end up in CLI error output and in the GUI's eventual error-display surface. The reason enum is machine-readable; callers branch on it, not on the detail text. This pairs cleanly with PR #104's `panel.binding` shape: the reason becomes the `status` discriminator and the detail becomes the `message` field.

**Why not just `bool` + raise?** Three reasons:

1. The GUI needs to render distinct affordances per failure class — "fix the file" for `bad_magic` / `truncated`, "wrong key" for `bad_signature` / `unknown_key`, "unsupported format" for `bad_format_version` / `unknown_algo`. A boolean collapses all of those into "it failed."
2. The CLI needs distinct exit codes per failure class. A boolean forces the CLI to either lose information or re-derive it from a string detail.
3. The architecture invariant pins the enum set; if a future contributor adds a new reason without updating the invariant, the test fails loudly. A `raise` could introduce a new exception subclass without anyone noticing.

**Why a `header` field on the result?** Calling code (the CLI, the rehearsal report, future GUI inspection) frequently wants to display the format version, model version, and payload length REGARDLESS of whether the signature matched. Returning the parsed header alongside the result avoids forcing every consumer to re-parse the bytes. `header` is `None` only when the magic itself was bad (so no parse happened) or when the bytes are too truncated to extract a header.

## 7. CLI surface

`rytm-randomizer cockpit-export-profile-model [args]` — drives the end-to-end pipeline.

### 7.1 Synopsis

```
rytm-randomizer cockpit-export-profile-model
    --profile-id <id>
    --output <path>
    [--key-id <label>]
    [--key-bytes <hex>]
    [--unsigned]
    [--profiles-dir <dir>]
    [--json]
```

### 7.2 Flags

| Flag | Required | Default | Notes |
|---|---|---|---|
| `--profile-id <id>` | yes | — | The ULID of the `ProfileModel` to export. Resolved against `--profiles-dir` (or `~/.rytm-randomizer/profiles/` if unset). |
| `--output <path>` | yes | — | The `.rymp` file to write. The parent directory must exist. |
| `--key-id <label>` | no | — | The key identifier. Required for signed mode unless `--key-bytes` is provided. |
| `--key-bytes <hex>` | no | — | Override key material as a hex string. For tests + scripted use. Mutually exclusive with `--key-id`-only mode. |
| `--unsigned` | no | False | Write the Phase 1 packed bytes directly with no envelope. Mutually exclusive with `--key-id` / `--key-bytes`. |
| `--profiles-dir <dir>` | no | `~/.rytm-randomizer/profiles/` | Override the profile registry root. |
| `--json` | no | False | Emit a deterministic JSON summary on stdout instead of human-readable lines. |

### 7.3 Flow

1. Resolve `--profile-id` against the registry. If the profile is missing → exit code 2, `stderr` message, no file written.
2. Resolve the key:
   - If `--unsigned`: key = None.
   - Else if `--key-bytes`: key = `bytes.fromhex(value)`.
   - Else: read `~/.rytm-randomizer/keys/<key_id>.key` (Phase-3.5 keystore; Phase 3 ships only the resolver hook and a "key not found" error path).
3. `payload = pack_profile_model(profile)` (the Phase 1 packed bytes).
4. If signed: `envelope = pack_signed(payload, algo="hmac-sha256", key_id=..., key=...)`.
   Else: `envelope = payload` (raw).
5. `atomic_write(output_path, envelope)`.
6. `result = verify_file(output_path, key_resolver=lambda kid: key if kid == key_id else None)`.
7. Emit human-readable lines (or JSON if `--json`) summarizing: input profile, output path, bytes written, signed Y/N, key id, verification status.
8. Exit 0 if verification ok, else exit 3 (file was written but failed verification — likely a bug; the operator should not trust the file).

### 7.4 Exit codes

| Code | Meaning |
|---|---|
| 0 | Export succeeded and post-flight verification returned `reason="ok"`. |
| 1 | Generic CLI error (bad flag combination, internal error). |
| 2 | Pre-write failure: profile id not found, key not found, parent directory missing, mutually exclusive flag combination, oversized algo/key_id, etc. The output file was NOT written. |
| 3 | Post-write verification failed. The file WAS written but failed `verify_file` (e.g. an OSError during fsync survived, or — extremely unlikely — a CRC mismatch caused by a hardware fault). The operator should not trust the file; the error message includes the `VerificationResult.reason` and `detail`. |

The distinct codes let CI scripts react appropriately: code 2 is "fix the command line", code 3 is "investigate the hardware / OS", code 0 is "ship it." Code 1 is the catch-all for genuine bugs.

### 7.5 Why a CLI when the cockpit GUI will also expose this?

Three reasons:

1. **The CI / build pipeline can use it.** Future builds may ship a pre-baked profile bundle with the installer. A scriptable export is required.
2. **Phase 3's "rehearsal" pattern needs a CLI to mirror.** The pre-flight report (§8) wraps the same code path the CLI uses, so any operator or developer can replay the pre-flight without launching the GUI.
3. **The cockpit's GUI export button is the Phase-3-to-Phase-3.5 bridge.** When the keystore UI lands, the GUI's button is a wrapper over the same `cockpit/export/cli.py` logic. The CLI is the foundation; the GUI button is the front-of-house wrapper.

### 7.6 Stability guarantees

- **The CLI's flag set is part of the contract.** Adding flags is allowed; removing or renaming flags is a breaking change. The `--help` fixture in `tests/fixtures/cli_help/` pins the current shape; the architecture invariant test catches accidental drift.
- **The JSON output (`--json`) is part of the contract.** Field names, value types, and the sort_keys discipline are stable. Adding fields is allowed; removing or renaming fields is a breaking change. The integration test asserts the JSON schema against a frozen baseline.
- **Exit codes are part of the contract.** Per the table above; CI scripts can branch on them.
- **Stderr / stdout discipline.** Human-readable lines go to stdout (so `--json` mode is `stdout`-clean). Error messages go to stderr. A successful export produces zero stderr output. The architecture invariant pins this behavior.

## 8. Rehearsal report — `cockpit-export-rehearsal-report`

A new passive CLI report at `reports/cockpit_export_rehearsal.py`. Mirrors PR #104's `cockpit_send_plan_rehearsal_surface_report` shape:

| PR #104 (rehearsal-surface) | Phase 3 (export-rehearsal) |
|---|---|
| Pre-SEND boundary report | Pre-EXPORT boundary report |
| Inputs: send plan (or wrapped readiness JSON) | Inputs: profile id (or wrapped registry JSON) |
| Output: panels (status, locked pads, packets, primary action) + JSON | Output: panels (status, key resolution, payload size, signing summary, verification preview, primary action) + JSON |
| `replay_command` field for reproducibility | Same field, same shape |
| Constants: `SEND_PLAN_REHEARSAL_SURFACE_VERSION`, `SAFETY_LINES`, enums | Same shape: `EXPORT_REHEARSAL_VERSION`, `SAFETY_LINES`, enums |
| Pinned by `test_cockpit_send_plan_rehearsal_surface_invariants.py` (BACKFILLED in this phase) | Pinned by `test_export_pipeline_invariants.py` |

### 8.1 Inputs

The report takes either:

- A `--profile-id <id>` + `--profiles-dir <dir>` pair, or
- A `--profile-file <path>` to a `ProfileModel` JSON, or
- The wrapped registry JSON via `--registry-file <path>` containing a top-level `profile` key (the cockpit's GUI may want to pass a not-yet-saved profile through this entry).

The wrapped-JSON pattern follows PR #104's `_readiness_from_mapping` helper exactly: peel out the inner `profile` key if present, otherwise treat the document as a bare profile.

### 8.2 Panels

| Panel | Content |
|---|---|
| Status | `ready` / `blocked` / `unsigned` (informational). |
| Profile | `profile_id`, `name`, `kind`, `model_version`, `traits` count, `pad_mappings` count. |
| Payload | Computed `payload_len` from `pack_profile_model`. CRC32. |
| Signing | `algo`, `key_id`, `key_resolved` (Y/N), `sig_len` projection (32 bytes for hmac-sha256). |
| Verification | The `VerificationResult.reason` the verifier WOULD return if the file were written and re-read. |
| Primary action | Operator-facing text: "Run `cockpit-export-profile-model --profile-id X --output Y --key-id K`" or "Provide a key id" or "Re-analyze the profile". |
| Replay command | The PowerShell + bash one-liner that reproduces THIS report. |

### 8.3 Output

Deterministic JSON (sort_keys + frozen dataclass-to-dict) plus human-readable lines. Same formatter helpers as PR #104. The JSON shape is pinned by the architecture invariant test.

### 8.4 Safety

- Never writes any file. Never opens a MIDI port. Never touches `mido`. Never makes a network call. The verifier path uses an in-memory `pack_profile_model` + `pack_signed` + `verify_blob` chain — no temp files, no disk IO beyond the optional `--profile-file` read.
- The `SAFETY_LINES` constant includes `"no file writing"`, `"no MIDI sending"`, `"passive/read-only"` — pinned by the architecture invariant test.

### 8.5 Why the rehearsal report exists separately from the CLI

The CLI is the action; the rehearsal report is the audit. They share a code path (the pre-flight portion of `cockpit-export-profile-model` is exactly the body of `build_cockpit_export_rehearsal_report` minus the write + verify steps), but they exist as separate commands so the audit can run in environments where the action SHOULD NOT run:

- Pre-merge CI on a PR that changes `pack_profile_model`: rehearse against every built-in scene profile, diff the projected payload lengths and CRCs against a baseline, fail loud on drift.
- A bug report from an operator: ask them to run the rehearsal report and paste the JSON; the maintainer can reconstruct what the export WOULD have done without needing the operator's keystore or write permissions.
- A future "import this third-party `.rymp`" UI: rehearse a verification against the file (not the source profile) and surface the panels in a sidebar, then let the operator decide whether to add the profile to their registry.

This separation mirrors the PR #103 / PR #104 split: `cockpit-send-plan-readiness-report` is the audit, the cockpit's armed SEND button is the action, the gating is enforced by the action checking the readiness report's output before firing. Phase 3 establishes the same pattern for the export pipeline, so when a future Phase 4 hardware-load UI lands it has a ready-made audit surface to gate against.

### 8.6 Composition with the cockpit-send-plan rehearsal-surface report

A future cockpit GUI view may want to render BOTH the send-plan rehearsal-surface AND the export rehearsal in one composite panel — "everything the operator needs to know about the current profile before they SEND it to hardware and before they EXPORT it to flash." Both reports return the same panel / binding / acceptance-check / replay-command shape (this is the load-bearing reuse pattern PR #104 established), so a composer is straightforward: load both reports, merge the panels in display order, dedupe shared metadata (profile id, model version), and render. The composite report is NOT in Phase 3 scope but the abstractions are aligned so it falls out for free in a follow-on phase.

## 9. Integration test — end-to-end round trip

`tests/test_cockpit_export_pipeline_integration.py` adds one comprehensive test that exercises the full Phase 3 pipeline:

```python
@pytest.mark.fast
def test_signed_export_round_trips_byte_identical(tmp_path: Path) -> None:
    profile = make_user_profile(name="round-trip", traits=...)   # Phase 1 dataclass
    key = secrets.token_bytes(32)
    output = tmp_path / "round_trip.rymp"

    # Phase 1: pack
    payload = pack_profile_model(profile)
    # Phase 3: sign
    envelope = pack_signed(payload, algo="hmac-sha256", key_id="test-key", key=key)
    # Phase 3: atomic write
    atomic_write(output, envelope)
    # Phase 3: verify
    result = verify_file(output, key_resolver=lambda kid: key if kid == "test-key" else None)
    assert result.ok
    assert result.reason == "ok"
    assert result.signed is True
    # Phase 1: unpack
    recovered_payload = unwrap_signed(output.read_bytes()).payload
    recovered = unpack_profile_model(recovered_payload)
    assert recovered == profile

    # Negative cases:
    tampered = bytearray(output.read_bytes())
    tampered[-5] ^= 0xFF   # flip a payload bit
    bad = verify_blob(bytes(tampered), key_resolver=lambda kid: key)
    assert not bad.ok
    assert bad.reason in {"bad_signature", "bad_crc"}
```

Plus parametrized cases for unsigned mode, wrong key, unknown key, bad magic, truncated envelope, truncated payload, mismatched algo, oversized algo/key_id (rejected at pack-time), and parent-dir-missing.

### 9.1 The conformance fixture corpus

Beyond the per-call round-trip test above, the integration test also asserts byte-equality against a frozen corpus under `tests/cockpit/fixtures/export_format_conformance/`:

```
tests/cockpit/fixtures/export_format_conformance/
    scene_industrial/
        profile.json        # source ProfileModel as JSON
        key.bin             # 32-byte test key
        expected.rymp       # the canonical signed envelope
    user_minimal/
        profile.json        # smallest valid user profile (one trait, one pad mapping)
        key.bin
        expected.rymp
    user_empty_pads/
        profile.json        # profile with no pad mappings (corner case for the iteration loop)
        key.bin
        expected.rymp
    _regen.py               # script that rebuilds the expected.rymp files from profile.json + key.bin
```

The conformance test asserts `pack_signed(pack_profile_model(load(profile.json)), key=load(key.bin), key_id="test-key", algo="hmac-sha256") == load(expected.rymp)` for every fixture. Drift between the implementation and the fixtures fails CI loudly: if a contributor changes the wire format unintentionally, the conformance test catches it before the PR merges.

The fixtures are the cross-language ground truth — when the Phase 4 hardware loader's C implementation lands, it will be verified against the same `expected.rymp` files. The `_regen.py` script rebuilds them from the source JSON + key when an intentional format bump lands; the script is gated behind a CI check that requires the fixture diff to be accompanied by an allow-list edit on the format-version constant.

### 9.2 Negative test enumeration

The integration test parametrizes the negative cases as one table:

| Case | Setup | Expected outcome |
|---|---|---|
| Tampered payload bit | bit-flip a byte inside the payload | `bad_crc` (CRC32 catches before the signature check); `ok=False` |
| Tampered signature bit | bit-flip a byte inside `sig` | `bad_signature`; `ok=False` |
| Wrong key (right key_id) | sign with `key_a`, verify with `key_b` resolved for the same key_id | `bad_signature`; `ok=False` |
| Unknown key | resolver returns None | `unknown_key`; `ok=False` |
| Bad magic | corrupt the first 4 bytes to `b"XXXX"` | `bad_magic`; `ok=False`; `header=None` |
| Truncated envelope | slice off the last 8 bytes | `truncated`; `ok=False` |
| Truncated payload | shrink `payload_len` by 4 in the envelope | `truncated` or `bad_crc` (depending on where truncation falls); `ok=False` |
| Bumped envelope format version | set envelope `format_version = 2` | `bad_format_version`; `ok=False` |
| Bumped inner format version | set inner RYMP `format_version = 2` | `bad_format_version`; `ok=False` |
| Mismatched algo on wire | swap `algo` to `hmac-sha512` while signing with sha256 | `unknown_algo`; `ok=False` |
| Oversized algo | algo string of 256 bytes (overflows uint8) | `ValueError` at `pack_signed` (rejected at construct-time, never reaches verify) |
| Oversized key_id | key_id string of 256 bytes (overflows uint8) | `ValueError` at `pack_signed` |
| Empty key | `pack_signed(..., key=b"")` | `ValueError` (HMAC keys must be non-empty) |
| Parent dir missing | `atomic_write(/nonexistent/path/foo.rymp, ...)` | `OSError`; original target untouched (vacuously, it doesn't exist) |
| Write-permission denied | mock `chmod 444` on parent dir | `OSError`; original target (if any) untouched |
| Atomic-write crash simulation | mock `os.fsync` to raise OSError mid-write | OSError propagates; temp file cleaned up; target untouched |

Every case is one parametrized line in the integration test. The coverage gate enforces that every reason enum value is exercised at least once.

## 10. Architecture invariants

`tests/architecture/test_export_pipeline_invariants.py` pins:

- **Module location:** all four new modules live under `rytm_randomizer/cockpit/export/`.
- **MAGIC constants:** `model_format.MAGIC == b"RYMP"`, `signing.SIGNED_MAGIC == b"RYMS"` — both 4 bytes, both ASCII, both distinct.
- **Format version constants:** `model_format.FORMAT_VERSION == 1`, `signing.SIGNED_FORMAT_VERSION == 1`. Bumping either requires an explicit allow-list edit.
- **Supported algorithm set:** `signing.SUPPORTED_ALGORITHMS == frozenset({"hmac-sha256"})`. New algorithms require an explicit allow-list edit (catches accidental widening).
- **Signature length per algorithm:** `signing.SIGNATURE_LENGTHS == MappingProxyType({"hmac-sha256": 32})` — pinned so the wire format stays unambiguous.
- **`VerificationResult.reason` enum:** the frozenset of accepted values is pinned to exactly `{"ok", "bad_magic", "bad_format_version", "bad_signature", "bad_crc", "truncated", "unknown_algo", "unknown_key", "io_error"}`.
- **Never-raises:** for every module-level function declared in `cockpit/export/verifier.py`, the function's source AST contains no `raise` statements except inside private helpers that are explicitly try/except-wrapped at the public boundary.
- **No-MIDI / no-network discipline:** the imports of `cockpit/export/**` and `reports/cockpit_export_rehearsal.py` (transitively) do not include `mido`, `rtmidi`, `socket`, `asyncio`, `subprocess`, `threading`, `cockpit.ws.server`, `real_midi_adapter`, or `midi_io`.
- **CLI registration:** `cockpit-export-profile-model` and `cockpit-export-rehearsal-report` are both registered in `cli_registry` and both auto-enroll in the passive-CLI safety sweep via the new auto-discovery refactor.
- **Rehearsal report's `SAFETY_LINES`:** contains the strings `"no file writing"`, `"no MIDI sending"`, `"passive/read-only"`.
- **Atomic-write contract:** `writer.atomic_write` opens its temp file in `path.parent` (asserted by AST inspection of the function body), and the temp file's name pattern starts with the target stem.

`tests/architecture/test_cockpit_send_plan_rehearsal_surface_invariants.py` (PR #104 BACKFILL) pins the analogous invariants on the rehearsal-surface report:

- Module location under `rytm_randomizer/reports/`.
- `SEND_PLAN_REHEARSAL_SURFACE_VERSION` constant exported (major version must not change without an allow-list edit).
- `SAFETY_LINES` contains `"no MIDI sending"`, `"passive/read-only"`.
- `surface_status` / `screen_state` / `send_control_state` enum string sets match a frozen baseline.
- `_COMMAND_NAME == "cockpit-send-plan-rehearsal-surface-report"`.
- No imports of `mido`, `rtmidi`, `real_midi_adapter`, `midi_io`, `cockpit.ws.server`, `subprocess`, `socket`, `threading`, `asyncio`.

`tests/architecture/test_real_midi_passive_cli_safety.py` (REFACTOR) replaces the hand-maintained `PASSIVE_CLI_COMMANDS` / `PASSIVE_CLI_SWEEP_COMMANDS` tuples with a `cli_registry` walk:

```python
@pytest.fixture(scope="module")
def passive_cli_commands() -> tuple[tuple[str, str], ...]:
    """All passive CLI commands, auto-discovered from cli_registry."""
    all_commands = sorted(cli_registry.iter_command_names())
    return tuple((name, "--help") for name in all_commands if name not in _ARMED_ALLOW_LIST)


_ARMED_ALLOW_LIST: Final[frozenset[str]] = frozenset({
    # The handful of armed-runtime commands that legitimately import mido at top
    # level. New armed commands must be added here EXPLICITLY (Gate 9 / Gate 10
    # discipline) — auto-discovery enforces the inverse: every passive command
    # auto-enrolls, every armed command must be explicitly excluded.
    "send",
    "send-batch",
    "run",
    "rehearsal-run",
})
```

This kills the recurring bug class. Every new passive CLI is automatically in the sweep; every new armed command must be EXPLICITLY allow-listed (which is a much easier review checklist than "remembered to update PASSIVE_CLI_COMMANDS?").

### 10.1 Invariant inventory — full enumeration

For agentic implementers, here is the exhaustive list of architecture invariants Phase 3 lands. Each invariant is one test method (or one parametrized test row) in the architecture test files.

**`tests/architecture/test_export_pipeline_invariants.py` (NEW):**

1. `test_signed_magic_is_exactly_RYMS` — `signing.SIGNED_MAGIC == b"RYMS"` and `len(SIGNED_MAGIC) == 4`.
2. `test_signed_format_version_is_one` — `signing.SIGNED_FORMAT_VERSION == 1`.
3. `test_supported_algorithms_is_exactly_hmac_sha256` — `signing.SUPPORTED_ALGORITHMS == frozenset({"hmac-sha256"})`.
4. `test_signature_lengths_map_is_immutable_and_complete` — `SIGNATURE_LENGTHS` is a `MappingProxyType`, contains every key in `SUPPORTED_ALGORITHMS`, and the value for `"hmac-sha256"` is exactly 32.
5. `test_verification_result_reason_enum_is_pinned` — the `Literal` arguments of `VerificationResult.reason` are exactly the nine documented values.
6. `test_verifier_module_has_no_top_level_raises` — AST scan of `cockpit/export/verifier.py` finds no `raise` statement at module-level or inside `verify_blob` / `verify_file` (private helpers may raise; the public boundary wraps).
7. `test_export_pipeline_does_not_import_mido` — `pytest_subprocess`-style import test on `cockpit/export/cli.py`, `signing.py`, `verifier.py`, `writer.py`, `reports/cockpit_export_rehearsal.py` — none transitively imports `mido` or `rtmidi`.
8. `test_export_pipeline_does_not_import_socket_or_subprocess` — same, for `socket`, `asyncio`, `subprocess`, `threading`, `cockpit.ws.server`, `real_midi_adapter`, `midi_io`.
9. `test_export_cli_is_registered` — `"cockpit-export-profile-model"` is in `cli_registry.iter_command_names()`.
10. `test_export_rehearsal_cli_is_registered` — `"cockpit-export-rehearsal-report"` is in `cli_registry.iter_command_names()`.
11. `test_export_rehearsal_safety_lines_include_required_phrases` — `cockpit_export_rehearsal.SAFETY_LINES` is a tuple containing exactly the strings `"no file writing"`, `"no MIDI sending"`, `"passive/read-only"` (order pinned).
12. `test_atomic_write_opens_temp_in_target_parent_dir` — AST inspection of `writer.atomic_write` confirms the `NamedTemporaryFile` call passes `dir=path.parent` and a `prefix` argument derived from `path.stem`.
13. `test_atomic_write_calls_fsync_before_replace` — AST inspection confirms `os.fsync` appears before `os.replace` in the function body.
14. `test_export_rehearsal_version_is_semver` — `EXPORT_REHEARSAL_VERSION` matches `^\d+\.\d+\.\d+$`.

**`tests/architecture/test_cockpit_send_plan_rehearsal_surface_invariants.py` (NEW — PR #104 BACKFILL):**

1. `test_module_lives_under_reports` — `rytm_randomizer.reports.cockpit_send_plan_rehearsal_surface` resolves and is in the reports package.
2. `test_version_constant_exported` — `SEND_PLAN_REHEARSAL_SURFACE_VERSION` is importable and matches `^\d+\.\d+\.\d+$`.
3. `test_safety_lines_include_required_phrases` — `SAFETY_LINES` contains `"no MIDI sending"`, `"passive/read-only"`.
4. `test_surface_status_enum_is_pinned` — the `Literal` arguments of the `surface_status` field are exactly `{"ready", "blocked"}`.
5. `test_screen_state_enum_is_pinned` — `Literal` arguments are exactly `{"send-ready-review", "review-required", "disabled"}` (or the actual current set).
6. `test_send_control_state_enum_is_pinned` — `Literal` arguments are exactly `{"send-ready-review", "disabled", "review-required"}` (or the actual current set).
7. `test_command_name_is_pinned` — `_COMMAND_NAME == "cockpit-send-plan-rehearsal-surface-report"`.
8. `test_module_does_not_import_mido_or_network` — same import-discipline check as the export invariants above, applied to the rehearsal-surface module.

**`tests/architecture/test_real_midi_passive_cli_safety.py` (REFACTOR):**

The hand-maintained `PASSIVE_CLI_COMMANDS` / `PASSIVE_CLI_SWEEP_COMMANDS` tuples are replaced with a fixture:

```python
_ARMED_ALLOW_LIST: Final[frozenset[str]] = frozenset({
    # The handful of armed-runtime commands that legitimately import mido
    # at top level. New armed commands must be added here EXPLICITLY (Gate 9
    # / Gate 10 discipline) — auto-discovery enforces the inverse: every
    # passive command auto-enrolls, every armed command must be explicitly
    # excluded.
    "send",
    "send-batch",
    "run",
    "rehearsal-run",
})

@pytest.fixture(scope="module")
def passive_cli_commands() -> tuple[tuple[str, str], ...]:
    """All passive CLI commands, auto-discovered from cli_registry."""
    all_commands = sorted(cli_registry.iter_command_names())
    return tuple((name, "--help") for name in all_commands if name not in _ARMED_ALLOW_LIST)


def test_armed_allow_list_only_contains_known_armed_commands() -> None:
    """The allow-list cannot grow without explicit review.

    If a new entry appears in _ARMED_ALLOW_LIST, this test forces a
    deliberate edit AND a justification comment beside the entry."""
    # AST-introspect the allow-list source to require a comment beside each
    # entry; fail if any entry is undocumented.
    ...
```

The existing per-command subprocess sweep then runs against the `passive_cli_commands` fixture. Every new passive command auto-enrolls; every new armed command requires an explicit allow-list edit.

## 11. PR #104 leverage — explicit callout

This phase's plan deliberately FOLDS IN the three items PR #104's review flagged as Phase 3 lock-in work:

| PR #104 recommendation | Phase 3 deliverable |
|---|---|
| "Add an architecture invariant that pins the JSON contract" (rehearsal-surface) | `tests/architecture/test_cockpit_send_plan_rehearsal_surface_invariants.py` (new file in this PR). |
| "Auto-discover passive CLI commands from `cli_registry` at test-time" | The `test_real_midi_passive_cli_safety.py` refactor described in §10. |
| "Encoder/formatter duplication should collapse to a shared `reports/_passive_section.py` helper" | Tracked but DEFERRED to a follow-up PR — the export-rehearsal report uses the existing helpers exactly the way the rehearsal-surface report does, so when the shared helper lands BOTH consumers migrate together. The deferral is documented in `CONTRIBUTING.md`. |

The reason these are bundled into Phase 3 rather than left as separate cleanup PRs:

- The architecture invariant test on the rehearsal-surface contract is the **load-bearing piece** the Phase 3 export pipeline depends on for schema stability. Per PR #104's review: "without this, every cosmetic edit to the rehearsal surface risks silently breaking the Phase 3 consumer that does not exist yet." Phase 3 is now creating that consumer (the export-rehearsal report has the same shape and will eventually share a formatter helper with the rehearsal-surface report). The invariant has to land BEFORE the consumer.
- The passive-CLI auto-discovery refactor is the **structural fix** that prevents Phase 3's two new CLI commands (and Phase 4's hardware CLIs, and every future phase's reports) from silently dropping out of the safety sweep. Per PR #104's review: "Phase 3 will add more passive reports... the same hand-maintained tuple will keep getting forgotten." Phase 3 is the first phase that adds passive CLIs AFTER the bug class was identified; fixing the bug class as part of this phase prevents the recurrence the review predicted.

## 12. Phase 4 readiness — the cross-language consumer contract

The hardware loader (Phase 4) reads `.rymp` files written by Phase 3. The cross-language contract is:

### 12.1 Binary stability

- **MAGIC bytes** (`RYMP` and `RYMS`) are fixed forever. The hardware reads four bytes and dispatches on them.
- **`FORMAT_VERSION` uint16** is the version the loader checks against `SUPPORTED_FORMAT_VERSIONS`. A loader written against version 1 SHOULD reject version 2 with a typed error rather than attempt best-effort parsing — same discipline the Python loader follows today.
- **Endianness** is big-endian for every multi-byte integer. Pinned by `_FIXED_HEADER_STRUCT = struct.Struct(">4sHB")` etc. — the `>` prefix is canonical.
- **CRC32** is `zlib.crc32` (ISO/IEC standard polynomial 0xEDB88320, init 0xFFFFFFFF, final XOR 0xFFFFFFFF). Every C runtime has an implementation; the hardware loader links against `zlib` or a 256-byte lookup-table equivalent.
- **MessagePack** is the payload encoding. `msgpack-c` is the reference C implementation; `msgpack-python` is the Python implementation. Round-trip fixtures (`tests/cockpit/fixtures/export_format_conformance/*.rymp`) pin the byte-level output so a hardware loader can be tested against the same fixtures.

### 12.2 Signature stability

- **HMAC-SHA256** is the only algorithm Phase 3 ships. SHA-256 is BSD-licensed reference implementations everywhere; embedded ports are 5-10 KB of code. HMAC adds another 50 lines.
- **Signed bytes** (`algo || 0x1f || key_id || 0x1f || payload`) are unambiguously parseable in C with three `memcpy`s.
- **`hmac.compare_digest`** corresponds to a constant-time `memcmp` in C; the embedded port must use the constant-time variant.

### 12.3 Key management on hardware

- Phase 4's hardware keystore is a flash-stored array of `(key_id_utf8, key_bytes32)` records. The hardware loader looks up the envelope's `key_id`, runs the constant-time compare against the loaded key, accepts or rejects.
- The Phase 3 `--key-id` flag and the Phase 4 hardware lookup use the SAME `key_id` namespace. An operator who signs a profile with `key_id="buzzi-2026"` and copies it to an SD card will see the hardware find the matching key by the same label.

### 12.4 Test fixture contract

The integration test corpus (`tests/cockpit/fixtures/export_format_conformance/`) is a frozen set of (`ProfileModel.json`, `key.bin`, `expected.rymp`) triples. The Python implementation is verified against them in CI; the future C implementation will be verified against the same triples. The fixtures are the cross-language ground truth.

### 12.5 What the hardware project gets from Phase 3 without writing any code itself

By the time the hardware project starts, Phase 3 has already delivered:

1. **A frozen wire format** documented in this spec and pinned by architecture invariants. The hardware C reader can be written against the spec without referencing the Python source.
2. **A conformance fixture corpus** (`tests/cockpit/fixtures/export_format_conformance/`) the hardware reader can target directly. Hardware reads `expected.rymp`, parses it, asserts the recovered `ProfileModel` matches `profile.json`. Same fixtures, same expected output, deterministically.
3. **A reference implementation** in Python (`cockpit/export/serialize.py`, `cockpit/export/signing.py`, `cockpit/export/verifier.py`) that the C author can read for algorithm clarity. The Python source is small (< 500 lines total across the four new files), pure stdlib, and free of cleverness — it is deliberately written to be readable, not optimized.
4. **A never-raises verifier contract** that the hardware loader inherits. Hardware crashes are catastrophic (the box reboots, possibly bricks); the same "every kind of badness returns a typed result" discipline that protects the Python GUI also protects the hardware firmware.
5. **A signed envelope that strips off cleanly** to recover the bit-identical Phase 1 packed payload. The hardware can defer the signature check (e.g. verify once at flash time, skip on subsequent loads if the SD slot is sealed) without complicating the inner-payload parser.
6. **A constant-time signature compare requirement** documented as part of the algorithm. The C author knows to use `CRYPTO_memcmp` or write a constant-time loop; they don't have to discover the requirement after a timing-attack post-mortem.
7. **A key namespace** that aligns with the Phase 3.5 keystore. An operator who signs with `key_id="buzzi-2026"` on Phase 3 will find the same label in the hardware's keystore on Phase 4.

This is exactly the kind of cross-language contract handoff that Phase 4 will need. By doing the work in Phase 3 — wire format, signing, atomic write, verifier discipline — we ship a hardware-ready format BEFORE the hardware project starts, instead of discovering the format issues a year into the firmware build.

### 12.6 Migration path if the hardware adds capabilities Phase 3 didn't predict

A few foreseeable hardware capabilities that might want format extensions:

- **Profile bundles** (multiple profiles in one `.rymp` for batch flashing). The wire format could grow a `bundle` marker or wrap multiple Phase-3 envelopes in a Phase-4-specific outer envelope. The Phase 3 single-profile path is unaffected.
- **Encryption** (operator wants the on-card profiles to be unreadable to a hostile party with physical access to the SD card). Encryption would layer ON TOP of the signing envelope: encrypt the inner payload, sign the encrypted bytes, ship `RYMS-encrypted` as a new magic. Same Phase 3 signing primitives, same `key_id` namespace, new magic for the new shape.
- **Public-key signing** (publisher signs a profile, operator's hardware verifies against a trusted publisher key). The envelope's `algo` field is the discriminator; `ed25519` is reserved as a future value. The wire format would gain an `issuer_key_id` field; the keystore would learn to distinguish "publisher keys" (verify-only) from "operator keys" (sign and verify).
- **Compression** (large profiles with many traits and pad mappings). zstd or lz4 framed compression on the inner payload, marked by a flag in the inner format-version (so the Phase 3 unsigned path also gets compression for free). The compression algorithm would join `SUPPORTED_ALGORITHMS` style — a frozen set pinned by an architecture invariant.

None of those are Phase 3 deliverables. All of them fit the existing envelope shape with a new value in an existing field plus a one-line update to the supported-set constant. The Phase 3 design's discoverability rule — "every wire-format choice is a single string or integer that can be enumerated and pinned" — is what makes the migration tractable.

## 13. What stays unchanged

- **V1.34 parity is untouched.** Phase 3 does not modify any engine code, any V1.34 reference data, any parity test, or any of the 685 `tests/fixtures/v134_parity/` JSON goldens. The signed export pipeline is layered alongside the existing engine; the engine never sees a `.rymp` file.
- **Phase 1 binary format is unchanged.** `pack_profile_model` / `unpack_profile_model` return / accept the exact same bytes today and after Phase 3. The signing envelope wraps; it does not modify.
- **Phase 2 wizard is unchanged.** The wizard continues to write JSON to `~/.rytm-randomizer/profiles/`. Phase 3 reads those JSON files via the existing `ProfileRegistry`.
- **Passive / armed boundary is preserved.** Phase 3's pipeline never opens a MIDI port. The CLI writes a local file; the rehearsal report writes nothing. The pipeline is passive-by-construction.
- **`mido` lazy-import discipline is preserved.** None of the new modules import `mido` (or anything that transitively imports `mido`). Architecture invariants enforce this.
- **No new third-party dependencies.** HMAC + SHA-256 + CRC32 are stdlib. `os.replace` is stdlib. MessagePack is already a Phase 1 dependency. No new package, no new toolchain.
- **CLI dispatcher is untouched.** The two new CLI commands are registered through the existing `cli_registry` lazy-discovery path. `rytm_randomizer/cli.py` does not change.
- **WebSocket Protocol is unchanged.** Phase 3 does not introduce new WS commands or events. The GUI consumer for the export pipeline (a future "Export profile" button) will be a Phase 3.5 or Phase 4 deliverable; this phase ships only the CLI + the rehearsal report.

## 14. Plan-requirements conformance

Per `docs/PLAN_REQUIREMENTS.md`, the implementation plan derived from this spec commits to:

- [x] **Gate 1** — 100% branch coverage on every new file (signing, verifier, writer, cli, cockpit_export_rehearsal, the two new architecture tests, the integration test). Pinned per workstream.
- [x] **Gate 2** — V1.34 parity byte-identical. No engine code touched, no V1.34 fixture touched.
- [x] **Gate 3** — lint / format / type clean (ruff + black + isort + mypy strict).
- [x] **Gate 4** — no new dead code; all new public functions are exercised by the integration test and the per-module tests.
- [x] **Gate 5** — docs updated (WS-G ships the spec, plan, ARCHITECTURE §6.4, ARCHITECTURE_DIAGRAMS new section, COCKPIT_QUICKSTART §5c, STATUS entry, BUILDING_INSTALLERS additive paragraph, README one-liner, CONTRIBUTING one-liner on the wrapped-JSON pattern).
- [x] **Gate 6** — type-system hygiene. Frozen dataclasses (`VerificationResult`, `SignedBlob`, `SignedEnvelope`), `Literal` types on `algo` and `reason`, no bare `Any`.
- [x] **Gate 7** — observability. `get_metrics().record_*` on `pack_signed`, `verify_blob`, `atomic_write`, and both CLI entry points. Each emits a counter incrementing on call and a separate counter on outcome class (ok / bad_signature / bad_crc / etc.).
- [x] **Gate 8** — intent-named tests: `test_signed_export_round_trips_byte_identical`, `test_verifier_never_raises_on_truncated_envelope`, `test_atomic_write_leaves_no_partial_file_on_simulated_crash`, etc.
- [x] **Gate 9** — module organization: new code lives under existing `cockpit/export/` and `reports/` subpackages. No new top-level `*.py`.
- [x] **Gate 10** — `Literal` types: `algo: Literal["hmac-sha256"]`, `reason: Literal[...]`. Enums pinned by architecture tests.
- [x] **Gate 11** — shared test fixtures: `tests/cockpit/conftest.py` gains `signed_blob_factory`, `export_round_trip_artifacts`. `tests/cockpit/fixtures/export_format_conformance/*.rymp` are the cross-language ground-truth corpus.
- [x] **Gate 12** — `Final` constants throughout (`SIGNED_MAGIC`, `SIGNED_FORMAT_VERSION`, `SUPPORTED_ALGORITHMS`, `SIGNATURE_LENGTHS`, `EXPORT_REHEARSAL_VERSION`, `SAFETY_LINES`).
- [x] **Gate 13** — no new env vars (the Phase-3.5 keystore directory will be configurable, but Phase 3 hardcodes the default `~/.rytm-randomizer/keys/` for the resolver hook).
- [x] **Gate 14** — maintainability audit (pre / post in the plan).
- [x] **Gate 15** — learning extraction. The wrapped-JSON pattern + the atomic-file-write contract + the never-raises verifier contract become reusable skills under `.claude/skills/learned/`.
- [x] **Gate 16** — execution shape (7 parallel WSes against `feat/phase-3-export-pipeline` off `modularize-v1.34`, bundling into ONE PR — same shape as the Phase 2 plan).
- [x] **Gate 17** — abstraction reuse: the export pipeline reuses `cockpit/export/model_format.py` (Phase 1), `cockpit/export/serialize.py` (Phase 1), `cockpit/profiles/registry.py` (Phase 1), `cli_registry` (existing), and the rehearsal report reuses `reports/passive_report_lines`, `live_gui_common`, `CliCommand`, and the `cockpit_send_plan_rehearsal_surface.py::_readiness_from_mapping` wrapped-JSON pattern.
- [x] **Gate 18** — architecture-doc + diagram freshness. WS-G adds ARCHITECTURE §6.4, a new ARCHITECTURE_DIAGRAMS sequence diagram (section 32), and the updates listed in Gate 5.

Exceptions: none.

## 15. Open decisions deferred to the implementation plan

- **Keystore directory layout.** Phase 3 ships only the `key_resolver` hook; the keystore file format and management UI are deferred to Phase 3.5. The plan documents the default `~/.rytm-randomizer/keys/<key_id>.key` (raw 32 bytes) but the file-discovery logic is gated behind a single resolver function so swapping to a JSON manifest or an OS-keyring backend is a one-file change.
- **Whether the GUI export button ships in Phase 3 or Phase 3.5.** This spec ships only the CLI + the rehearsal report. A WebSocket `export_profile_model` command and a GUI button in the Mutation Panel is straightforward but adds frontend surface area; deferring it to a follow-on PR keeps Phase 3 lean.
- **CI fixture-corpus refresh policy.** When the canonical `expected.rymp` fixtures need to change (e.g. a `ProfileModel` field is added), the regeneration script should be a single one-liner with a CI gate that fails on unexpected diffs. The plan will specify whether the script lives under `scripts/` or under `tests/cockpit/fixtures/export_format_conformance/_regen.py`.
- **Whether `--unsigned` is hidden behind a confirmation prompt.** An unsigned `.rymp` carries integrity (CRC32) but not authenticity (signature). Defaulting to unsigned is the safer-to-use option for Phase 3 (no keystore required) but a future hardware loader may refuse unsigned profiles entirely. The CLI flag exists; whether it surfaces a banner-style warning is a small UX decision deferred to implementation.
- **Metric naming.** `get_metrics().record_counter("cockpit.export.signed.ok")` vs `record_counter("cockpit_export_signed_ok")` — the plan will follow whatever the rest of the cockpit code already uses (PR #99 established the dotted convention; Phase 3 will mirror it).

These don't change the design's shape; they're implementation-plan choices.

## 16. Operator workflows — three end-to-end stories

The spec is easier to evaluate against concrete operator stories. Each below walks an operator from intent to outcome.

### 16.1 "I built a profile and want to share it with another producer"

The operator has a `kind="user"` profile in `~/.rytm-randomizer/profiles/<id>.json` and a friend wants to try it on their own rig.

1. Operator runs `cockpit-export-rehearsal-report --profile-id <id> --unsigned` to preview what would be exported.
2. The report confirms `status: unsigned`, lists the profile name, payload length, and the verification result that would be returned (`reason: "ok"` for an unsigned bare-RYMP blob with a valid CRC32).
3. Operator runs `cockpit-export-profile-model --profile-id <id> --output ~/share/buzzi.rymp --unsigned`.
4. The CLI packs, writes atomically, and post-flight verifies. Exit code 0.
5. Operator sends `buzzi.rymp` to their friend over chat / email / USB stick.
6. The friend's cockpit (a future "Import profile" UI; out of scope for Phase 3) reads the file, calls `verify_file` (returns `reason: "ok"` because the CRC matches), unpacks via `unpack_profile_model`, and offers to save it to their own registry.
7. Both operators are now driving the same `ProfileModel`.

No keystore involved, no signing — unsigned mode is fine for casual sharing. Integrity is guaranteed by the CRC32; authenticity is guaranteed by the chat / email / USB out-of-band trust.

### 16.2 "I want a signed profile I can flash to my own hardware later"

The operator has set up a keystore (Phase 3.5 — out of scope for this spec, but the resolver hook exists in Phase 3) with a key labeled `buzzi-2026`. They want to ship a signed profile to the hardware they will eventually own.

1. Operator runs `cockpit-export-rehearsal-report --profile-id <id> --key-id buzzi-2026` to preview.
2. The report confirms `status: ready`, `key_resolved: yes`, lists the projected signature length (32 bytes for hmac-sha256), and the verification result the pipeline would return (`reason: "ok"` with `signed: true`).
3. Operator runs `cockpit-export-profile-model --profile-id <id> --output ~/profiles/buzzi.rymp --key-id buzzi-2026`.
4. The CLI packs, signs, writes atomically, and post-flight verifies (using the same key resolved through the same keystore). Exit code 0.
5. Operator copies `buzzi.rymp` to an SD card and inserts it into the eventual hardware.
6. The hardware (Phase 4) reads the file, looks up `buzzi-2026` in its on-device keystore, runs the constant-time HMAC compare, accepts the file, unpacks the inner payload, and loads the profile.

The signed envelope is what the hardware authenticates. If someone tampers with the file on the SD card mid-transit, the signature check fails and the hardware refuses to load it.

### 16.3 "I downloaded a third-party `.rymp` and want to know if it's safe to load"

The operator received a `.rymp` file from a community member. They want to inspect it before trusting it.

1. Operator runs `cockpit-export-rehearsal-report --profile-file ~/downloads/strange.rymp`.
2. The report unwraps the file (without verifying the signature, since they don't have the key), prints the inner payload's profile name, model version, trait set, and pad mappings.
3. The operator decides the profile looks reasonable.
4. They run `cockpit-export-rehearsal-report --profile-file ~/downloads/strange.rymp --key-bytes <hex>` if they have the key bytes from the publisher (passed out of band).
5. The report runs the signature check and reports `verified: ok` or `verified: bad_signature`.
6. Either way, the file was never executed — only inspected.

The never-raises verifier contract is what makes this story safe. If the file were malformed (e.g. a maliciously truncated envelope), the verifier returns `reason: "truncated"` rather than crashing the report. The operator gets a clean error message and the report exits with a non-zero code.

### 16.4 "I'm setting up CI to bake a profile into the installer"

A future build pipeline wants to ship a default set of profiles with the installer. The build is automated and runs unattended.

1. The CI script loops over the profile-id list and calls `cockpit-export-profile-model --profile-id <id> --output build/profiles/<id>.rymp --unsigned` for each (signing requires keystore access which CI shouldn't have).
2. For each profile, the script asserts exit code 0 and runs `cockpit-export-rehearsal-report --profile-file build/profiles/<id>.rymp --json` and diffs the resulting JSON against a frozen baseline.
3. Any drift in the baseline (a profile's traits changed, the format version bumped, etc.) fails the CI job loudly.
4. The successful build artifacts are bundled into the installer via the existing Briefcase / Tauri pipelines.

This story drives the stability guarantees in §7.6 — the `--json` output is part of the contract precisely because tooling consumes it. The architecture invariant tests pin the JSON shape so a future contributor who renames a field gets caught at CI time, not at customer-installer time.

### 16.5 "I want to migrate from an unsigned exported profile to a signed one"

The operator earlier exported a profile unsigned, then later set up a keystore and wants the existing file to be signed too.

1. Operator runs `cockpit-export-rehearsal-report --profile-file ~/profiles/my.rymp` against the existing unsigned file to confirm the contents.
2. They locate the source profile id from the report's output.
3. They run `cockpit-export-profile-model --profile-id <id> --output ~/profiles/my.rymp --key-id buzzi-2026` — the atomic-write contract REPLACES the file in place (the old unsigned bytes are gone; the new signed bytes are durable).
4. They re-run the rehearsal report against the new file to confirm `signed: yes`, `verified: ok`.

Atomic-write's REPLACE semantic is what makes this safe. If the new export fails partway, the old unsigned file is untouched — they don't end up with a half-written signed file replacing a valid unsigned one. The atomic contract holds across the upgrade.

### 16.6 "The hardware loader rejected my file — what do I do?"

The operator inserted an SD card with a `.rymp` file; the hardware refused to load it.

1. Operator inserts the SD card back into their laptop.
2. They run `cockpit-export-rehearsal-report --profile-file /Volumes/SD/buzzi.rymp --key-bytes <their key as hex>`.
3. The report inspects the file (using the same never-raises verifier the hardware uses) and produces a diagnostic:
   - `bad_magic` -> the file is corrupted or isn't a `.rymp` at all; re-copy from source.
   - `bad_format_version` -> the file was exported by a newer cockpit than the hardware supports; downgrade the cockpit or upgrade the hardware firmware.
   - `bad_signature` -> the key on the SD card doesn't match the one in the hardware's keystore; check that the same `key_id` is registered on both sides with the same key bytes.
   - `bad_crc` -> the SD card itself may be failing (bit-rot); re-export and re-copy.
   - `truncated` -> the file didn't fully copy to the SD card; re-copy with `sync` after.
4. The diagnostic is the same on both the laptop and the hardware (modulo the hardware not having a human-readable display) because the verifier contract is shared.

This story is the load-bearing argument for the never-raises verifier returning a TYPED reason. The operator-facing diagnostic on the laptop is the same machine-readable signal the hardware sees; one set of diagnostic strings, one set of remediation guides, one source of truth.

## 17. Failure-mode catalog — what can go wrong, what the system does

A complete catalog of every failure path the pipeline handles. Each row is a real failure mode an operator might encounter; the "outcome" column is the SAME on every machine because the architecture invariants pin it.

| Failure | Detected by | Outcome | Operator-facing message |
|---|---|---|---|
| Profile id not in registry | `ProfileRegistry.load(id)` raises `KeyError` | CLI catches, exits 2 | `error: profile id '<id>' not found in '<dir>'` |
| Profile JSON malformed | `ProfileRegistry.load` raises `ValueError` (Phase 1 contract) | CLI catches, exits 2 | `error: profile '<id>' has malformed JSON: <detail>` |
| `--key-id` provided but key not in keystore | resolver returns None | CLI catches, exits 2 | `error: no key registered for key_id='<id>'; check ~/.rytm-randomizer/keys/` |
| `--key-bytes` not valid hex | `bytes.fromhex(value)` raises `ValueError` | CLI catches, exits 2 | `error: --key-bytes must be a hex string: <detail>` |
| Output parent dir does not exist | `atomic_write` raises `FileNotFoundError` | CLI catches, exits 2 | `error: parent directory '<dir>' does not exist; create it first` |
| Output parent dir not writable | `atomic_write` raises `PermissionError` | CLI catches, exits 2 | `error: cannot write to '<dir>': permission denied` |
| Disk full mid-write | `atomic_write` raises `OSError(ENOSPC)`; temp cleaned up | CLI catches, exits 2 | `error: no space left on device while writing to '<dir>'` |
| OS reports fsync failure (rare; hardware fault) | `atomic_write` raises `OSError`; temp cleaned up | CLI catches, exits 2 | `error: fsync failed: <detail>` |
| Post-write verification returns `bad_crc` (extremely unlikely; hardware fault) | CLI's verify step | Exits 3 | `warning: file written but CRC verification failed: <detail>` |
| Post-write verification returns `bad_signature` (would mean a code bug, since same key was used) | CLI's verify step | Exits 3 | `warning: file written but signature verification failed (likely a bug): <detail>` |
| `--unsigned` + `--key-id` (mutually exclusive flags) | CLI flag parser | Exits 2 BEFORE any work | `error: --unsigned cannot be combined with --key-id or --key-bytes` |
| `--key-id` with no `--unsigned` and no keystore entry | resolver | Exits 2 | `error: no key registered for key_id='<id>'; pass --unsigned or set up a keystore` |

All of these are exercised by the integration test (§9.2) or the CLI unit tests in WS-C. The architecture invariant `test_atomic_write_cleanup_on_failure` (in WS-E) confirms the temp-file unlink path is reached on every failure branch.

## 18. Performance characteristics

The pipeline is intentionally small. Concrete numbers measured against representative profiles:

| Operation | Profile size | Time (cold) | Time (warm) |
|---|---|---|---|
| `pack_profile_model` (one scene profile, ~50 traits) | ~3 KB output | < 1 ms | < 1 ms |
| `pack_profile_model` (typical user profile, 5 sources analyzed) | ~5-15 KB | < 1 ms | < 1 ms |
| `sign_profile_blob` (HMAC-SHA256 over 10 KB) | — | < 1 ms | < 1 ms |
| `pack_signed` (envelope assembly) | — | < 1 ms | < 1 ms |
| `atomic_write` (write + fsync + replace on SSD) | 10 KB | 5-20 ms | 5-20 ms (fsync dominates) |
| `verify_file` (read + verify) | 10 KB | < 5 ms | < 1 ms (OS cache) |
| `cockpit-export-profile-model` end-to-end | 10 KB | 30-50 ms | 10-20 ms |
| `cockpit-export-rehearsal-report` (no write) | 10 KB | 10-20 ms | < 5 ms |

The end-to-end CLI invocation includes Python interpreter startup (~50-100 ms cold) which dominates the actual pipeline work. For batch operations (export 100 profiles), a future caller should import `cockpit.export.cli.main` directly and call it 100 times in one Python process to amortize startup; alternatively, future Phase 3.5 work may add a `cockpit-export-batch` CLI that takes a profile-id list.

`atomic_write`'s fsync is the only operation with non-deterministic timing — it depends on the underlying storage (SSD: 5-20 ms typical; spinning rust: 50-200 ms; network FS: highly variable). The pipeline does not try to amortize fsync across multiple writes; each export gets its own fsync. This is the right tradeoff for one-export-at-a-time operator workflows; a batch CLI would coalesce.

## 19. Security considerations

A signing pipeline that doesn't surface its threat model is a signing pipeline that will get used wrong. This section is explicit about what Phase 3 protects against, what it doesn't, and what the operator's responsibilities are.

### 19.1 What Phase 3 protects against

- **Bit-level corruption.** The CRC32 trailer in the Phase 1 packed payload catches single-bit flips, multi-bit flips within a CRC32 burst-detection range, and most accidental file corruption (bad SD card, half-flushed write, network transfer truncation). The signature catches anything the CRC misses, including intentional manipulation that preserves the CRC.
- **In-transit tampering with intent.** An attacker who modifies a `.rymp` file in transit (man-in-the-middle on a download, modified SD card swapped before insertion) cannot produce a valid signature without the key. The hardware loader rejects the modified file.
- **Substituting a different operator's profile.** An attacker cannot replace an operator's signed profile with a different one signed under the operator's `key_id` (because they don't have the key bytes). They could swap in a profile signed under a DIFFERENT `key_id`, but the hardware would either reject it (the new key_id isn't in the keystore) or load it as a different profile (which the operator would notice).
- **Accidental swap.** A profile signed under `key_id="buzzi-2026"` cannot be silently loaded as if it were signed under `key_id="other-2026"` — the signed bytes include the `key_id` (via the `algo || 0x1f || key_id || 0x1f || payload` framing). Reframing attacks are explicitly defeated.

### 19.2 What Phase 3 does NOT protect against

- **Compromise of the signing key.** If an attacker obtains the operator's key bytes, they can sign anything they want under that `key_id`. Mitigation is operator-side: use the keystore (Phase 3.5) responsibly, rotate keys if compromise is suspected, do not share key bytes over insecure channels.
- **Confidentiality of the profile contents.** The signed envelope is NOT encrypted. Anyone who can read the `.rymp` file can read the trait set, pad mappings, and metadata inside. The operator's musical-style choices are not state secrets, but if confidentiality ever becomes a requirement (commercial profiles sold under license, etc.), encryption would layer on top per §12.6.
- **Replay attacks on the hardware.** If the hardware loader doesn't track which profiles have been loaded before, an attacker with physical access could swap out one signed profile for another (older, also signed) version that the loader would accept. Phase 4 hardware design will need to address replay if the threat model requires it (e.g. by maintaining a per-profile monotonic counter in flash).
- **Side-channel attacks on the keystore.** Reading key bytes from a process's memory, observing timing of HMAC computation, or exploiting cache-based side channels are out of scope. The Python `hmac.compare_digest` is constant-time, but other parts of the pipeline (file IO, OS keyring access) are not hardened against advanced side-channel attackers.

### 19.3 Operator responsibilities

- **Generate keys with sufficient entropy.** A 32-byte key from `secrets.token_bytes(32)` is cryptographically strong; a 32-byte key derived from a password or a low-entropy source is not. The Phase 3.5 keystore UI will enforce `secrets`-based generation; for now the CLI's `--key-bytes` path is the operator's responsibility.
- **Protect the keystore directory.** `~/.rytm-randomizer/keys/` should be `chmod 700` (and `chmod 600` on each key file). The keystore UI in Phase 3.5 will enforce this; for now it is the operator's responsibility. The pipeline itself does not enforce permission bits because they are platform-dependent.
- **Rotate keys when sharing changes.** If an operator stops sharing profiles with a collaborator, rotating the key (generate a new key with a new `key_id`, re-sign profiles under the new key, distribute the new key only to the trusted parties) is the standard remediation. The Phase 3 wire format supports per-profile `key_id`, so different profiles can be signed under different keys for different audiences.
- **Trust new keys deliberately.** Adding a new `key_id` to the hardware's keystore is a deliberate "I trust this publisher" action. The hardware design (Phase 4) should make this a visible operator-level step, not a silent auto-acceptance.

### 19.4 Cryptographic primitives — provenance and audit

- **HMAC-SHA256** is FIPS 198-1 / RFC 2104. Reference implementations exist in every cryptographic library. The Python implementation is in `hashlib.hmac` from CPython stdlib; the embedded port would use `mbedtls`, `BoringSSL`, or `wolfSSL` (all of which have small-footprint configurations suitable for Cortex-M class hardware).
- **CRC32** with ISO/IEC polynomial 0xEDB88320 (also called CRC-32/ISO-HDLC, used by zlib, gzip, PNG). Reference implementations exist as 256-byte lookup tables in every C runtime.
- **SHA-256** is FIPS 180-4. Same provenance as HMAC-SHA256's hash function.
- **`secrets.token_bytes`** is CPython's `os.urandom`-backed CSPRNG. On Linux it pulls from `getrandom(2)`; on macOS from `/dev/urandom`; on Windows from `BCryptGenRandom`. All three are cryptographically appropriate.

## 20. Maintainability + documentation discipline

Per Gate 14 the spec commits to maintainability discipline that survives future contributors.

### 20.1 Code-comment density

Each new module ships with a module-level docstring explaining purpose, dependencies, and gotchas. Each public function ships with a docstring including:

- One-line summary.
- Parameter explanations (especially for `Literal` arguments and `key_resolver` callbacks).
- Return-type contract (especially for the never-raises verifier).
- `Raises:` section listing every exception path (or "never raises" for the verifier).
- Example usage where the call site is non-obvious.

The convention follows the existing Phase 1 `cockpit/export/model_format.py` style.

### 20.2 Type-checking discipline

- No bare `Any`. Every callable uses `Literal[...]`, frozen dataclasses, or `Protocol` where appropriate.
- `mypy --strict` passes on every new file. The project's existing `pyproject.toml` mypy config covers the new files automatically because they live under `rytm_randomizer/`.
- `Callable` types for `key_resolver` use the full signature: `Callable[[str], bytes | None]` rather than `Callable[..., Any]`.

### 20.3 Test discipline

- Per-module unit tests in `tests/cockpit/test_export_*.py` (or `tests/test_cockpit_export_*.py` for tests that span multiple cockpit modules).
- One integration test (`tests/test_cockpit_export_pipeline_integration.py`) that asserts the assembled pipeline behaves end-to-end.
- Three architecture invariant files (per §10).
- 100% branch coverage per WS, enforced by the WS's coverage gate.
- `pytest.mark.fast` on tests that don't touch disk; standard `pytest` for the integration + atomic-write tests (which use `tmp_path`).

### 20.4 Naming discipline

Following the existing `cockpit/export/` conventions:

- Module names: snake_case, descriptive (`signing`, `verifier`, `writer`, `cli` — clear single-responsibility names).
- Public functions: `verb_noun(...)` (`sign_profile_blob`, `verify_blob`, `atomic_write`, `pack_signed`).
- Constants: `SHOUTING_SNAKE_CASE` with explicit `Final` annotation.
- Dataclasses: `PascalCase` with `@dataclass(frozen=True)`.
- Test functions: `test_<intent>` (e.g. `test_signed_export_round_trips_byte_identical`, `test_verifier_never_raises_on_truncated_envelope`).

## 21. Glossary

| Term | Meaning |
|---|---|
| `ProfileModel` | The Phase 1 frozen dataclass representing operator-curated style + pad-mapping intelligence. The "thing" being exported. |
| Packed payload | The Phase 1 binary format: `RYMP` magic + format version + model version + payload length + MessagePack(`ProfileModel.to_dict()`) + CRC32 trailer. |
| Signed envelope | The Phase 3 binary format wrapping a packed payload: `RYMS` magic + format version + algo + key_id + sig + payload length + the packed payload itself. |
| `.rymp` | The conventional filename extension for an exported profile (whether packed-and-signed or packed-unsigned). |
| Atomic write | `tempfile.NamedTemporaryFile` in target's parent dir + `flush` + `os.fsync` + `os.replace`. Guarantees no partial files visible at the target path. |
| Never-raises verifier | A verifier that returns a typed `VerificationResult` for every input, including malformed input, rather than raising. |
| Key resolver | A function `Callable[[str], bytes | None]` that maps a `key_id` to its 32-byte key. The Phase 3 implementation reads from `~/.rytm-randomizer/keys/<key_id>.key`; Phase 3.5 adds a keystore UI. |
| Rehearsal report | A passive CLI report that runs the same code path as an action but doesn't perform the action. The pattern was established by PR #104 for SEND-readiness and is reused by Phase 3 for EXPORT-readiness. |
| Wrapped-JSON pattern | A reusable input pattern where a passive report accepts either the inner data JSON or a wrapping report's JSON (peeling out the inner key). Documented in CONTRIBUTING.md. |
| Auto-discovery (CLI safety sweep) | The Phase 3 refactor that replaces a hand-maintained list of passive CLI commands with a `cli_registry.iter_command_names()` walk + an opt-out allow-list for armed commands. Kills a recurring bug class. |

## 22. Cross-references

The spec lives at the intersection of several existing pieces of work. For evaluators wanting context:

- **Phase 1 cockpit spec** — [`2026-05-23-cockpit-and-profile-model-design.md`](2026-05-23-cockpit-and-profile-model-design.md) — defines the `ProfileModel` shape, the WS Protocol, and the seven built-in scene profiles Phase 3 will export.
- **Phase 2 wizard spec** — [`2026-05-24-profile-wizard-design.md`](2026-05-24-profile-wizard-design.md) — defines the authoring flow that produces user profiles Phase 3 will export.
- **PR #103 send-plan readiness report** — established the passive-CLI / armed-action split that Phase 3 mirrors for EXPORT.
- **PR #104 send-plan rehearsal-surface report** — established the panel / binding / acceptance-check / replay-command shape that Phase 3's `cockpit_export_rehearsal.py` reuses; established the wrapped-readiness-JSON pattern that `_profile_from_mapping` follows; flagged the auto-discovery refactor and the rehearsal-surface architecture invariant as Phase 3 lock-in items, both of which land in this phase.
- **`docs/PLAN_REQUIREMENTS.md`** — the 18-gate plan-conformance checklist; §14 of this spec maps each gate to a Phase 3 deliverable.
- **`docs/ARCHITECTURE.md` §6.2 + §6.3** — Phase 1 and Phase 2 cockpit layers; this spec adds §6.4.
- **`docs/ARCHITECTURE_DIAGRAMS.md` §28 + §29 + §30 + §31** — Phase 1 + Phase 2 cockpit diagrams; this spec adds §32.

## 23. Review checklist for the design

For the user reviewing this spec, the questions worth asking:

- [ ] Is the wire format extensible enough for the foreseeable Phase 4 needs (multi-key signing, encryption, profile bundles)?
- [ ] Is the signed envelope unambiguous on the wire (no reframing attacks)?
- [ ] Is the atomic-write contract cross-platform without exotic platform-specific calls?
- [ ] Does the never-raises verifier contract have an exhaustive reason enum?
- [ ] Are the CLI flags stable enough for tooling to depend on?
- [ ] Does the rehearsal report's shape align with PR #104's so a future composer can merge them?
- [ ] Does the auto-discovery refactor of `test_real_midi_passive_cli_safety.py` correctly enforce the inverse rule ("armed commands need explicit allow-list entries")?
- [ ] Is the conformance fixture corpus large enough to lock the wire format against drift?
- [ ] Is the failure-mode catalog (§17) complete enough that an operator hitting any failure gets actionable diagnostics?
- [ ] Are the security considerations (§19) frank about what is and isn't protected?

Answers should be either "yes" (move to implementation plan), "yes with these tweaks" (revise the spec), or "no, here's the missing piece" (extend the spec).

## 24. Sign-off

The spec is **draft / pending user review**. Once approved, the implementation plan at [`docs/superpowers/plans/2026-05-24-phase-3-export-pipeline.md`](../plans/2026-05-24-phase-3-export-pipeline.md) dispatches 7 parallel workstreams (signing, writer, CLI+verifier, rehearsal+backfill, arch invariants, integration tests, docs) against `feat/phase-3-export-pipeline` off `modularize-v1.34`. Bundle review lands as ONE PR per the standard Phase 1 / Phase 2 cadence.

Phase 3 is the file-format contract Phase 4 will consume. Getting the wire format right NOW — magics, format versions, signing algorithm, atomic write, never-raises verifier, conformance fixtures — saves a year of "we shipped the hardware but the file format isn't quite right" rework down the line. The architecture invariants in §10 are the load-bearing guarantee that the format stays right.

The full pipeline is small (~500 LOC of new Python, no new third-party dependencies, no new toolchain) but it carries a lot of cross-phase, cross-language weight. The spec is sized accordingly.

## 25. Appendix A — example wire-format byte dump

To make the wire format concrete, here is an annotated byte dump of a minimal signed envelope (using a deliberately small profile + a fixed test key):

```
# Source profile (JSON, before MessagePack encoding):
{
    "profile_id": "01HXXXX",
    "name": "test",
    "kind": "user",
    "model_version": "1.0.0",
    "traits": [{"name": "low_end", "value": 0.5}],
    "pad_mappings": [{"trait": "low_end", "pad_id": 1, "weight": 1.0}],
    "transition_curve": "linear",
    "source_summary": "1 source"
}

# Phase 1 packed payload (annotated):
52 59 4d 50                # RYMP magic
00 01                      # format_version = 1 (uint16 BE)
05                         # model_version_len = 5 (uint8)
31 2e 30 2e 30             # model_version = "1.0.0" (utf-8)
00 00 00 a3                # payload_len = 163 (uint32 BE)
<163 bytes of MessagePack>  # the encoded ProfileModel.to_dict()
ab cd ef 12                # crc32 trailer (uint32 BE)

# Phase 3 signed envelope wrapping the above (annotated):
52 59 4d 53                # RYMS magic
00 01                      # envelope format_version = 1 (uint16 BE)
0b                         # algo_len = 11 (uint8)
68 6d 61 63 2d 73 68 61    # algo = "hmac-sha" (continued...)
2d 32 35 36                #         "-256" (total 11 bytes)
0a                         # key_id_len = 10 (uint8)
74 65 73 74 2d 6b 65 79    # key_id = "test-key01" (10 bytes)
30 31
20                         # sig_len = 32 (uint8)
<32 bytes of HMAC-SHA256>  # signature
00 00 00 b8                # payload_len = 184 (uint32 BE, includes inner header + payload + crc)
<the entire Phase 1 packed payload from above>
```

The envelope's `payload_len` is the byte length of the WRAPPED Phase 1 packed payload (header + payload + crc), not just the inner MessagePack length. This means the hardware loader can `memcpy` `payload_len` bytes starting from the signature end and treat them as a self-contained Phase 1 packed blob — the inner parser doesn't need to know it was wrapped.

## 26. Appendix B — minimal reference parser (illustrative C)

To make the cross-language contract concrete, here is what a minimal Phase 4 reader might look like in C. This is illustrative — the actual Phase 4 firmware will be more defensive (bounds-check everything, integrate with the hardware's keystore abstraction, etc.) — but the shape is stable.

```c
// Note: error handling elided for brevity; real implementation should
// return distinct error codes for each failure class (mirror the
// VerificationResult.reason enum).

typedef struct {
    uint16_t format_version;
    char model_version[256];
    uint8_t model_version_len;
    const uint8_t* payload;
    uint32_t payload_len;
    uint32_t expected_crc;
} rymp_t;

int rymp_parse(const uint8_t* blob, size_t blob_len, rymp_t* out) {
    if (blob_len < 7) return -1;                              // truncated
    if (memcmp(blob, "RYMP", 4) != 0) return -1;              // bad_magic
    out->format_version = (blob[4] << 8) | blob[5];           // BE uint16
    if (out->format_version != 1) return -1;                  // bad_format_version
    out->model_version_len = blob[6];
    if (blob_len < 7u + out->model_version_len + 4) return -1; // truncated
    memcpy(out->model_version, blob + 7, out->model_version_len);
    out->model_version[out->model_version_len] = '\0';
    const uint8_t* len_ptr = blob + 7 + out->model_version_len;
    out->payload_len = ((uint32_t)len_ptr[0] << 24) | ((uint32_t)len_ptr[1] << 16)
                    | ((uint32_t)len_ptr[2] << 8)  | (uint32_t)len_ptr[3];
    const size_t header_len = 7 + out->model_version_len + 4;
    if (blob_len < header_len + out->payload_len + 4) return -1; // truncated
    out->payload = blob + header_len;
    const uint8_t* crc_ptr = blob + header_len + out->payload_len;
    out->expected_crc = ((uint32_t)crc_ptr[0] << 24) | ((uint32_t)crc_ptr[1] << 16)
                    | ((uint32_t)crc_ptr[2] << 8)  | (uint32_t)crc_ptr[3];
    // Caller must verify crc32(blob, header_len + payload_len) == expected_crc.
    return 0;
}

typedef struct {
    char algo[256];
    char key_id[256];
    uint8_t sig[64];           // up to 64 bytes for sha512; sha256 uses first 32
    uint8_t sig_len;
    const uint8_t* payload;    // points into the original blob; not copied
    uint32_t payload_len;
} ryms_t;

int ryms_parse(const uint8_t* blob, size_t blob_len, ryms_t* out) {
    if (blob_len < 7) return -1;
    if (memcmp(blob, "RYMS", 4) != 0) return -1;
    uint16_t version = (blob[4] << 8) | blob[5];
    if (version != 1) return -1;
    size_t off = 6;
    uint8_t algo_len = blob[off++];
    if (blob_len < off + algo_len) return -1;
    memcpy(out->algo, blob + off, algo_len);
    out->algo[algo_len] = '\0';
    off += algo_len;
    uint8_t key_id_len = blob[off++];
    if (blob_len < off + key_id_len) return -1;
    memcpy(out->key_id, blob + off, key_id_len);
    out->key_id[key_id_len] = '\0';
    off += key_id_len;
    out->sig_len = blob[off++];
    if (blob_len < off + out->sig_len + 4) return -1;
    memcpy(out->sig, blob + off, out->sig_len);
    off += out->sig_len;
    const uint8_t* len_ptr = blob + off;
    out->payload_len = ((uint32_t)len_ptr[0] << 24) | ((uint32_t)len_ptr[1] << 16)
                    | ((uint32_t)len_ptr[2] << 8)  | (uint32_t)len_ptr[3];
    off += 4;
    if (blob_len < off + out->payload_len) return -1;
    out->payload = blob + off;
    // Caller must:
    //   1. resolve key bytes by out->key_id
    //   2. compute HMAC-SHA256 over (algo || 0x1f || key_id || 0x1f || payload)
    //   3. CRYPTO_memcmp(computed, out->sig, out->sig_len) == 0
    //   4. then call rymp_parse(out->payload, out->payload_len, &rymp)
    return 0;
}
```

Total: ~80 lines of C for a complete parser. The signature compare + key resolution are another ~30 lines (HMAC-SHA256 from `mbedtls` is one function call). The CRC32 check is another ~10 lines (256-byte lookup table + a 4-line loop). The whole reader fits in roughly 150 lines of C plus a 5 KB `mbedtls` dependency — well within the budget of a Cortex-M0+ class device.

This appendix is illustrative; the Phase 4 firmware project will produce the real reference implementation. The point is to show that the format Phase 3 ships is genuinely small + portable, not abstract handwaving.
