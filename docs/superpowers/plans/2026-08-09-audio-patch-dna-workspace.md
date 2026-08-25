# Audio-to-Patch DNA Workspace

> Status: complete (merged in PR #228)

## Goal

Deliver one passive workflow that analyzes a supplied audio file once, explains its measurable sound DNA, creates eight deterministic Analog Four directions, lets the operator select one direction, and exports the selected candidate through the existing hardware-safe A4 batch exporter.

The workflow is an interpretation tool. It does not claim forensic recreation of a recording or knowledge of the original artist's equipment.

## User workflow

1. Run `audio-patch-dna` with an audio path and output directory.
2. Review a JSON workspace and readable Markdown report containing pitch, envelope, rhythm, brightness, noise, spectral movement, tonal stability, and eight candidates.
3. Re-run with `--select 1..8` and a source A4 kit to export only the chosen candidate as a validated A4 SysEx batch.
4. Audition the exported patch manually. No MIDI port is enumerated, opened, or written by this workflow.

## Candidate directions

1. Closest
2. Darker
3. Brighter
4. Metallic
5. Percussive
6. Atmospheric
7. Deeper
8. Animated

Each direction applies bounded transforms to the same measured audio features and then uses the existing Analog Four inference and export layers. Candidate order and transforms are deterministic.

## Architecture

```text
audio file
  -> isolated one-pass analysis
  -> AudioFeatureAnalysis + AudioDnaEvidence
  -> eight bounded feature directions
  -> existing Analog Four inference
  -> workspace JSON + Markdown comparison
  -> optional selected-candidate A4 batch export
```

The implementation belongs in `style_analysis/` for analysis and candidate construction and `cockpit/export/` for filesystem orchestration and CLI handling. It adds no top-level package module and no real-MIDI dependency.

## Safety and compatibility

- Passive by construction; no MIDI imports, providers, ports, or sends.
- One audio decode per workspace build.
- Existing A4 batch validation, envelope packing, and SysEx verification remain authoritative.
- Existing V1.34 behavior and parity fixtures remain unchanged.
- Rytm export is intentionally deferred until the separate dual-kit codec work is merged.
- Tests and validation run with at most two workers on the local studio PC.

## Verification

- Complete suite: 7,767 passed, 4 skipped.
- Architecture: 743 passed.
- Frozen V1.34 parity: 685 passed.
- Touched production coverage: 100% statement and branch coverage across 11 files.
- Repository coverage: 99.45% blended; 98.95% pure branch coverage.
- Strict touched-production typing: 0 errors and 0 warnings.
- Ruff, Black, isort, and the mechanical code-review gate passed.
- No MIDI provider or physical port was constructed, enumerated, opened, or written.
