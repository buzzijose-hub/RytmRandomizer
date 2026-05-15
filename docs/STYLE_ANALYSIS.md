# Style analysis (WS-V Layers 1-2)

`rytm_randomizer/style_analysis/` is the **deterministic measurement**
half of the four-layer guardrails system described in
`GUARDRAILS_DESIGN_SPEC.md`. It turns reference material (audio files,
libraries, descriptions) into a typed `FeatureReport`, which the WS-V
interpretation skill (`.claude/skills/MusicLibraryGuardrails/`) then
turns into a draft `GuardrailProfile` for the WS-W validator.

## The four-layer model

| Layer | Owner | Module / file | Output |
|---|---|---|---|
| **1. Measurement** | code | `rytm_randomizer/style_analysis/` | `FeatureReport` (typed, content-hashed, confidence-tagged) |
| **2. Interpretation** | agent (+ skill) | `.claude/skills/MusicLibraryGuardrails/` + `.claude/skills/DataAnalysisGuardrails/` | DRAFT-state `GuardrailProfile` |
| **3. Validation** | code | `rytm_randomizer/guardrails/validation.py` (WS-W, future) | VALIDATED or REJECTED profile |
| **4. Consumption** | code | `rytm_randomizer/guardrails/resolver.py` (WS-W, future) + engines | Resolved bounds the randomizer mutates within |

WS-V owns **Layers 1 and 2**. WS-W owns Layers 3 and 4. The seam is the
typed Guardrail Profile contract in
`rytm_randomizer/guardrails/schema.py` (already shipped by WS-W's first
step); WS-V *produces* it, WS-W *validates and consumes* it.

## Installing the `style` extra

Layer 1's deterministic audio extraction relies on
[`librosa`](https://librosa.org/). It is an **optional** dependency -
the core install does not pull it in, so a user who only needs the
description-only path (or only the rest of the package) is not paying
for the heavy audio stack.

```bash
# Core install (description-only path works; no audio measurement):
pip install -e ".[dev]"

# Full audio-extraction install:
pip install -e ".[style,dev]"
```

If you call `extract_from_audio` / `extract_from_partial` /
`analyze_library` (with audio files present) without the `style` extra,
the call raises `StyleAnalysisDependencyError` with an actionable
message. Lazy-import discipline means importing
`rytm_randomizer.style_analysis` itself never touches `librosa`; that
happens only when an audio path actually runs.

## Running an analysis

### Description only (no audio, LOW confidence)

```python
from rytm_randomizer.style_analysis import extract_from_description
from rytm_randomizer.guardrails.schema import SourceType

report = extract_from_description(
    "rolling hypnotic techno, 128 BPM, anchored low end",
    source_type=SourceType.STYLE_DESCRIPTION_ONLY,
)
# report.confidence is Confidence.LOW; numeric fields are zeroed
# placeholders. The interpretation skill (Layer 2) fills in mutation
# intent from the description directly.
```

### Single audio file (HIGH confidence)

```python
from pathlib import Path
from rytm_randomizer.style_analysis import extract_from_audio

report = extract_from_audio(Path("reference.wav"))
# report.bpm, .kick_density, .low_end_weight, .spectral_brightness,
# .texture_noise, .energy_arc, .tempo_stability are measured
# deterministically by librosa.
```

### Library (folder of audio, HIGH confidence)

```python
from pathlib import Path
from rytm_randomizer.style_analysis import analyze_library

report = analyze_library(Path("library/"))
# Walks WAV/AIF/AIFF/FLAC/MP3 files (sorted, deterministic), aggregates
# per-file features with median (scalars) + element-wise mean (energy
# arc). Empty directory -> LOW-confidence zeroed report.
```

### Partial (some audio + user notes, MEDIUM confidence)

```python
from pathlib import Path
from rytm_randomizer.style_analysis import extract_from_partial

report = extract_from_partial(
    [Path("a.wav"), Path("b.wav")],
    notes="user prefers tighter kicks, dryer texture",
)
```

### Hashing for traceability

```python
from rytm_randomizer.style_analysis import compute_feature_report_hash

digest = compute_feature_report_hash(report)
# Same canonical-JSON SHA-256 pattern as
# rytm_randomizer.guardrails.schema.compute_content_hash. The WS-V
# interpretation skill stamps `digest` into
# `Provenance.feature_report_hash` so the validated profile points back
# to the exact measurement it was derived from.
```

## Determinism guarantee

For a given audio file, `extract_from_audio` always returns the same
measurements (modulo the `derived_at` timestamp, which is wall-clock).
This is asserted by the librosa-gated test
`test_extract_from_audio_runs_on_synthetic_signal` in
`tests/test_style_analysis.py`: a second extraction on the same WAV
yields identical `bpm`, `tempo_stability`, `spectral_brightness`, and
`energy_arc`.

Implementation choices that make this hold:

- Librosa is called with `sr=22050, mono=True` (explicit sample rate +
  channel collapse). No defaults that vary by system.
- The energy arc is sampled at 8 evenly-spaced indices via
  `numpy.linspace`, then normalised against the peak RMS. No
  randomness.
- The library walker sorts file paths before aggregation
  (`Path.rglob("*")` -> `sorted(...)`), so the per-file order is
  deterministic across machines/filesystems.

The description-only path is deterministic by construction (it never
reads audio).

## Copyright safety - "influence, not replica"

The schema can express *behavioral mutation boundaries* (ranges,
classes, directions, risk). It deliberately has **no field for a
melody, an arrangement map, a copyrighted hook, or a sound-alike
patch**. The Guardrail Profile literally cannot carry a replica through
this contract because the contract has nowhere to put one
(`GUARDRAILS_DESIGN_SPEC.md` section 7.3). Reference -> discovery is
enforced by the *shape* of the artifact, not by the agent's goodwill.

When the user analyzes a commercial track or reference artist, the
interpretation skill captures *high-level musical traits* (energy
profile, density, texture, mutation directions) - never melodies,
arrangements, or sound-alike sound design. The skill explicitly bans
language like "clone this track" / "make it identical" and uses
language like "inspired by the reference behavior" / "original anchor
direction".

This is the **influence not replica** rule, lifted unchanged from the
pre-schema `MusicLibraryGuardrails` skill.

## See also

- `GUARDRAILS_DESIGN_SPEC.md` - the full four-layer design.
- `rytm_randomizer/guardrails/schema.py` - the typed Guardrail Profile
  contract (the seam between WS-V and WS-W).
- `.claude/skills/MusicLibraryGuardrails/SKILL.md` - the Layer 2
  interpretation skill (the tight version; reads
  `reference.md` on demand at analysis time).
- `.claude/skills/DataAnalysisGuardrails/SKILL.md` - the sibling
  interpretation skill for parameter / capture-data input.
- `tests/test_style_analysis.py` - schema, immutability, hashing,
  lazy-import discipline, librosa-gated synthetic-signal tests.
