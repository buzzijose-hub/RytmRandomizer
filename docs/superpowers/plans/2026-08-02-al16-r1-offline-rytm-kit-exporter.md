# AL16 Phase R1 Offline Analog Rytm Kit Exporter

> Status: in-flight - implementation, review repairs, and bounded closeout verification passed; AL02 correctly remains blocked by 18 verified mapping gaps
>
> Offline audit implemented; AL02 output remains blocked by verified mapping gaps.

## Scope

Implement a passive, deterministic compiler boundary for one AL16 Analog Rytm
saved kit. The phase reserves all sixteen AL16 operating states but attempts
only `AL02 LOCK`. It does not add live MIDI, enumerate ports, or implement a
real-device adapter.

## Architecture

1. Decode and validate one complete Elektron saved-kit frame.
2. Parse a dependency-free JSON-compatible YAML musical recipe.
3. Validate permanent pad roles and machine/pad compatibility.
4. Resolve only fields present in the strict positive-evidence allowlist.
5. Resolve target notes only through an approved machine-specific table.
6. Fail before mutation when a critical field lacks positive evidence.
7. On a fully verified future recipe, patch a copy, repack, verify the checksum
   and encoded length, decode again, and compare requested semantics and the
   byte-diff allowlist.
8. For this evidence-limited proof, write a manifest, validation report, and
   zero-mutation byte-diff report while withholding the `.syx` file.
9. Keep build/report orchestration under `cockpit/export`, separate from the
   registered passive `al16-rytm-kit-export` command adapter that owns argument
   parsing and process exit behavior.

## Evidence boundary

The initialized Rytm reference round-trips byte-for-byte. Common filter and
amp locations are known except amp volume. Saved-kit machine changes,
machine-specific source parameters, sample level, amp volume, the XT Classic
F2 tuning lookup, and destination-slot writing are not positively
writer-validated. AL02 therefore must remain blocked until those observations
exist; substituting candidate offsets would violate the project safety policy.

## Verification

- Pure codec tests use synthetic payloads and optionally the local private
  reference through `RYTM_TEST_REFERENCE`.
- Exporter tests assert deterministic recipe identity, exact preserved tracks,
  explicit mapping gaps, absence of `.syx`, unchanged reference bytes, and
  zero MIDI dependencies.
- Focused tests run single-process to avoid unnecessary workstation load.
- Focused exporter, saved-kit codec, and CLI regression tests: 115 passed,
  1 skipped.
- Exporter and saved-kit codec proof tests: 95 passed, 1 skipped.
- Data-layer drift tests: 200 passed.
- Architecture tests: 739 passed with one unrelated warn-only result.
- V1.34 byte-frozen parity: 685 passed.
- Full repository suite: 7,627 passed, 4 skipped.
- Total coverage: 99.44%; pure branch coverage: 98.92% against the 98% floor.
- Touched production coverage: 14 files at 100% line and branch coverage.
- Strict touched-production type check: 14 modules, 0 errors and 0 warnings.
- Ruff, Black, isort, and `git diff --check`: passed.
- Two deterministic blocked builds produced byte-identical reports, recording
  18 critical mapping gaps and zero intentionally changed bytes. No `.syx` was
  emitted and the initialized reference SHA-256 remained unchanged.
- Deterministic evidence SHA-256 values were
  `80e264e151846452970cacd9d1e22f309befe15072d2f654b3fe436966077d37`
  for the manifest,
  `bcf04d1a77c412d93efa1ec558a817df6656ea000d0fb8b337efc992eabbe6e5`
  for the validation report, and
  `5263e9042b091fb89a1a6da005e5056909a3a9a37f12490900c4b2422703701f`
  for the byte-diff report.

## Maintainability review (Gate 14)

The paired audit and closeout report are durable review artifacts:

- [`2026-08-02-al16-r1-offline-rytm-kit-exporter_MAINTAINABILITY_AUDIT.md`](2026-08-02-al16-r1-offline-rytm-kit-exporter_MAINTAINABILITY_AUDIT.md)
- [`2026-08-02-al16-r1-offline-rytm-kit-exporter_MAINTAINABILITY_REPORT.md`](2026-08-02-al16-r1-offline-rytm-kit-exporter_MAINTAINABILITY_REPORT.md)

| Dimension | Before | After |
| --- | --- | --- |
| Fact ownership | Exporter-local strings and sizes | Typed converter/mode facts and Rytm layout constants in `data/` |
| Dispatch | Repeated raw strings | `Literal`-typed canonical constants |
| Name decoding | Local byte slicing | Shared `snapshot.envelope.read_ascii_name` |
| Pad iteration | Hard-coded numeric range | Canonical `AL16_PAD_ROLES` order |
| Observability | Blocked result only | One traced operation, bounded logs, and one blocked metric |
| Determinism | Same-key-order fixture | Reordered-key recipe plus fixed `SOURCE_DATE_EPOCH` proof |
| Failure evidence | Loose lower-bound assertion | Exact 18-path mapping-gap assertion |
| Hardware boundary | Passive by convention | Architecture tests and import surface prove no MIDI dependency |
| Documentation | Future writer wording mixed with current behavior | Current audit-only behavior separated from future writer work |
| Recovery | Implicit rerun | Immutable reference, atomic reports, deterministic recipe ID, rerunnable command |

The exporter remains deliberately small and fail-closed. It adds the contained
strict Rytm saved-KIT codec required by this phase while reusing the existing
layout metadata, Elektron envelope/u14 helpers, observability primitives, and
local-file export contracts.

## Execution and recovery (Gates 15-16)

