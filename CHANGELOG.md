# Changelog

All notable changes to RytmRandomizer are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

The single source of version truth is the `[project] version` field in
`pyproject.toml`. Each release moves the entries below from `[Unreleased]` into a
new versioned section. See the **Releasing** section of `CONTRIBUTING.md` for the
full version-bump and tagging flow.

## [Unreleased]

### Added

- Show Kit Forge: immutable paired Rytm/A4 sources, scoped candidates,
  favorites, manual-save recapture verification, ordered show-time preflight,
  and explicit atomic local show packs. Filter 1 Frequency gains fixture-backed
  A4 offline generation; A4 SEND and persistent hardware SAVE remain blocked.
- Passive RIO145 native-KIT tooling for Analog Four and Analog Rytm: strict
  SysEx inspection/diff/roundtrip validation, deterministic recipe builds,
  target-return validation, and OXI evidence export. The integration includes
  12 real-machine fixtures and adds no MIDI provider, port, sender, or native
  Elektron pattern-generation path.
- `tests/fixtures/v134_parity/` — JSON goldens capturing the V1.34 reference
  output for every parity request the engine/runner suite asserts against.
  Generated via `PARITY_CAPTURE_MODE=1 pytest`, then committed.
- Capture/check modes in `tests/_parity_worker.py`. The parity worker now
  routes each request through either `capture_reference()` (writes a fixture)
  or `assert_engine_matches()` (compares engine output to the fixture).

### Changed

- Parity tests under `tests/test_engines_pad*.py`, `tests/test_group_runner.py`
  and `tests/test_scene_runner.py` no longer drive the V1.34 monolith
  side-by-side with the package; they compare engine output to the committed
  JSON goldens. Same byte-for-byte contract, no live monolith required.

### Removed

- `rytm_hybrid_randomizer_v134.py` (2,950 LOC). The retired monolith's
  reference behavior is preserved as the JSON goldens noted above.
- Subprocess-vs-monolith parity tests in `tests/test_midi_io.py`,
  `tests/test_randomization.py`, `tests/test_data_layer.py` and
  `tests/test_state_package.py`. Replaced by in-process branch coverage and a
  frozen `_V134_GLOBAL_DEFAULTS` constant where the monolith's cold-start
  globals were previously snapshotted out-of-process.
- Architecture tests that verified the monolith file existed and had a clean
  working-tree diff. Replaced by a guard ensuring the monolith is not
  resurrected at either of its historic locations.

### Fixed

## [1.34.0] - 2026-05-14

Baseline release: the validated V1.34 expanded-scene-layer monolith
(`rytm_hybrid_randomizer_v134.py`), the hardware-validated MIDI
randomizer/mutator for the Elektron Analog Rytm MK2. Stable tag of record:
`v1.34-stable-expanded-scene-layer`.

### Added

- Hardware-validated MIDI randomizer/mutator for the Analog Rytm MK2, driven
  from a small text prompt that sends CC messages over MIDI via `mido`.
- Four-lane pad layout: Pad 1 (BD Hard / protected kick foundation), Pad 2
  (BD Classic / secondary percussion), Pad 3 (SY Raw / bass + synth-percussion
  motion), Pad 4 (BD Acoustic / body + accent pressure).
- Layered scene system S0–S5: Home/Clean anchors (S0), Rolling (S1/S1A/S1B),
  Deeper (S2/S2A/S2B), Intense (S3/S3A/S3B), Wild (S4/S4A/S4B), and Back to
  Clean anchors (S5).
- A 4-pad group layer, isolated single-pad mutation, and legacy single-profile
  mutation.
- Safety guardrails: no new machine profiles, no new MIDI CC mappings, no new
  parameter ranges, no Pads 5–12 expansion; guarded main-prompt `1`/`2`/`3`
  commands that send no MIDI; four-pad scene/global commands auto-load anchors
  when needed.

[Unreleased]: https://github.com/misteredr/RytmRandomizer/compare/v1.34.0...HEAD
[1.34.0]: https://github.com/misteredr/RytmRandomizer/releases/tag/v1.34.0
