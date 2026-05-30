# Rytm Selector Discovery Design - 2026-05-30

## Goal

Make explicit per-pad discovery settings affect selector-style sound controls
such as BD Acoustic `Waveform`, SY Raw waveform rows, filter mode, and LFO
waveform. The current live randomizer is musically useful, but selector rows can
stay unchanged at range edges even when a performer sets a pad to `amount wide`
and `density full`.

## Design

Keep default live behavior cautious. Selector controls should still move by one
step without wrap for normal live commands and non-wide randomizer settings.

When `randomize` is using a pad contract with `amount wide`, selector rows that
survive density, lock, lane, and Pad 1 foundation checks may choose a different
legal value from the selector range. The choice should be deterministic for the
same command, generation, pad, parameter, machine, and anchor value, so `go`
stays reproducible and `Z` can still return to the captured anchor.

Lane policy remains the outer permission layer. If a selector belongs to a lane
set to `off`, it is not sent or mutated. If a selector belongs to a lane set to
`micro`, it keeps the existing one-step live behavior even when the pad amount
is wide. Machine SRC selector rows that do not belong to a lane, such as BD
Acoustic `Waveform`, can use wide selector discovery.

## Out Of Scope

- No new `discover` command in this slice.
- No machine switching.
- No default live-profile widening.
- No changes to continuous amount/density/bias behavior.
- No parity fixture regeneration.

## Acceptance

- `pad 2 amount micro`, `pad 2 density full`, `randomize` keeps a BD Acoustic
  waveform at the top edge unchanged in live mode.
- `pad 2 amount wide`, `pad 2 density full`, `randomize` changes that same
  waveform to a different value inside the legal `0..11` selector range.
- Existing snapshot-shell lane, randomizer, send, and reset tests remain green.

