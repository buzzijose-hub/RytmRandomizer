# Model Export Pipeline Implementation Plan — Phase 3

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development. This plan is structured for **maximum-parallelization autonomous execution** per Gate 16 — seven workstreams run concurrently in isolated worktrees, bundle into ONE pull request against `feat/phase-3-export-pipeline` off `modularize-v1.34`.

**Goal:** Wrap the Phase 1 `pack_profile_model` binary serializer in a production-grade export pipeline (HMAC-SHA256 signing, atomic file writes, never-raises integrity verification, end-to-end CLI, passive pre-flight report) that produces the byte-stable `.rymp` files the Phase 4 hardware loader will consume.

**Architecture:** Adds four NEW modules under the existing `rytm_randomizer/cockpit/export/` subpackage (`signing.py`, `verifier.py`, `writer.py`, `cli.py`), one NEW passive report under `rytm_randomizer/reports/` (`cockpit_export_rehearsal.py`), three NEW architecture invariant test files / refactors, and one end-to-end integration test. Reuses every existing Phase 1 abstraction (the `RYMP` packed format, the `ProfileRegistry`, the `cli_registry`) plus the wrapped-JSON / panel / binding / replay-command shape from PR #103 + PR #104.

**Tech Stack:** Python 3.11 + stdlib (`hmac`, `hashlib`, `zlib`, `secrets`, `os.replace`, `tempfile.NamedTemporaryFile`). No new third-party dependencies. MessagePack is already a Phase 1 dependency.

**Source spec:** `docs/superpowers/specs/2026-05-24-phase-3-export-pipeline-design.md`.

---

## 1. Workstream graph

