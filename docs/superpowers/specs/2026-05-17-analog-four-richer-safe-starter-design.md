# Analog Four Richer Safe-Starter Design

## Goal

Expand the Analog Four side of the dual-machine bridge from a tiny smoke-level
starter into a modest, musical, hardware-sendable starter plan.

The plan must help the current dual-machine snapshot flow feel useful when the
target is `analog-four` or `both`, while keeping the same safety rule:
only mapped, reference-known CC messages are eligible for real MIDI output.

## Current State

- Rytm snapshot plans can produce mapped CC events from saved kit snapshots.
- Analog Four saved-kit snapshot candidates remain intentionally blocked from
  real MIDI because their saved offsets are not yet proven CC mappings.
- The fallback Analog Four safe-starter plan is hardware-sendable but too thin:
  it sends only Filter 1 Frequency and Pan per track.

## Desired Starter Coverage

Use five conservative CC changes per Analog Four track:

- Track 1, bass / low tonal anchor:
  Track Level CC95, OSC1 Level CC69, OSC2 Level CC78,
  Filter 1 Frequency CC18, Amp Pan CC10.
- Track 2, stab / sequence pressure:
  Track Level CC95, OSC1 Waveform CC70, Filter 1 Frequency CC18,
  Amp Env Decay CC105, Amp Pan CC10.
- Track 3, pad / drone / atmosphere:
  Track Level CC95, OSC1 Level CC69, OSC2 Level CC78,
  Filter 2 Frequency CC19, Reverb Send CC93.
- Track 4, FX / noise / transition:
  Track Level CC95, Noise Level CC77, Noise Fade CC76,
  Filter 1 Frequency CC18, Amp Pan CC10.

This raises the A4 safe-starter stream from 8 to 20 mapped CC messages.
With the current synthetic Rytm fixture, the combined stream rises from 14 to
26 messages. With Jose's real Rytm project slot 1, target `both` should rise
from 68 to 80 accepted mapped CC messages.

## Non-Goals

- Do not send Analog Four saved-offset snapshot candidates to hardware.
- Do not claim NRPN coverage.
- Do not add continuous hardware tracking.
- Do not add Analog Four sound/engine selection yet.
- Do not change Rytm snapshot mutation behavior.

## Acceptance

- Existing A4 snapshot candidates remain blocked in active send plans.
- `--snapshot-target analog-four` emits only the 20 A4 safe-starter CC events.
- `--snapshot-target both` routes Rytm snapshot CCs and all 20 A4 starter CCs
  to the correct device ports.
- Reports show the richer track message counts without changing the safety
  language.
