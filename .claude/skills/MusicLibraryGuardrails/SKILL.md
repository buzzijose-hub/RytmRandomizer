---
name: MusicLibraryGuardrails
description: |
  Analyze a track, folder, library, live recording, factory sound study,
  or a written style description (rolling techno, hypnotic, Birmingham,
  Schranz, peak-time) and produce a draft GuardrailProfile for the
  RytmRandomizer. Use when the user asks to "analyze a track / library",
  "build a guardrail profile from X", "interpret this FeatureReport",
  "what guardrails for [style]", or to turn audio/style into mutation
  ranges. Output is a DRAFT-state GuardrailProfile against
  rytm_randomizer/guardrails/schema.py - typed, copyright-safe by
  construction. Reference, not replica.
---

# Layer 2: music/style analysis -> draft GuardrailProfile

You are the agent half of the WS-V pipeline (`GUARDRAILS_DESIGN_SPEC.md`
section 7). Code (Layer 1) measures into a `FeatureReport`; you
interpret it into a `DRAFT`-state `GuardrailProfile` for the WS-W
validator.

## Procedure

1. **Source.** Audio -> call
   `rytm_randomizer.style_analysis.extract_from_audio` /
   `analyze_library` / `extract_from_partial`. Description-only ->
   `extract_from_description`. Propagate `report.confidence`.
2. **Style tags.** 3-8 behavioral tags, not marketing genres.
3. **Role-map first.** Per pad: `RoleAssignment(role,
   mutation_direction)`. No `GuardrailBound` may exist without a role
   for its pad - WS-W's validator rejects orphan bounds.
4. **Bounds per role.** Each `GuardrailBound(pad, parameter, low, high,
   guardrail_class, direction)`. High-risk params (volume, clock,
   transport, pattern/program change, kit save, extreme tuning,
   unvalidated SysEx, live machine switching) must be
   `LOCKED_DEFAULT`/`FORBIDDEN` - validator rewrites them otherwise.
5. **Construct typed draft** directly against
   `rytm_randomizer.guardrails.schema`: `Provenance` (with
   `feature_report_hash = compute_feature_report_hash(report)`),
   `MusicalCharacter`, `RoleMapping`, `bounds`, `locked_default`,
   `forbidden`, `scenes`, `state=ProfileState.DRAFT`,
   `schema_version=SCHEMA_VERSION`, `content_hash` via
   `compute_content_hash(profile_without_hash)`.
6. **Hand off.** WS-W owns DRAFT -> VALIDATED -> ... -> LIVE_APPROVED.

## Read `reference.md`

For full feature checklists, per-style mutation examples (rolling, raw
peak-time, sci-fi), per-role behavior defaults, scene-key conventions,
SourceType taxonomy, and the legacy JSON-template output shape, **read
`reference.md` when you are actually running an analysis**.

## Core rule

Reference -> discovery. The schema has no field for melodies,
arrangements, or sound-alike patches. Copyright safety is structural.
