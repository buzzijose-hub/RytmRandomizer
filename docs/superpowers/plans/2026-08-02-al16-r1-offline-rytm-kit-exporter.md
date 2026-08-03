# AL16 Phase R1 Offline Analog Rytm Kit Exporter

> Status: implementation complete; final integration verification in progress
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
- Focused exporter and codec tests: 34 passed.
- Relevant Rytm layout, codec, envelope, data, and device tests: 191 passed.
- Architecture tests: 736 passed with one unrelated warn-only result.
- Touched production coverage: 438 statements and 130 branches at 100%.
- Strict touched-production type check: 6 modules, 0 errors.
- Ruff, Black, isort, and `git diff --check`: passed.
- Two deterministic blocked builds produced byte-identical reports; no `.syx`
  was emitted and the initialized reference SHA-256 remained unchanged.