This was one tightly coupled workstream in one isolated feature worktree and
one non-stacked PR. Parallel work was limited to read-only review dimensions
(architecture, types, tests, side effects, observability, abstraction reuse,
documentation, and maintainability); there were no sibling writer branches to
merge. That shape avoids conflicting edits across the exporter, its canonical
data facts, and its exact evidence tests.

| Workstream | Ownership | Dependency | Result |
| --- | --- | --- | --- |
| R1 exporter | Single writer worktree | Existing codec/layout evidence | Complete, fail-closed |
| Mechanical verification | Read-only commands | R1 exporter | Complete on the current local tree |
| Dimension reviews | Parallel read-only agents | Pushed PR head | Complete; findings repaired by the single writer |
| Hosted CI | GitHub Actions | Exact pushed head | Must be green before the final CODEOWNER request |
| CODEOWNER review | Edward Rosado | Green exact PR head | Pending |

The durable state is the Git branch plus deterministic evidence artifacts. A
run may be restarted from the same immutable reference, recipe, destination
slot, and `SOURCE_DATE_EPOCH`; no hardware state is involved. Terminal success
for Phase R1 means all verification gates are green, the exact 18 critical
gaps are reported, zero raw bytes are changed, and no `.syx` is emitted.
Unexpected positive output, reference drift, a changed gap set, or any MIDI
dependency is a hard failure. Verification uses at most two pytest workers to
respect workstation stability. The review/verification budget is 72 hours;
the work stops rather than weakening a gate when that budget is exhausted.

Autonomous execution rules for this run:

1. Kickoff only from the verified integration base in one isolated worktree.
2. Record scope decisions in this plan before adding a production path.
3. Rebase only when required by the base and never rewrite a reviewed remote head.
4. Persist recovery state in the schema-checked state file after phase changes.
5. Recover from the immutable reference, recipe identifier, branch, and evidence hashes.
6. Keep permissions passive; never invoke `app --arm`, enumerate ports, or transmit MIDI/SysEx.
7. Stop on reference drift, unexpected positive output, gap-set drift, or an exhausted budget.
8. Terminate Phase R1 only after local gates, hosted CI, and CODEOWNER approval are complete.

Durable execution artifacts:

- [`2026-08-02-al16-r1-offline-rytm-kit-exporter_ARCHITECTURE_BEFORE_AFTER.md`](2026-08-02-al16-r1-offline-rytm-kit-exporter_ARCHITECTURE_BEFORE_AFTER.md)
- [`2026-08-02-al16-r1-offline-rytm-kit-exporter_RUN_REPORT.md`](2026-08-02-al16-r1-offline-rytm-kit-exporter_RUN_REPORT.md)
- [`2026-08-02-al16-r1-offline-rytm-kit-exporter_RUN_LOG.md`](2026-08-02-al16-r1-offline-rytm-kit-exporter_RUN_LOG.md)
- [`2026-08-02-al16-r1-offline-rytm-kit-exporter_STATE.schema.json`](2026-08-02-al16-r1-offline-rytm-kit-exporter_STATE.schema.json)
- [`2026-08-02-al16-r1-offline-rytm-kit-exporter_STATE.json`](2026-08-02-al16-r1-offline-rytm-kit-exporter_STATE.json)

The existing `elektron-sysex-envelope` learned skill now records the reusable
multi-file evidence-publication rule: validate bounded portable names, stage
the complete sidecar set, preserve the previous generation, roll back a partial
publish, and hash-lock committed evidence. Recipe canonicalization and
canonical-path collision detection remain exporter-local because they have not
yet recurred as a stable cross-workflow abstraction.

## Replay log

The closeout resolved the repository and Python interpreter from the current
workspace, bounded pytest at two workers, and never invoked the armed
application entry point, enumerated ports, or transmitted MIDI/SysEx.

```powershell
$repoRoot = git rev-parse --show-toplevel
$python = (Get-Command python).Source
$reference = Join-Path $repoRoot "reference\RYTM_Test1_Init_Kit.syx"

& $python -m pytest tests/test_al16_rytm_export.py `
  tests/test_analog_rytm_saved_kit_codec.py `
  tests/cockpit/test_al16_rytm_cli.py -n 0 -q
& $python -m pytest tests/test_al16_rytm_export.py `
  tests/test_analog_rytm_saved_kit_codec.py -n 0 -q
& $python -m pytest tests/test_data_layer_drift.py -n 0 -q
& $python -m pytest tests/architecture/ -n 2 -q
& $python -m pytest -m "not fast" -n 2 -q
& $python -m pytest -n 2 --cov=rytm_randomizer --cov-branch `
  --cov-report=term-missing --cov-report=xml:coverage.xml -q
& $python scripts/typecheck_touched.py
& $python scripts/check_touched_coverage.py coverage.xml
& $python scripts/coverage_ratchet.py coverage.xml
& $python -m ruff check .
& $python -m black --check --target-version=py311 .
& $python -m isort --profile black --check-only .
git diff --check

$env:SOURCE_DATE_EPOCH = "1785628800"
& $python -m rytm_randomizer.cli al16-rytm-kit-export `
  --reference $reference `
  --recipe specs/al16/AL02_LOCK_RYTM.yaml `
  --destination-slot 127 `
  --output output/local/al16-r1-audit-1/AL02_LOCK_RYTM.syx
```

The final command intentionally returned the blocked status, wrote only the
three deterministic evidence reports, reported the exact 18 mapping gaps, and
left the `.syx` output absent. Repeating it in a second clean output directory
produced the same three hashes recorded above.