| WS | Title | Depends on | Parallel-safe with | Owner files |
|---|---|---|---|---|
| **WS-A** | Signing module | — | B,C,D,E,F,G | `cockpit/export/signing.py` + tests |
| **WS-B** | Atomic file writer | — | A,C,D,E,F,G | `cockpit/export/writer.py` + tests |
| **WS-C** | CLI orchestration + verifier | A | B,D,E,F,G | `cockpit/export/verifier.py`, `cockpit/export/cli.py` + tests |
| **WS-D** | Rehearsal report + PR #104 backfill | A | B,C,E,F,G | `reports/cockpit_export_rehearsal.py` + tests + the `--help` CLI fixture update |
| **WS-E** | Architecture invariants (new + refactor) | A,C,D | B,F,G | `tests/architecture/test_export_pipeline_invariants.py` (NEW), `tests/architecture/test_cockpit_send_plan_rehearsal_surface_invariants.py` (NEW — PR #104 backfill), `tests/architecture/test_real_midi_passive_cli_safety.py` (REFACTOR to auto-discovery) |
| **WS-F** | End-to-end integration tests | A,B,C,D | E,G | `tests/test_cockpit_export_pipeline_integration.py`, `tests/cockpit/fixtures/export_format_conformance/**` |
| **WS-G** | Docs + diagrams | — | A,B,C,D,E,F | `docs/superpowers/specs/2026-05-24-phase-3-export-pipeline-design.md`, `docs/superpowers/plans/2026-05-24-phase-3-export-pipeline.md`, `docs/ARCHITECTURE.md`, `docs/ARCHITECTURE_DIAGRAMS.md`, `docs/COCKPIT_QUICKSTART.md`, `docs/STATUS.md`, `docs/BUILDING_INSTALLERS.md`, `README.md`, `CONTRIBUTING.md` |

**Parallelization waves:**
- **Wave 1 (t=0, fully parallel):** WS-A, WS-B, WS-D, WS-E, WS-G — fully independent at start.
  - (WS-D and WS-E depend formally on WS-A's `sign_profile_blob` signature but can stub-implement against the documented Protocol from the spec while WS-A runs in parallel; both reconcile against WS-A's final interface at integration.)
- **Wave 2 (after WS-A):** WS-C — depends on `signing.sign_profile_blob` + `pack_signed` to build the verifier and CLI.
- **Wave 3 (after WS-A, WS-B, WS-C, WS-D):** WS-F — integration tests assert the assembled pipeline end-to-end.

Orchestrator dispatches all 7 at t=0; dependent WSes block on predecessors' `ws_done` markers in the state file.

---

## 2. Per-workstream detail

### WS-A · Signing module

- **Worktree:** `RytmRandomizer-worktrees/p3-ws-a-signing`
- **Branch:** `feat/ws-a-signing`
- **Owns:**
  - `rytm_randomizer/cockpit/export/signing.py` (NEW)
  - `tests/cockpit/test_export_signing.py` (NEW)
- **Delivers:**
  - `SIGNED_MAGIC: Final[bytes] = b"RYMS"` (4 bytes; distinct from the `RYMP` payload magic).
  - `SIGNED_FORMAT_VERSION: Final[int] = 1` (uint16 big-endian on the wire; separate from the inner payload's `FORMAT_VERSION`).
  - `SUPPORTED_ALGORITHMS: Final[frozenset[str]] = frozenset({"hmac-sha256"})`.
  - `SIGNATURE_LENGTHS: Final[Mapping[str, int]] = MappingProxyType({"hmac-sha256": 32})`.
  - `SignedEnvelope` frozen dataclass (algo, key_id, sig, payload).
  - `sign_profile_blob(payload: bytes, *, algo: Literal["hmac-sha256"], key_id: str, key: bytes) -> bytes` — computes the signature over `algo || 0x1f || key_id || 0x1f || payload`.
  - `pack_signed(payload: bytes, *, algo, key_id, key) -> bytes` — wraps the payload in the full RYMS envelope.
  - `unpack_signed(blob: bytes) -> SignedEnvelope` — strict parse; raises `ValueError` on malformed input. (The never-raises adapter lives in WS-C's `verifier.py`.)
  - Validation: rejects oversized `algo` / `key_id` (must fit in uint8), unsupported algorithms, wrong `sig` length per algorithm.
  - **100% branch coverage** on `signing.py`.
- **Crew:** implementer -> coverage gate -> reviewer.

### WS-B · Atomic file writer

- **Worktree:** `RytmRandomizer-worktrees/p3-ws-b-writer`
- **Branch:** `feat/ws-b-writer`
- **Owns:**
  - `rytm_randomizer/cockpit/export/writer.py` (NEW)
  - `tests/cockpit/test_export_writer.py` (NEW)
- **Delivers:**
  - `atomic_write(path: Path, blob: bytes) -> None` per the spec §5 contract:
    1. Open `NamedTemporaryFile(delete=False, dir=path.parent, prefix=f"{path.stem}.", suffix=".rymp.tmp")`.
    2. `tmp.write(blob)`.
    3. `tmp.flush()` + `os.fsync(tmp.fileno())`.
    4. `os.replace(tmp.name, path)`.
    5. On any exception: unlink the temp file in a `finally` clause; re-raise.
  - Edge cases:
    - Parent directory missing -> `OSError` from `NamedTemporaryFile`; caller fault.
    - Write-permission denied -> `OSError`; temp file cleaned up.
    - Disk full -> `OSError` mid-write; temp file cleaned up.
    - Simulated process kill between write and replace: a leftover `*.rymp.tmp` is fine (still no partial `*.rymp`).
  - Tests use `tmp_path` exclusively (no `/tmp` writes), simulate partial-write via `mock.patch` on `os.fsync` raising, and assert the original file is untouched on failure.
  - **100% branch coverage** on `writer.py`.

### WS-C · CLI orchestration + verifier

- **Worktree:** `RytmRandomizer-worktrees/p3-ws-c-cli-verifier`
- **Branch:** `feat/ws-c-cli-verifier`
- **Owns:**
  - `rytm_randomizer/cockpit/export/verifier.py` (NEW)
  - `rytm_randomizer/cockpit/export/cli.py` (NEW)
  - `tests/cockpit/test_export_verifier.py` (NEW)
  - `tests/cockpit/test_export_cli.py` (NEW)
  - Additive registration line in `rytm_randomizer/cli_registry.py` (one-liner: `register("cockpit-export-profile-model", _lazy_load("cockpit.export.cli", "main"))`).
- **Delivers:**
  - `VerificationResult` frozen dataclass per spec §6 (`ok`, `reason: Literal[...]`, `detail`, `header`, `signed`).
  - `verify_blob(blob, *, key_resolver=None) -> VerificationResult` — never raises; dispatches on leading magic; returns `bad_magic` / `truncated` / `bad_format_version` / `bad_signature` / `bad_crc` / `unknown_algo` / `unknown_key` / `ok` per the spec's reason enumeration.
  - `verify_file(path, *, key_resolver=None) -> VerificationResult` — wraps `verify_blob` and converts `IOError` / `OSError` into `VerificationResult(ok=False, reason="io_error", detail=str(exc))`.
  - `main(argv: list[str]) -> int` for the `cockpit-export-profile-model` CLI per the spec §7 flag table, flow, and exit codes.
  - Tests cover every reason enum value with targeted blobs (bit-flip the sig, bit-flip the payload, truncate the envelope, bump the format version, mangle the algo, omit the key resolver, etc.).
  - CLI tests use `tmp_path` + `monkeypatch` of the profile registry root + a synthetic `key_resolver` fixture.
  - **100% branch coverage** on `verifier.py` and `cli.py`.

### WS-D · Rehearsal report + PR #104 backfill polish

- **Worktree:** `RytmRandomizer-worktrees/p3-ws-d-rehearsal`
- **Branch:** `feat/ws-d-rehearsal`
- **Owns:**
  - `rytm_randomizer/reports/cockpit_export_rehearsal.py` (NEW)
  - `tests/test_cockpit_export_rehearsal_report.py` (NEW)
  - Additive registration line in `rytm_randomizer/cli_registry.py` (`register("cockpit-export-rehearsal-report", _lazy_load("reports.cockpit_export_rehearsal", "main"))`).
  - CLI `--help` fixture update for the new command.
- **Delivers:**
  - `EXPORT_REHEARSAL_VERSION: Final[str]`, `SAFETY_LINES: Final[tuple[str, ...]]`.
  - Frozen dataclasses for the report (panels, bindings, status, primary action, replay command).
  - `build_cockpit_export_rehearsal_report(*, profile, key_id=None, key_resolver=None) -> CockpitExportRehearsalReport` — pure builder; never writes a file; never opens a port.
  - `_profile_from_mapping(mapping: Mapping[str, object]) -> ProfileModel` — peels out the wrapped `profile` key per the PR #104 `_readiness_from_mapping` pattern.
  - `to_cockpit_export_rehearsal_json(report) -> str` — deterministic JSON (sort_keys, frozen dataclass tree).
  - `main(argv: list[str]) -> int` for the `cockpit-export-rehearsal-report` CLI: accepts `--profile-id`/`--profiles-dir`, `--profile-file`, or `--registry-file`; emits JSON (`--json`) or human-readable lines.
  - Tests cover happy path (`status="ready"`), missing key (`status="blocked"`), unsigned mode (`status="unsigned"`), wrapped-JSON peel, malformed input, every panel rendered, deterministic JSON.
  - **100% branch coverage** on the report module.
- **Reuse callouts:**
  - Reuses `reports.passive_report_lines`, `reports.formatter`, `reports.live_gui_common`, `CliCommand`, `pop_option_value`, `format_cli_error` — the same set the rehearsal-surface report uses.
  - Reuses `cockpit.export.signing.sign_profile_blob` to compute the projected signature length (the actual bytes are not retained).
  - Reuses `cockpit.export.verifier.verify_blob` to compute the projected verification result against an in-memory pack (no disk IO).

### WS-E · Architecture invariants

- **Worktree:** `RytmRandomizer-worktrees/p3-ws-e-arch`
- **Branch:** `feat/ws-e-arch-invariants`
- **Owns:**
  - `tests/architecture/test_export_pipeline_invariants.py` (NEW)
  - `tests/architecture/test_cockpit_send_plan_rehearsal_surface_invariants.py` (NEW — PR #104 backfill)
  - `tests/architecture/test_real_midi_passive_cli_safety.py` (REFACTOR from hand-maintained tuples to `cli_registry` auto-discovery + opt-out allow-list per the spec §10)
- **Delivers:**
  - Invariants on `cockpit/export/**` per spec §10 (MAGIC bytes, format-version constants, supported-algorithm set, signature lengths, `VerificationResult.reason` enum, never-raises AST check, no-MIDI / no-network import check, CLI registration check, `atomic_write` temp-file location check).
  - Invariants on `reports/cockpit_send_plan_rehearsal_surface.py` per spec §11 (PR #104 backfill — module location, `SEND_PLAN_REHEARSAL_SURFACE_VERSION` constant exported, `SAFETY_LINES` content, `surface_status` / `screen_state` / `send_control_state` enum sets, `_COMMAND_NAME`, no-MIDI import discipline).
  - Refactored `test_real_midi_passive_cli_safety.py` with `passive_cli_commands` fixture walking `cli_registry.iter_command_names()`, `_ARMED_ALLOW_LIST` frozen set of armed command names, and the existing per-command subprocess sweep run against the auto-discovered list.
  - **100% branch coverage** on the three test files (the test files themselves are exercised).
- **Reuse callouts:**
  - Reuses `tests/architecture/_ast_helpers.py` (or adds one if it doesn't exist) for the AST inspection that proves the verifier's never-raises contract.
  - Reuses `cli_registry.iter_command_names` (existing) for the auto-discovery refactor.

### WS-F · End-to-end integration tests

- **Worktree:** `RytmRandomizer-worktrees/p3-ws-f-integration`
- **Branch:** `feat/ws-f-integration`
- **Owns:**
  - `tests/test_cockpit_export_pipeline_integration.py` (NEW)
  - `tests/cockpit/fixtures/export_format_conformance/**` (NEW — at least 3 canonical (`profile.json`, `key.bin`, `expected.rymp`) triples covering: a scene profile, a user profile, a profile with empty `pad_mappings`).
  - Additive `signed_blob_factory` + `export_round_trip_artifacts` fixtures in `tests/cockpit/conftest.py`.
- **Delivers:**
  - The end-to-end `test_signed_export_round_trips_byte_identical` test from spec §9.
  - Parametrized negative cases: tampered payload, tampered sig, wrong key, unknown key, unsigned mode, bad magic, truncated envelope, truncated payload, mismatched algo, oversized `algo` / `key_id` (rejected at pack-time), parent-dir-missing, write-permission-denied.
  - Cross-language ground-truth fixtures: the three canonical `expected.rymp` files plus a `_regen.py` script that rebuilds them from the source `profile.json` + `key.bin` so a future C implementation has byte-stable targets to verify against.
  - Conformance test asserts the current `pack_signed` output is BYTE-IDENTICAL to each canonical `expected.rymp` — drift between the implementation and the fixtures fails CI loudly.
  - **100% branch coverage** on the integration test module.

### WS-G · Docs + diagrams — YOU ARE HERE

- **Worktree:** `RytmRandomizer-worktrees/p3-ws-g-docs` (this one)
- **Branch:** `feat/ws-g-docs`
- **Owns:**
  - `docs/superpowers/specs/2026-05-24-phase-3-export-pipeline-design.md` (NEW)
  - `docs/superpowers/plans/2026-05-24-phase-3-export-pipeline.md` (NEW — this file)
  - `docs/ARCHITECTURE.md` (additive §6.4 "Export Pipeline (Phase 3)" subsection under cockpit)
  - `docs/ARCHITECTURE_DIAGRAMS.md` (additive new mermaid sequence diagram: section 32 "Cockpit · Export Pipeline (Phase 3)")
  - `docs/COCKPIT_QUICKSTART.md` (additive §5c "Exporting a profile for hardware" walkthrough after the wizard §5b walkthrough)
  - `docs/STATUS.md` (additive 2026-05-24 entry AT THE TOP describing Phase 3)
  - `docs/BUILDING_INSTALLERS.md` (additive paragraph noting the Tauri bundle includes the export CLI via the sidecar's `python -m rytm_randomizer.cli cockpit-export-profile-model ...` entry)
  - `README.md` (additive one-liner in the "Cockpit (alpha)" section mentioning the export pipeline)
  - `CONTRIBUTING.md` (additive one-liner under the cockpit/reports section documenting the wrapped-readiness-JSON pattern PR #104 introduced + this PR's reuse of it)
- **Delivers:**
  - Spec doc targets ~1,000-1,500 lines; mirrors `2026-05-24-profile-wizard-design.md` structure + Gate-1-18 conformance section.
  - Plan doc targets ~300-500 lines; mirrors `2026-05-24-profile-wizard.md` structure.
  - ARCHITECTURE §6.4 references the spec doc + the diagram + the module tree from spec §3.
  - ARCHITECTURE_DIAGRAMS section 32 is a mermaid sequence diagram showing operator -> cockpit_gui -> cli -> profile_registry -> pack -> sign -> atomic_write -> verify -> operator.
  - COCKPIT_QUICKSTART §5c covers: pre-flight rehearsal command, execute command, verify status, what the `.rymp` file is good for (Phase 4 readiness).
  - STATUS entry summarizes the four new modules, the rehearsal report, the three architecture invariant files (two NEW + one REFACTOR), and the Phase-4 readiness of the binary format.
  - BUILDING_INSTALLERS paragraph clarifies that no new system dependencies are introduced and the Tauri bundle invokes the CLI via the sidecar's existing entry point.
  - README one-liner points to `docs/COCKPIT_QUICKSTART.md` §5c.
  - CONTRIBUTING one-liner names `cockpit_send_plan_rehearsal_surface.py::_readiness_from_mapping` as the canonical wrapped-JSON pattern and notes `cockpit_export_rehearsal.py` follows the same shape.

---

## 3. Disjoint-file ownership matrix

| Path prefix | WS-A | WS-B | WS-C | WS-D | WS-E | WS-F | WS-G |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| `rytm_randomizer/cockpit/export/signing.py` | OK | | | | | | |
| `rytm_randomizer/cockpit/export/writer.py` | | OK | | | | | |
| `rytm_randomizer/cockpit/export/verifier.py` | | | OK | | | | |
| `rytm_randomizer/cockpit/export/cli.py` | | | OK | | | | |
| `rytm_randomizer/reports/cockpit_export_rehearsal.py` | | | | OK | | | |
| `rytm_randomizer/cli_registry.py` (two one-line additive registrations) | | | OK | OK | | | |
| `tests/cockpit/test_export_signing.py` | OK | | | | | | |
| `tests/cockpit/test_export_writer.py` | | OK | | | | | |
| `tests/cockpit/test_export_verifier.py` + `test_export_cli.py` | | | OK | | | | |
| `tests/test_cockpit_export_rehearsal_report.py` | | | | OK | | | |
| `tests/architecture/test_export_pipeline_invariants.py` | | | | | OK | | |
| `tests/architecture/test_cockpit_send_plan_rehearsal_surface_invariants.py` | | | | | OK | | |
| `tests/architecture/test_real_midi_passive_cli_safety.py` (REFACTOR) | | | | | OK | | |
| `tests/test_cockpit_export_pipeline_integration.py` + fixture corpus | | | | | | OK | |
| `tests/cockpit/conftest.py` (additive fixtures) | | | | | | OK | |
| `docs/superpowers/specs/2026-05-24-phase-3-export-pipeline-design.md` | | | | | | | OK |
| `docs/superpowers/plans/2026-05-24-phase-3-export-pipeline.md` | | | | | | | OK |
| `docs/ARCHITECTURE.md` + `ARCHITECTURE_DIAGRAMS.md` + `COCKPIT_QUICKSTART.md` + `STATUS.md` + `BUILDING_INSTALLERS.md` + `README.md` + `CONTRIBUTING.md` | | | | | | | OK |

**Cross-WS conflicts at integration:**

- `rytm_randomizer/cli_registry.py` — WS-C and WS-D both add one line. The two lines are in different positions (alphabetical ordering of command names) and the integration merge can take both without conflict; if a textual conflict appears it's a trivial 2-line merge in the integration phase.
- `tests/cockpit/conftest.py` — WS-F adds fixtures additively; no existing fixture is touched.
- The CLI `--help` fixture file (WS-D update) — only WS-D touches; no conflict.

---

## 4. Agent crew per WS

Same pattern as Phase 2 plan §4:

1. **Implementer** — bite-sized TDD per task -> produces files + tests
2. **Coverage gate** — `pytest --cov=<touched> --cov-branch --cov-fail-under=100`
3. **Lint** — ruff + black + isort + mypy strict
4. **Self-review** — agent verifies own work

A WS is `ws_done` when 1-4 all green.

---

## 5. Self-driving decision rules

Same state machine as Phase 1 / Phase 2: `INIT -> RUNNING -> INTEGRATING -> CI_ITERATION -> DONE`. Same retry semantics. Same "no AskUserQuestion during the run" rule. Same hard stops:

- V1.34 parity fixture diff that survives 2 reverts.
- Bundle integration conflict outside §3 table.
- Code-reviewer Critical that survives 2 fix cycles.
- Budget exhaustion.

---

## 6. Integration phase

```bash
git checkout modularize-v1.34 && git pull
git checkout feat/phase-3-export-pipeline                    # bundle branch (holds spec+plan + integration commits)

# Merge dependency order (matches the wave ordering):
git merge --no-ff origin/feat/ws-a-signing
git merge --no-ff origin/feat/ws-b-writer
git merge --no-ff origin/feat/ws-c-cli-verifier
git merge --no-ff origin/feat/ws-d-rehearsal
git merge --no-ff origin/feat/ws-e-arch-invariants
git merge --no-ff origin/feat/ws-f-integration
git merge --no-ff origin/feat/ws-g-docs                      # this branch
```

Bundle verification (full gate battery from Phase 2 plan §6):

- `python -m pytest -q` (full suite)
- `python -m pytest tests/architecture/ -q`
- V1.34 parity untouched (verify `git status --short tests/fixtures/v134_parity/` empty)
- Lint trio (ruff + black + isort) + mypy strict
- Whole-package coverage stays >= 95% floor
- The new `tests/cockpit/fixtures/export_format_conformance/*.rymp` files are committed in BINARY form (the `.gitattributes` rule for `*.rymp binary` lands as part of WS-F).

---

## 7. The single PR

- **Base:** `modularize-v1.34` -> **Head:** `feat/phase-3-export-pipeline`
- **Title:** `feat: model export pipeline (Phase 3 — HMAC signing + atomic write + verifier + CLI + rehearsal report)`
- **Body:** Full 18-gate conformance checklist (§9) + strict-rules confirmation + links to spec + plan + the three PR-#104-leverage callouts (rehearsal-surface invariant backfill, passive-CLI auto-discovery refactor, wrapped-JSON pattern documentation in CONTRIBUTING).
- **Status:** draft initially; ready-for-review once `INTEGRATING` lands green; codex review hook fires automatically.

---

## 8. Operational guardrails

- **Hard time budget:** 60 hours wall-clock (smaller than Phase 2 since this phase is mostly Python stdlib glue + docs; no new frontend code, no new third-party deps).
- **Recovery:** same as Phase 2 — read on-disk state, query `gh pr list`, resume from reconciled state.
- **Permission profile:** `acceptEdits`; refuse force-push to protected branches, V1.34 fixture regen, hardware-pin bumps, `--no-verify`.
- **Hard stops:** V1.34 parity fixture diff that survives 2 reverts; bundle integration conflict outside §3 table; code-reviewer Critical that survives 2 fix cycles; budget exhaustion.

---

## 9. Plan-requirements conformance

Per `docs/PLAN_REQUIREMENTS.md`:

- [x] **Gate 1** — 100% branch coverage on touched files (per-WS enforcement).
- [x] **Gate 2** — V1.34 parity byte-identical (no engine code touched, no V1.34 fixture touched).
- [x] **Gate 3** — lint / format / type clean.
- [x] **Gate 4** — no new dead code (every new public function exercised by the integration test + per-module tests).
- [x] **Gate 5** — docs updated (WS-G).
- [x] **Gate 6** — frozen dataclasses + `Protocol`s + no bare `Any` + `Literal` discriminators.
- [x] **Gate 7** — `get_metrics().record_*` on the four new public functions (`pack_signed`, `verify_blob`, `atomic_write`, both CLI entry points).
- [x] **Gate 8** — intent-named tests.
- [x] **Gate 9** — no new top-level `*.py`; all new modules under existing `cockpit/export/` and `reports/` subpackages.
- [x] **Gate 10** — `Literal` types for `algo`, `reason`, `status`; pinned by architecture invariants.
- [x] **Gate 11** — `signed_blob_factory` + `export_round_trip_artifacts` shared fixtures in `tests/cockpit/conftest.py`.
- [x] **Gate 12** — `Final` constants throughout (`SIGNED_MAGIC`, `SIGNED_FORMAT_VERSION`, `SUPPORTED_ALGORITHMS`, `SIGNATURE_LENGTHS`, `EXPORT_REHEARSAL_VERSION`, `SAFETY_LINES`).
- [x] **Gate 13** — no new env vars (keystore directory is hardcoded in Phase 3; the env-var override is a Phase-3.5 deliverable).
- [x] **Gate 14** — maintainability audit included (pre and post).
- [x] **Gate 15** — learning extraction: the wrapped-JSON pattern, the atomic-file-write contract, the never-raises verifier contract all become reusable skills under `.claude/skills/learned/`.
- [x] **Gate 16** — execution shape: 7 parallel WSes, one bundled PR.
- [x] **Gate 17** — abstraction reuse: `cockpit/export/model_format.py` (Phase 1), `cockpit/export/serialize.py` (Phase 1), `cockpit/profiles/registry.py` (Phase 1), `cli_registry` (existing), `reports.passive_report_lines` / `reports.formatter` / `reports.live_gui_common` / `CliCommand` (existing), `cockpit_send_plan_rehearsal_surface._readiness_from_mapping` wrapped-JSON pattern (PR #104).
- [x] **Gate 18** — architecture-doc + diagram freshness (WS-G).

Exceptions: none.

---

## 10. Execution handoff

**Kickoff** (operator runs in chat):

```
/loop run docs/superpowers/plans/2026-05-24-phase-3-export-pipeline.md
```

Orchestrator follows §5, runs §6 integration, opens the PR per §7, iterates §5's `CI_ITERATION` until green + reviewed, writes `DONE`.

**Out-of-scope (deferred to follow-on phases):**

- Phase 3.5 — keystore + key-management UI (the wizard for generating, rotating, importing keys; the JSON / OS-keyring backend).
- Phase 4 — hardware runtime (the dedicated box that reads `.rymp` files and runs the embedded mutation engine).
- GUI export button in the Mutation Panel (WebSocket `export_profile_model` command + frontend wiring — a Phase 3.5 or Phase 4 add).
- Shared `reports/_passive_section.py` formatter helper (PR #104 follow-up; will pick up the rehearsal-surface report AND the new export-rehearsal report together).
- HMAC-SHA512 / Ed25519 signing algorithms (wire format is forward-compatible; new algorithms ship as one-line additions to `SUPPORTED_ALGORITHMS` + `SIGNATURE_LENGTHS`).
