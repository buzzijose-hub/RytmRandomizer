# Analog Four SysEx Readiness Intake PR14

## Why

The Analog Four style reports can plan intent and mock rows from synthetic or
pre-promoted snapshots, but real `.syx` kit dumps still need an honest intake
step. Jose supplied real Analog Four kit and project dumps; read-only analysis
showed saved-kit frames use Elektron family byte `0x06`, object byte `0x52`,
and a 7-bit-packed payload with the kit name in the unpacked record.

This slice makes that real file shape decodable while keeping A4 mutation
blocked until offsets are validated.

## Scope

- Add a small A4 strategy-owned offset manifest for saved-kit intake constants.
- Teach `AnalogFourSnapshotDecoder` to recognize real saved-kit frames, unpack
  the shared Elektron payload, read/clean the kit name, and preserve the
  unpacked bytes.
- Keep `offsets_promoted=False`; this PR must not make A4 hardware sends or
  mock CC previews ready from decoded SysEx alone.
- Surface the saved-kit/candidate layout in the A4 mutation mock-preview report
  and JSON so operators can tell the difference between synthetic candidate
  data and a decoded real file.
- Add a passive A4 kit catalog report so full C6 kit dumps can be scanned for
  decoded slots, names, layouts, byte counts, and candidate-only readiness
  before any offset-promotion work begins.
- Add a passive A4 style kit-readiness sweep so every decoded kit in a dump can
  be evaluated against one style target and surfaced as preview-ready versus
  blocked metadata for future GUI/audio-analyzer kit selection.
- Add stable short payload fingerprints to the A4 catalog and style-readiness
  sweep so future GUI/audio-analyzer consumers can compare exact kit states
  across dumps without relying on kit names alone.
- Update status, README, and architecture diagrams for the new strategy helper.

## Out Of Scope

- Promoting any A4 parameter offsets.
- Sending MIDI, opening MIDI ports, or changing armed runtime behavior.
- Dual-machine PR #61 changes; this branch is clean-base and non-stacked.
- Rytm V1.34 parity behavior or parity fixture regeneration.

## TDD Plan

1. Add failing decoder tests for real saved-kit frames and internal NUL kit-name
   cleanup.
2. Add failing mock-preview tests for the new saved-kit readiness message and
   JSON/text layout field.
3. Add failing A4 kit-catalog tests for text, JSON, CLI parsing, and passive
   error handling.
4. Add failing A4 style kit-readiness sweep tests for text, JSON, CLI parsing,
   and passive error handling.
5. Add failing A4 payload-fingerprint expectations for catalog/readiness text
   and JSON.
6. Implement the manifest, decoder, mock-preview, kit-catalog, and readiness
   sweep changes
   minimally.
7. Run focused tests, real-file passive CLI smoke checks, architecture, fast,
   full, coverage, lint, and review gates before any push.

## Plan-Requirements Conformance

- [x] Gate 1 (100% branch coverage on touched files) -- coverage gate will run
  before PR publication.
- [x] Gate 2 (V1.34 parity byte-identical) -- no V1.34 runtime or parity fixture
  behavior is intentionally changed.
- [x] Gate 3 (lint/format/type clean) -- ruff, black, and isort required before
  PR publication.
- [x] Gate 4 (dead-code purge) -- new manifest constants are consumed by decoder
  and tests.
- [x] Gate 5 (docs updated) -- README, docs/STATUS.md, architecture diagrams,
  and this plan are updated.
- [x] Gate 6 (type-system hygiene) -- concrete dataclasses/constants; no `Any`.
- [x] Gate 7 (observability adoption) -- N/A: passive pure decoding/reporting,
  no hot MIDI path.
- [x] Gate 8 (test hygiene) -- focused behavior tests use intent-named cases.
- [x] Gate 9 (module organization) -- new helper lives under
  `devices/strategies/`; no new top-level package.
- [x] Gate 10 (string-literal dispatch hygiene) -- no new dispatch strings.
- [x] Gate 11 (shared fixtures) -- helper data stays local to the single test
  file that needs it.
- [x] Gate 12 (module constants use Final) -- manifest constants are `Final`.
- [x] Gate 13 (env vars) -- no env vars added.
- [x] Gate 14 (maintainability review) -- verify no duplicated SysEx helper
  implementation; shared envelope helpers are reused.
- [x] Gate 15 (learning phase) -- N/A: no reusable new agent skill needed for
  this small intake slice.
- [x] Gate 16 (execution shape) -- isolated worktree, clean base, non-stacked.
- [x] Gate 17 (abstraction reuse) -- uses `snapshot/envelope.py` and existing
  Device Strategy boundaries.
- [x] Gate 18 (architecture docs/diagrams fresh) -- diagram counts and strategy
  lists updated.

## Done Criteria

- Real Analog Four kit dumps decode to operator-readable kit names.
- Operators can list decoded A4 kit slots/names from a dump without choosing a
  style target, including stable payload fingerprints for kit-state comparison.
- Operators can sweep all decoded A4 kits in a dump against one style target and
  see which kits are blocked by candidate-only offsets before choosing a slot.
- A4 mock-preview report says decoded saved-kit SysEx is still candidate-only.
- No hardware behavior changes.
- PR opens only after #61 is no longer blocking or when explicitly approved as
  an independent same-base PR.
