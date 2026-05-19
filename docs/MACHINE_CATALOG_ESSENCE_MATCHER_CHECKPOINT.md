# Machine Catalog And Essence Matcher Checkpoint

Date: 2026-05-16

## Purpose

The Machine Catalog and Essence Matcher is the first passive layer that turns
the future audio analyzer's musical observations into Rytm-native engine
choices.

The long-term goal is not to clone a reference track. It is to analyze a track's
energy, density, transient shape, metallic character, tonal movement, and
performance pressure, then choose 12 Analog Rytm pad roles and machine
candidates that can capture the essence of that track.

## Current Capability

The new passive `rytm_randomizer.essence.machine_catalog` module provides:

- machine-family metadata for the V1.34 mutable machines
- inventory placeholders for future engines that still need manual mapping
- a 12-pad role template for reference-driven kit planning
- a role matcher that ranks machines from role tags and reference essence tags
- Reference/Discovery behavior for planning:
  - reference side: only currently mapped mutable V1.34 machines
  - discovery side: includes inventory-only future machines as candidates

The passive CLI now exposes this through:

```powershell
python -m rytm_randomizer.cli essence-plan-report --tags metallic,bell,driving,repetition --discovery 0.35
```

It can also derive those broad tags from a written reference description:

```powershell
python -m rytm_randomizer.cli essence-plan-report --description "metallic bell pressure driving repetition Detroit techno" --discovery 1.0
```

This prints the 12-pad role plan and top candidate engines for each pad. The
same command with a high discovery value, such as `--discovery 1.0`, may show
future inventory candidates like SY Chip, Dual VCO, hat families, and cymbal
families, but those candidates remain blocked from real mutation until mapped
and validated.

The description path uses `rytm_randomizer.essence.tag_adapter`. It extracts
coarse musical tags only; it does not preserve artist names, track titles,
melodies, arrangements, or patch recipes.

The passive CLI also exposes a readiness gate:

```powershell
python -m rytm_randomizer.cli essence-application-readiness-report --mode safe-anchors --description "metallic bell driving repetition" --discovery 0.35
```

This reports whether the 12-pad plan is apply-ready under Safe Anchors or Live
Snapshot, and gives each pad a reason such as `mapped_pad_supported`,
`pads_5_12_not_runtime_supported`, `snapshot_not_captured`, or
`machine_needs_manual_mapping`.

This module is metadata and scoring only. It does not send MIDI, open ports,
request dumps, write SysEx, or mutate hardware.

## Current Mutable Machines

The catalog marks the currently mapped V1.34 machines as `mutable_v134`:

- BD Hard
- BD Classic
- BD Sharp
- BD Acoustic
- BD FM
- BD Plastic
- BD Silky
- SD Hard
- SD Classic
- SD FM
- SY Raw

## Future Inventory Machines

The catalog also tracks important future machine families as
`needs_manual_mapping`:

- SY Chip
- Dual VCO
- RS family
- CP family
- CH/OH hat family
- CY/CB cymbal family

These engines can appear in discovery planning, but they are not yet approved
for mutation. Each one still needs manual-backed machine values, parameter
maps, safe ranges, fixtures, and hardware validation.

## Twelve-Pad Role Template

The first 12-pad essence template is:

- Pad 1: main kick foundation
- Pad 2: secondary low percussion
- Pad 3: metallic motif
- Pad 4: body/accent hit
- Pad 5: closed hat pulse
- Pad 6: open hat / noise lift
- Pad 7: rim/click texture
- Pad 8: snare/clap pressure
- Pad 9: tonal bell accent
- Pad 10: open hat
- Pad 11: atmosphere/noise layer
- Pad 12: wild discovery lane

This is planning metadata only. It does not mean the runtime supports Pads 5-12
mutation yet.

## Audio Analyzer Relevance

A future analyzer might extract tags such as:

- `metallic`
- `bell`
- `driving`
- `repetition`
- `density`
- `noise`
- `tension`

The matcher can already rank candidate machines for those tags. For a
metallic, bell-like, driving reference, currently mapped engines such as BD FM
and SD FM rank as usable candidates. When Discovery is high, future engines
such as SY Chip and Dual VCO can be included as inventory candidates while
remaining blocked from real mutation until mapped.

The description adapter can now provide those tags from language before the
real analyzer workflow exists. The same adapter also accepts a passive
`FeatureReport`, so later audio analysis can feed the matcher without changing
the planner surface.

## Safety Boundary

This checkpoint adds no active behavior:

- no MIDI sending
- no port discovery
- no port opening
- no command execution
- no hardware mutation
- no SysEx receive/write behavior
- no real audio analysis
- no Pads 5-12 runtime mutation

## Next Step

The next useful passive slice is to add mock 12-pad snapshot fixtures, so Live
Snapshot readiness can be exercised against realistic captured pad/machine
inventories before any live receive path is authorized.
