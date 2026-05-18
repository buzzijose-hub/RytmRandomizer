# 12-Pad Rytm Engine Runtime Foundation Design

## Context

The project now has the passive pieces needed to start turning style intent into
12-pad Analog Rytm setup behavior:

- `rytm_randomizer.essence.machine_catalog` ranks Rytm machines for 12 pad
  roles and broad essence tags.
- `rytm_randomizer.essence.style_intent_profiles` translates prompts such as
  `Birmingham dark techno`, `schranz`, `classic Detroit techno`, and
  `peak-time techno` into deterministic tags and a discovery value.
- `rytm_randomizer.essence.rytm_engine_cycle_plan` chooses ranked machine
  candidates and already captures mock CC15 machine-select messages.
- `rytm_randomizer.essence.rytm_engine_cycle_starter_profiles` adds source
  starter values plus common filter/amp starter values.
- `rytm_randomizer.essence.twelve_pad_mock_runtime` proves a mapped-only
  12-pad mock runtime contract.

The next product milestone is to turn those planning layers into a clearer
guarded runtime foundation for all 12 Rytm pads. This is the bridge between
today's passive reports and the future performance workflow where the software
can dial in all 12 pads from style intent, then later from snapshots or audio
analysis.

## Goal

Build the first 12-pad Analog Rytm runtime foundation that starts from a style
prompt and produces a deterministic, inspectable, mock-first setup stream for
all 12 pads.

The stream should include:

- one machine select per planned pad via machine CC15;
- safe source starter values where the selected machine has source starter
  coverage;
- common filter/amp starter values;
- enough metadata to explain which style, role, pad, machine, and parameter
  caused each event.

## Non-Goals

This slice does not add:

- live snapshot capture;
- continuous tracking of manual knob tweaks;
- audio file analysis;
- Analog Four mutation;
- cross-device scene performance;
- pattern or sequencer mutation;
- SysEx writes;
- live SysEx request/receive;
- unguarded hardware sends.

Snapshot mode and the future audio analyzer remain first-class roadmap items,
but they should reuse this runtime send foundation instead of being built as
parallel send paths.

## Recommended Approach

Use the existing style-intent and engine-cycle planning stack as the source of
truth, then add one runtime-facing plan/report layer.

The new runtime layer should consume:

1. a style prompt;
2. an optional discovery value;
3. an optional starter profile mode;
4. the existing engine-cycle candidate plan.

It should output a single ordered 12-pad setup event stream:

1. CC15 machine select events;
2. source starter CC events for selected machines with source starter coverage;
3. common filter/amp starter CC events;
4. explicit skipped/blocked metadata for pads or machines without enough
   starter coverage.

The runtime layer should stay mock-only first. After the mock contract is
stable, add guarded dry-run and hardware send wrappers using the same safety
style as the existing `snapshot_*_guarded_sender`,
`snapshot_*_hardware_sender`, `dual_machine.guarded_sender`, and
`dual_machine.hardware_sender` modules.

## Architecture

### Existing Components

`essence.machine_catalog`

Owns 12-pad role templates and ranked Rytm machine candidates. It should remain
planning metadata only.

`essence.style_intent_profiles`

Owns broad genre/style prompt parsing. It should continue to produce a
deterministic tag set and discovery value.

`essence.rytm_engine_cycle_plan`

Owns style-driven machine candidate selection and CC15 mock preview.

`essence.rytm_engine_cycle_starter_profiles`

Owns starter shaping data and event generation for source/common starter values.

### New Runtime-Facing Contract

Add a focused plan module, likely under `rytm_randomizer.essence`, that produces
a `TwelvePadRytmRuntimePlan`.

The plan should contain:

- `style_prompt`;
- `matched_profile_labels`;
- `essence_tags`;
- `discovery`;
- ordered per-pad plans;
- ordered send events;
- blocked/skipped event explanations;
- aggregate counts for machine selects, source starters, common starters,
  blocked pads, and skipped parameters.

Each send event should contain:

- `pad`;
- `midi_channel`;
- `wire_channel`;
- `machine_key`;
- `machine_label`;
- `machine_value`;
- `event_role`;
- `parameter_name`;
- `cc`;
- `value`;
- `source`;
- `sends_real_midi=False` for mock reports;
- safety metadata used by guarded senders later.

The event order must be deterministic:

1. Pad 1 machine select;
2. Pad 1 source starters;
3. Pad 1 common starters;
4. Pad 2 machine select;
5. Pad 2 source starters;
6. Pad 2 common starters;
7. continue through Pad 12.

This ordering makes reports and hardware behavior easier to audit.

## Operator Experience

The first CLI/report should stay passive:

```powershell
python -m rytm_randomizer.cli twelve-pad-rytm-runtime-report --style "Birmingham dark techno" --discovery 0.35
```

The report should show:

- style prompt;
- matched profiles;
- essence tags;
- discovery value;
- pad-by-pad selected machine;
- which pads use full starter coverage;
- which pads use machine-select-only coverage;
- mock message counts;
- the exact mock CC stream;
- safety text.

Later active app entry points should follow the existing pattern:

```powershell
rytm-randomizer --dry-run --twelve-pad-rytm-runtime --style "Birmingham dark techno"
rytm-randomizer --arm --twelve-pad-rytm-runtime --style "Birmingham dark techno"
```

The active hardware path should be added only after the passive CLI and mock
sender behavior are stable.

## Safety Model

The first implementation must be passive/mock-only:

- no `mido` import at module import time;
- no port opening;
- no real MIDI send;
- no SysEx receive;
- no SysEx writes;
- no hardware mutation.

When a guarded sender is added:

- `--arm` is required;
- caller must inject an already selected/open Rytm output port;
- only Analog Rytm MKII events are eligible;
- event stream must reject non-ready plans;
- dry-run sender must accept only `MockMidiSender`;
- hardware sender must refuse skipped/blocked events and report exactly how
  many events were emitted.

## Relationship To Snapshot Mode

This style-prompt runtime foundation is not a replacement for snapshot mode.

Snapshot mode should later reuse the same event stream and guarded sender
interfaces, but swap the source of starter values:

- style runtime uses catalog/starter-profile values;
- snapshot runtime uses captured kit values as the baseline;
- audio analyzer runtime eventually chooses style/essence tags and target
  roles from a reference track, then uses the same engine/runtime foundation.

This keeps one send pipeline instead of three separate hardware paths.

## Test Strategy

Add tests in small layers:

1. passive import safety for the new runtime module;
2. style prompt creates 12 pad plans;
3. deterministic event ordering;
4. machine select count equals planned pads;
5. source/common starter counts are explicit;
6. mock sender captures the exact event stream;
7. report includes pad summaries, counts, and safety text;
8. CLI reads style/discovery arguments without hardware;
9. app dry-run path, if included in this slice, captures mock messages only;
10. architecture tests continue to pass with no new top-level modules.

## Success Criteria

This milestone is done when:

- a style prompt can produce a deterministic 12-pad Rytm runtime plan;
- the report explains all selected machines and starter events;
- mock sender captures the full ordered stream;
- no hardware is touched in passive paths;
- no new top-level modules are added;
- existing snapshot essence, dual-machine, and Analog Four behavior is
  unchanged;
- full fast tests and architecture tests pass.

## Open Follow-Ups

- Add guarded `--dry-run` and `--arm` app entry points after the passive runtime
  report is stable.
- Add live snapshot baseline runtime planning that uses captured kit values
  rather than style starter values.
- Add audio analyzer to derive essence tags and discovery settings from a
  reference track.
- Extend equivalent runtime planning to Analog Four after the Rytm send
  foundation is stable.
