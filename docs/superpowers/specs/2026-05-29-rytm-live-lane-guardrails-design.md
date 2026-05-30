# Rytm Live Lane Guardrails Design - 2026-05-29

## Goal

Make the Analog Rytm snapshot shell musically trustworthy as a live sound-design
performer beside an OXI sequencer. The OXI decides when notes, triggers, mutes,
and pattern changes happen. RytmRandomizer changes what the captured Rytm kit
becomes when those notes happen.

## Live Model

- `randomize` proposes a safe sound-design variation from the captured kit.
- `go` generates and sends the next variation.
- `kit` listens for a newly loaded Rytm kit and makes that the new anchor.
- `z` plus `send` returns the Rytm to the captured safe kit.
- `preset live`, `preset kick-safe`, and per-pad depth controls remain the
  fast performance controls.

The shell should support variation without changing the pattern, controlled
scene changes between sections, protected anchors such as kick and snare, more
movement on hats and synth voices, mid-set kit capture, and emergency reset.

## Lane Guardrails

Add session-only lane guardrails over the existing pad/depth system:

```text
lane tune off|micro|normal|wide
lane noise off|micro|normal|wide
lane fx off|micro|normal|wide
lane filter off|micro|normal|wide
lane amp off|micro|normal|wide
lane lfo off|micro|normal|wide
```

Lane settings reset when the shell exits and are preserved when `kit` /
`resnapshot` replaces the captured anchor during the same session. They should
be visible in `status` before sending.

## Defaults

Defaults favor live trust:

- `tune=micro`
- `noise=normal`
- `fx=micro`
- `filter=normal`
- `amp=normal`
- `lfo=off`

Pad and role guardrails still apply. Pad 1 remains protected by the existing
kick-foundation policy: Pad 1 filter, LFO, and AMP attack are omitted from
active sends, and Pad 1 source tuning stays close to the captured kit value.

## Semantics

For each candidate event:

1. Apply existing pad lock and Pad 1 foundation checks.
2. Classify the event into a lane when possible.
3. If the lane is `off`, leave the value anchored and omit that event from
   active sends.
4. If the lane is `micro`, `normal`, or `wide`, cap the event's effective
   movement depth to that lane before applying command or randomizer intent.
5. Existing per-pad depth, live/studio caps, tune policy, selector handling,
   and anchor-relative drift prevention remain in force.

This design is deliberately a permission layer, not a new randomization engine.

