# Rytm OXI-Style Randomizer Design - 2026-05-29

## Goal

Add an OXI-inspired randomizer layer to the Analog Rytm live snapshot shell. The
operator should set per-pad musical guardrails once, then press a global
randomize command repeatedly to generate new kit variations that respect those
guardrails.

The feature should feel like a creative collaborator, not a raw value
scrambler. It must keep the current-kit snapshot as the anchor and never walk
unbounded away from the loaded kit during repeated live performance.

## First Version Scope

This first pass extends the current snapshot shell only. It does not add a GUI,
saved presets, pattern note generation, machine switching, kit writes, project
writes, transport, performance macros, samples, source level, track level, or
amp volume changes.

The shell already has:

- current-kit snapshot anchoring
- `go` for next variation and send
- `mode live|studio`
- `depth gentle|normal|strong|wild`
- `tune off|micro|normal|wide`
- per-pad locks and depth overrides
- Pad 1 foundation protection

This design adds per-pad randomizer contracts on top of that.

## Operator Model

The operator configures guardrails before performing:

```text
pad 1 role kick
pad 1 density low
pad 1 bias tighter
pad 1 amount micro

pad 2 role synth
pad 2 density medium
pad 2 bias darker
pad 2 amount normal

pad 9 role hat
pad 9 density high
pad 9 bias brighter
pad 9 amount normal

status
go
go
go
```

The important behavior: `go` remains global, but each pad interprets it through
its own contract.

## Concepts

### Amount

Amount controls how far a touched parameter may move from the captured anchor.
It maps onto the existing session-depth window:

- `micro`: very small live movement
- `normal`: noticeable but controlled movement
- `wide`: larger movement, still bounded

For the first version, `amount` can reuse the existing pad depth override:

- `micro` -> `gentle`
- `normal` -> `normal`
- `wide` -> `strong`

Studio `wild` remains available through existing commands, but the OXI-style
layer should not default to it.

### Density

Density controls how many eligible parameters on a pad are touched per
variation. It does not control movement size.

- `off`: touch none of the pad's eligible parameters
- `low`: touch about 25 percent
- `medium`: touch about 50 percent
- `high`: touch about 75 percent
- `full`: touch every eligible parameter

Density is deterministic per generation and event, so repeated `go` commands
produce stable, testable variation shapes while still feeling random to the
operator.

### Bias

Bias controls the musical tendency of movement, not a hard rule. The first
version should support these biases:

- `neutral`: no directional weighting
- `darker`: filter tends down, space restrained, resonance may rise slightly
- `brighter`: filter tends up, transients and hats can open
- `tighter`: decay/hold/release tend down, space restrained
- `looser`: decay/hold/release and space tend up
- `grittier`: overdrive/resonance/transient/noise-adjacent rows are more likely

Bias should affect both event selection and delta direction, but all changes
must still remain inside the pad amount, tune lane, value metadata, and live
safety protections.

### Role

Role is a musical hint for safer defaults. The first version can infer a default
role from the current machine, then let the operator override it:

- `kick`
- `snare`
- `tom`
- `hat`
- `cymbal`
- `synth`
- `noise`
- `perc`

Role affects default density and allowed parameter families. For example, `kick`
is sparse and conservative; `hat` can tolerate more filter/decay variation;
`synth` can tolerate more source/filter/LFO movement.

## Pad Contract

Each pad has a contract:

```text
role: inferred or user-set
amount: micro|normal|wide
density: off|low|medium|high|full
bias: neutral|darker|brighter|tighter|looser|grittier
locked: existing lock state
```

Existing commands remain valid. The contract only adds a new selection layer
before the current mutation math.

## Command Surface

Add these commands:

```text
pad N role kick|snare|tom|hat|cymbal|synth|noise|perc|auto
pad N amount micro|normal|wide
pad N density off|low|medium|high|full
pad N bias neutral|darker|brighter|tighter|looser|grittier
randomize
```

`randomize` is an alias for global OXI-style generation. It can share the
existing `go` send behavior later, but the first implementation should keep it
as staged-only unless the existing `go` path explicitly calls it.

The `status` output should include a compact randomizer summary:

```text
randomizer pads: 1=kick/micro/low/tighter, 2=synth/normal/medium/darker
```

## Mutation Flow

For each candidate event:

1. Reject if the pad is locked.
2. Reject if existing live safety rejects it.
3. Determine the pad contract.
4. Reject if density selection says this event is not touched for this
   generation.
5. Apply the existing zone and command match logic.
6. Apply amount as the effective pad depth.
7. Apply tune lane rules for source tune/detune rows.
8. Apply bias to select the preferred sign or family emphasis.
9. Clamp to anchor-relative windows and value metadata.

The source of truth remains the captured snapshot anchor.

## Defaults

Default contracts should be inferred from current machine role and should remain
live-safe:

| Role | Amount | Density | Bias |
|---|---|---|---|
| kick | micro | low | tighter |
| snare | normal | medium | neutral |
| tom | micro | medium | tighter |
| hat | normal | high | brighter |
| cymbal | normal | medium | brighter |
| synth | normal | medium | neutral |
| noise | micro | low | neutral |
| perc | normal | medium | neutral |

Pad 1 still receives the existing foundation protections even if its role is
overridden.

## Testing

Add focused tests for:

- default contracts are inferred for all 12 pads
- `pad N density low` touches fewer eligible rows than `pad N density full`
- `pad N density off` suppresses pad changes without requiring a lock
- `pad N bias brighter` tends filter frequency upward for eligible filter rows
- `pad N bias tighter` tends decay/hold/release downward
- `pad N amount wide` permits wider movement than `pad N amount micro`
- `status` reports the compact randomizer contract summary
- invalid role/amount/density/bias commands are non-destructive
- existing live safety, `tune off`, locks, resnapshot, and `go` tests still pass

## Hardware Test

After implementation:

1. Start a fresh live snapshot shell.
2. Receive the current Rytm kit.
3. Run `status` and confirm inferred per-pad contracts.
4. Set one conservative kit:

   ```text
   pad 1 density low
   pad 1 bias tighter
   pad 2 density medium
   pad 2 bias darker
   pad 9 density high
   pad 9 bias brighter
   tune micro
   ```

5. Run `randomize`, then `changes`.
6. Send only after inspecting the changes.
7. Try repeated `go` or `randomize` variations and listen for musical continuity.

Stop if a kick loses low end, SY Raw noise jumps, a selector shows invalid
hardware state, the device shows transport/pattern/save behavior, or density
does not audibly change how much of a pad moves.

## Later Upgrades

Later versions can add:

- saved randomizer presets
- named musical scenes such as `build`, `breakdown`, `darken`, `open-hats`
- per-parameter family ranges
- cross-pad cohesion controls
- pattern-level note/trigger randomization
- a visual editor for pad contracts
