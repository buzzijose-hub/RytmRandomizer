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

### Changed

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
