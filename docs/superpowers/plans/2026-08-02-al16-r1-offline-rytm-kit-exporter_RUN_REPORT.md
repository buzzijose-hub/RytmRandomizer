# AL16 R1 Autonomous Run Report

> Status: in-flight (PR #222)

## Outcome

Phase R1 implemented the passive exporter boundary and produced deterministic
blocked-build evidence. AL02 did not compile because 18 critical mappings are
not positively verified. Zero raw bytes changed and no `.syx` was emitted.

## Timeline

1. Audited the existing Rytm saved-KIT layout, envelope, and reference, then added the missing strict codec.
2. Added canonical AL16 bank and recipe facts plus the passive command.
3. Implemented strict validation, mapping-gap evidence, and deterministic sidecars.
4. Proved reference preservation, no-MIDI behavior, parity, typing, and coverage.
5. Opened one non-stacked PR and ran dimension-specific post-push review.
6. Closed review findings around reuse, collision safety, determinism, scope, and docs.

## Final local verification

- Focused exporter, saved-kit codec, and CLI regression tests: 115 passed,
  1 skipped.
- Exporter and saved-kit codec proof tests: 95 passed, 1 skipped.
- Data-layer drift tests: 200 passed.
- Architecture: 739 passed with one unrelated warn-only result.
- V1.34 byte-frozen parity: 685 passed.
- Full suite: 7,627 passed, 4 skipped.
- Touched production coverage: 14 files at 100% line and branch coverage.
- Strict typing: 14 touched production modules, 0 errors and 0 warnings.
- Total coverage: 99.44%; pure branch coverage: 98.92%.
- Deterministic blocked-build evidence: 18 critical gaps, zero changed raw bytes, no `.syx`.

## Recovery and replay

The branch, state file, immutable recipe identifier, reference SHA-256, and
evidence hashes are sufficient to resume after interruption. Replay follows
`docs/AUTONOMOUS_RUN_PLAYBOOK.md` with at most two pytest workers. No hardware
state is part of this run.

## Lessons

- Evidence-only output must be named that way in both help and documentation.
- Output and sidecar paths must be checked against every verified input before reads or writes.
- Equivalent recipe mappings need deterministic key ordering.
- Wall-clock time cannot participate in default deterministic evidence.
- A blocked compiler result is the correct product when device evidence is incomplete.

## Learning extraction

The existing `elektron-sysex-envelope` skill now records the reusable
multi-file publication lesson: validate bounded portable names, stage the
complete sidecar set, preserve the previous generation, roll back partial
publication, and hash-lock committed evidence. Recipe canonicalization and
canonical-path collision detection remain local to this exporter until another
independent workflow proves a genuinely shared abstraction.

## Fresh-clone questions

- Can the command import and show help without a private reference? Yes.
- Can tests run without opening MIDI? Yes.
- Can an operator mistake sidecars for a loadable kit? Documentation and file names say no.
- Can a partial kit escape when mappings are absent? The exact gap set blocks `.syx` emission.
