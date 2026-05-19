# Machine Catalog And Essence Matcher Checkpoint

Date: 2026-05-18

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
- OS 1.72 pad/track machine compatibility for all 12 Rytm pads
- machine-selectable inventory for engines that can be selected by CC15
- a 12-pad role template aligned to the physical Rytm tracks
- a role matcher that ranks machines from role tags and reference essence tags
- Reference/Discovery behavior for planning:
  - reference side: only currently mapped mutable V1.34 machines
  - discovery side: includes machine-selectable inventory candidates

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
machine-selectable inventory candidates like SY Chip, Dual VCO, BT/XT toms,
hat engines, and cymbal/cowbell engines. Active engine-cycling runtime paths
must additionally enforce the OS 1.72 pad compatibility table before emitting
any CC15 machine select.

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

## Machine-Selectable Inventory

The catalog also tracks Rytm engines that have manual-backed CC15 machine
values but do not yet have full per-engine mutation maps:

- SY Chip
- Dual VCO
- RS Hard / RS Classic
- CP Classic
- BT Classic
- XT Classic
- CH/OH and HH hat engines
- CY/CB cymbal and cowbell engines
- UT Noise / UT Impulse

These engines can be selected by guarded CC15 paths when the runtime also has
a safe starter plan. Full freeform mutation still requires per-engine parameter
maps, safe ranges, fixtures, and hardware validation.

## Twelve-Pad Role Template

The current 12-pad essence template follows the Analog Rytm MKII OS 1.72
physical tracks:

- Pad 1: BD / Bass drum
- Pad 2: SD / Snare drum
- Pad 3: RS / Rim shot
- Pad 4: CP / Hand clap
- Pad 5: BT / Bass tom
- Pad 6: LT / Low tom
- Pad 7: MT / Mid tom
- Pad 8: HT / Hi tom
- Pad 9: CH / Closed hihat
- Pad 10: OH / Open hihat
- Pad 11: CY / Cymbal
- Pad 12: CB / Cowbell

The active engine-cycle/runtime planners use this same compatibility table, so
Pad 10 remains an open-hat lane and Pads 6-8 remain XT tom lanes.

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
