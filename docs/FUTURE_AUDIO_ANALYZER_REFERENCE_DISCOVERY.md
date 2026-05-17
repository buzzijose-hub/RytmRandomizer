# Future Audio Analyzer: Reference / Discovery Control

> STATUS: FUTURE PRODUCT DIRECTION. This is a docs-only checkpoint. It does
> not add 12-pad support, change V1.34 behavior, alter MIDI mappings, or
> authorize runtime implementation.

## Purpose

Capture the intended future shape of the audio analyzer and the
Reference/Discovery control so the idea survives the current hardware
validation and release-stabilization work.

The current product remains the V1.34-compatible four-pad Rytm randomizer. The
future analyzer layer should help turn reference material into safe mutation
guardrails, then let the user choose how closely the machine follows that
reference versus how far it explores.

## Current Foundation

The repository already has the early pieces for this direction:

- `rytm_randomizer/style_analysis/` can produce a deterministic
  `FeatureReport` from audio, folders, partial audio plus notes, or a written
  style description.
- `rytm_randomizer/guardrails/` defines and validates typed guardrail profiles.
- The `MusicLibraryGuardrails` skill interprets musical/style material into a
  draft guardrail profile.
- The optional `style` dependency group keeps audio analysis separate from the
  lean core install.
- `docs/FUTURE_ANALOG_FOUR_EXPANSION.md` captures the later cross-device
  direction for applying the same analyzer and slider ideas to Analog Four.
- `rytm_randomizer.machine_catalog` now provides the first passive bridge from
  analyzer-style essence tags to 12-pad Rytm role planning and candidate engine
  ranking.
- `essence-plan-report --tags <csv> --discovery <0..1>` exposes that bridge as
  a passive preview command before any real audio analyzer workflow is wired.
- `essence-plan-report --description <text> --discovery <0..1>` now derives
  broad, non-copying essence tags from written reference language before
  feeding the same passive 12-pad planner.
- `essence-application-readiness-report` now checks that plan against Safe
  Anchors or Live Snapshot and reports ready, blocked, and future-only pad
  reasons before any runtime mutation exists.
- `style-intent-report --style <text> --discovery <0..1>` now offers a
  second passive doorway beside reference-track analysis: broad style prompts
  such as Birmingham techno, dark techno, schranz, broken techno, or classic
  Detroit techno can feed the same non-copying 12-pad planner.

These pieces are not yet a polished end-user analyzer workflow.

## Core Control

The future user-facing macro control is:

```text
Reference |--------------------| Discovery
```

The slider is not a copying control. It adjusts how strongly the measured or
described reference constrains the randomizer.

Near **Reference**:

- Keep roles close to the analyzed material.
- Keep mutation ranges tighter.
- Preserve density, energy arc, low-end behavior, and texture more strongly.
- Favor stability for foundational elements such as kick and bass.

Near **Discovery**:

- Use the reference as a starting influence, then widen mutation ranges.
- Permit more surprise in percussion, texture, FX, and motion lanes.
- Preserve safety floors and forbidden parameters.
- Keep anchor return behavior available at all times.

Middle positions should preserve the reference's musical fingerprint while
allowing fresh variations.

## Future 12-Pad Role Model

Longer term, the analyzer should be able to map a reference track or library
onto a richer 12-pad Rytm layout. That future model is expected to treat pads
as musical roles rather than as anonymous slots.

Example role families:

- Kick / low-end foundation
- Secondary kick or low percussion
- Snare / clap / backbeat
- Bass or tonal percussion
- Closed hats / high pulse
- Open hats / ride energy
- Metallic percussion
- Noise / texture
- FX accent
- Fill / disruption
- Transition pressure
- Spare or user-defined role

The first passive 12-pad planning map now exists as metadata in
`rytm_randomizer.machine_catalog`. Pads 5-12 remain out of scope for the
current V1.34-compatible runtime. This checkpoint records product direction and
the passive planning bridge only.

## Per-Role Slider Behavior

The first version can be one global Reference/Discovery slider. Later versions
should allow role-level bias, for example:

- Keep kick close to reference.
- Let hats move moderately.
- Let percussion and FX explore widely.
- Keep bass pitch movement constrained unless explicitly loosened.

This would let a user keep the identity of a reference track while still using
the machine for original discovery.

## Copyright And Originality Boundary

The analyzer must extract musical tendencies, not copy protected material.

Allowed outputs:

- density tendencies
- energy arc
- low-end stability
- brightness and texture estimates
- role assignments
- mutation directions
- safe parameter bounds

Not allowed outputs:

- melodies
- arrangements
- sound-alike patch recipes
- instructions to clone a specific track
- copyrighted hooks or unique musical phrases

The goal is reference-informed original kit design: influence, not replica.

## Safety Boundary

This future feature must preserve the current safety principles:

- no new MIDI CCs without explicit approval
- no new machine/profile/range behavior without validation
- no hardware send path from passive analysis
- real MIDI remains gated behind explicit arming
- anchors and return-to-anchor commands remain first-class safety behavior
- Analog Four support remains a separate future workstream

## Proposed Future Sequence

1. Completed: first controlled Rytm MK2 hardware validation
   (2026-05-15).
2. Stabilize the V1.34-compatible release base.
3. Keep the existing style-analysis and guardrail schema tests green.
4. Completed: add a passive machine catalog / essence matcher bridge from
   future analyzer tags to 12-pad Rytm engine candidates.
5. Completed: expose a passive Essence Plan Preview CLI command for manually
   supplied essence tags and one global Reference/Discovery value.
6. Completed: connect written reference descriptions to the Essence Plan
   Preview through passive description-derived tags.
7. Completed: add a passive Essence Application Readiness gate for Safe
   Anchors versus Live Snapshot.
8. Completed: add a passive Style Intent Kit report for genre/tag prompts
   feeding the same 12-pad essence planner.
9. Design the first end-user analyzer workflow around one global
   Reference/Discovery slider.
10. Only after that, design the runtime 12-pad role map, Analog Four expansion, and any
   Pads 5-12 runtime support as separate approved implementation plans.

## Decision

The audio analyzer and Reference/Discovery slider remain part of the dream
project.

They are future-facing product direction, not current runtime scope. With the
first controlled Rytm MK2 hardware pass recorded, the next practical milestone
is stabilizing the V1.34-compatible release base.
