# Style Intent Kit Design

Date: 2026-05-16

## Purpose

Reference-track analysis should not be the only way to design a kit. The user
should also be able to ask for a broad style direction, such as broken techno,
dark Birmingham techno, hardcore, schranz, classic Detroit techno, driving
techno, or peak-time techno, and have the software translate that into the same
12-pad kit-planning machinery.

## Design

Add `rytm_randomizer.style_intent_profiles`, a passive style-intent layer. It
maps broad genre/style phrases to essence tags and a suggested Discovery value.
The layer is intentionally descriptive rather than prescriptive: it does not
clone artists, tracks, arrangements, or patches. It simply chooses broad
musical tendencies such as pressure, repetition, metallic tone, density,
darkness, motion, and air.

The first profiles are:

- broken techno
- dark techno
- Birmingham techno
- hardcore
- schranz
- classic Detroit techno
- driving techno
- peak-time techno

Each profile records Analog Rytm relevance and Analog Four future relevance.
Analog Four remains future-only; no Analog Four machine maps or runtime behavior
are added here.

## CLI

Add:

```powershell
python -m rytm_randomizer.cli style-intent-report --style "Birmingham dark techno"
python -m rytm_randomizer.cli style-intent-report --style "classic Detroit techno" --discovery 0.45
python -m rytm_randomizer.cli essence-application-readiness-report --mode live-snapshot --style "schranz" --fixture am9-slot-01
```

The report prints matched profiles, derived essence tags, suggested Discovery,
and the passive 12-pad candidate plan. The readiness command can also accept
`--style` directly, using the style profile's Discovery hint unless the
operator overrides it with `--discovery`. That keeps the style prompt,
candidate plan, and per-pad ready/blocked/future-only gate connected.

## Safety Boundary

This design adds no active behavior:

- no audio analysis
- no MIDI sending
- no port opening
- no command execution
- no hardware mutation
- no live SysEx receive
- no Analog Four runtime support
- no Pads 5-12 runtime mutation
