# Rytm Engine Cycle Plan Design

## Goal

Add a passive 12-pad Rytm engine-cycle planner that ranks real machine engines
per pad/style, including engines that have verified `CC15` machine values but
do not yet have tuned anchor profiles.

## Context

The current 12-pad snapshot essence path can already mutate all 12 pads and can
switch engines when the selected machine is one of the mapped V1.34-safe
profiles. The missing piece is visibility into the full Rytm engine palette:
hats, rims, claps, cymbals, utilities, SY Chip, SY Dual VCO, and other engines
are still treated as future/manual candidates, so style planning falls back to
the smaller mapped BD/SD/SY Raw set.

The SysEx decoder already knows the saved-kit machine values for the full Rytm
engine list, and the public MIDI guide confirms `Kit: Track Machine Type` is
`CC15` with values `1-33`, including the same machine names/values.

## Scope

In scope:

- Add a third machine support tier: `machine_selectable`.
- Promote identified engines with known machine values but no tuned anchor map
  into `machine_selectable`.
- Add a passive `rytm-engine-cycle-plan-report --style <text> [--discovery <0..1>]`.
- Rank candidate machines per existing 12-pad role and style intent.
- Capture the top ranked candidate per pad into a mock-only `CC15` stream.
- Report support status clearly: `mutable_v134` vs `machine_selectable`.

Out of scope:

- Real MIDI sending for the engine-cycle plan.
- Applying tuned anchors to `machine_selectable` engines.
- NRPNs.
- Live SysEx receive.
- Writing SysEx back to hardware.
- Continuous hand-knob tracking.

## Behavior

The report answers: "If this style wants a 12-pad kit, which engines should each
pad cycle through first?"

For each pad, the plan lists up to four ranked engine candidates. Each candidate
includes machine label, `CC15` value, support status, and matched tags. The mock
stream emits exactly one `CC15` event per pad for the top-ranked selectable
candidate. This proves the ordering and channel targeting without touching
hardware.

Existing snapshot essence and twelve-pad mock runtime behavior should remain
compatible. They can continue to require `mutable_v134` for anchor/mutation
events until generic starter anchors are explicitly designed and tested.

## Safety

- Passive CLI only.
- Mock sender only.
- No MIDI sending.
- No port opening.
- No hardware mutation.
- `machine_selectable` means engine switching is known, not full tuning.
