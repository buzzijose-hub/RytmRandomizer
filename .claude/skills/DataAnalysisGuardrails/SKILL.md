---
name: DataAnalysisGuardrails
description: |
  Analyze raw hardware data (Analog Rytm / Analog Four SysEx dumps,
  MIDI CC/NRPN captures, mutation logs, factory sound studies, existing
  profiles) and produce a draft GuardrailProfile for the RytmRandomizer.
  Use when the user asks to "analyze a SysEx dump", "interpret this
  MIDI capture", "audit a mutation log", "promote a factory sound study
  to a profile", or "build a profile from raw parameter data". Sibling
  to MusicLibraryGuardrails: that one is audio/style, this one is
  parameter/capture data. Output is a DRAFT-state GuardrailProfile
  against rytm_randomizer/guardrails/schema.py.
---

# Layer 2: data/capture analysis -> draft GuardrailProfile

Sibling of `MusicLibraryGuardrails` (which interprets audio/style).
Both produce a `DRAFT`-state `GuardrailProfile` against the WS-W
schema. Same lifecycle, same safety floor, same copyright-safe
structure - the input is just parameter / capture data instead of
audio.

## Procedure

1. **Role-first.** Pad 1 kick, Pad 2 snare, Pad 3 bass / SY-Raw, Pad 4
   accent (Rytm); T1 bass, T2 stab, T3 pad, T4 FX (Analog Four).
   Assign a role *before* extracting any range - WS-W rejects orphan
   bounds.
2. **Risk-tier each parameter** (low / medium / high). The high-risk
   floor (volume, clock, transport, pattern/program/project change,
   kit save/clear, extreme tuning, unvalidated SysEx, live machine
   switching) is non-negotiable; mark them `LOCKED_DEFAULT` /
   `FORBIDDEN` or WS-W will.
3. **Build conservative ranges.** Group by device / pad / machine /
   role. Strip outliers. Compute a central useful range, not min-max.
   Pick a `GuardrailClass`.
4. **Construct typed draft** directly against
   `rytm_randomizer.guardrails.schema`. For the `Provenance.
   feature_report_hash`, synthesize a `FeatureReport` via
   `extract_from_description` (or `extract_from_partial` if you have
   companion audio) and hash it with `compute_feature_report_hash`. All
   other fields: `MusicalCharacter`, `RoleMapping`, `bounds`,
   `locked_default`, `forbidden`, `scenes`,
   `state=ProfileState.DRAFT`, `schema_version=SCHEMA_VERSION`,
   `content_hash` via `compute_content_hash(profile_without_hash)`.
5. **Hand off.** WS-W validates DRAFT -> VALIDATED / REJECTED.

## Read `reference.md`

For the data-source taxonomy, the per-scope parameter tables
(`MACHINE` / `SRC` / `FILTER` / `AMP` / `LFO` / `FX SEND` on Rytm;
`OSC` / `FILTER` / `AMP/DRIVE` / `ENV` / `LFO` / `FX SEND` /
`VOICE/POLY` / `PERFORMANCE` on Analog Four), the LFO + FX safety
rules, the capture-state guardrails, and the mutation-approval
checklist, **read `reference.md` when you are running an analysis**.

## Core rule

Never treat raw parameter data as automatically safe. Anchors remain
permanent. Captured anchors do not replace validated anchors. Analysis
studies wide ranges; mutation code only uses approved ranges.
