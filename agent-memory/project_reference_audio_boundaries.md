---
name: Reference audio units, quality and replay boundaries
description: Preserve native contracts and retained identity while adding qualified audio diagnostics.
metadata:
  type: project
---

# Reference Audio Boundaries

Normalized audio traits, device display coordinates, encoded native values and
MIDI wire values are distinct contracts. A normalized inference equation must
produce the verified display domain before native conversion. Never rescue an
invalid proposal by widening an encoder, clamping a supplied display value or
silently dropping a selected control. A heuristic equation is not a calibrated
acoustic model or evidence for live transmission.

Keep direct pitch diagnostics separate from the existing eleven-feature score.
A strongest spectral peak is not necessarily a fundamental. pYIN voicing is a
model estimate, not probability of sound-match accuracy or proof of a played
MIDI note. Noise, multiple notes, short windows and octave ambiguity need explicit
uncertainty; do not automatically alter protected tuning or played notes.

Measure capture levels/clipping on original PCM, without normalization or
automatic cropping. Retain original and exact analyzed segment separately.
Reference/profile audio and controlled single-note audition requirements differ.
The short diagnostic window must not accidentally reject the established
long-form isolated analysis path.
Bind diagnostic rate, channel count and sample coordinates to the exact retained
WAV on publication and replay, not just its encoded hash. Detect repeated noise
activity independently of voiced pitch; insufficient stability or uncertain
multi-attack evidence must return a held diagnostic, not an analysis crash.

Optional diagnostics preserve legacy missing keys. Diagnostic refresh changes
measurement metadata only, never candidate bytes, source, favorites or identities.
Changed inference equations need a retained replay version: absence means the
old contract, not permission to silently regenerate a saved favorite. Old bad
equations may be replayed only for already-legal retained candidates; new work
uses the repaired model and keeps older sessions intact.

Optional new fields still expand a persisted schema. Mark new writes with the
canonical store version and migrate old records explicitly after validating the
original checksum. Reading must not rewrite originals or change replay identity;
an older app must return schema-newer, not misclassify a newer file as corrupt.
Match lazy DSP Protocol dtypes to installed-library behavior: default librosa
decoding is float32, while explicit diagnostic PCM remains float64. Repair the
annotation, not existing precision or measurements, and test both real paths.

Community MIDI CSVs are reference knowledge. Pin original hashes and upstream
identity and retain attribution/licensing, but keep MIDI ranges, display units,
native fields, executable mutation policy and physical receipts separate. A
blank address is missing, not zero; machine context matters for reused addresses.
Enum labels do not prove saved-slot association, wire conversion or safe SEND.

See [the reliability plan](../docs/superpowers/plans/2026-10-14-reference-sound-reliability.md)
and [the workflow architecture](../docs/ARCHITECTURE.md#reference-sound-workflow-2026-10).
