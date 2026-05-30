# Rytm Live Session Guardrails Design - 2026-05-29

## Goal

Add session-only live-performance controls to the Analog Rytm snapshot shell so
global mutations can hit the whole kit while respecting each pad's prepared
guardrails. The model should feel like an OXI-style global randomizer: one
command can mutate all active tracks, but each track/pad has its own allowed
movement range.

This first version is session-only. Settings reset when the shell exits. Saved
presets are a later upgrade.

## Operator Model

The shell starts from a freshly received or file-loaded current-kit SysEx
anchor. The operator can then set live guardrails before mutating:

```text
mode live
depth normal
pad 1 gentle
pad 3 strong
lock 5
status
4
changes
send
again
send
```

Global mutation commands still work quickly:

- `S1A`, `S3A`, `S3B`, `S4B`, and `4` mutate the full eligible kit.
- `Y`, `V`, and `N` mutate focused zones.
- `again` / `next` repeat the last mutation and create the next variation.
- `send` only transmits the staged plan.

The new rule is that every mutation command consults the current session
guardrails first.

## Modes

The shell gets a session mode:

- `live`: default. Tight ranges, especially for kick and other low-end anchors.
- `studio`: wider ranges for sound-design exploration.

Mode controls the maximum allowed movement for each depth. It does not change
the command vocabulary and does not enable machine switching, samples,
performance macros, source level, track level, amp volume, SysEx writes,
transport, pattern changes, or kit/project writes.

## Depths

The shell gets a global session depth:

- `gentle`: tiny movement, appropriate for live continuity.
- `normal`: musical movement, still controlled.
- `strong`: noticeable movement.
- `wild`: bigger movement, mainly for studio or intentional live drama.

Existing `micro`, `groove`, and `strong` prompts remain accepted for
compatibility. In live-session controls, `gentle` is the clearest operator word
for the safest depth. The implementation may internally map old depth names to
the new depth ladder.

## Pad Policies

Each pad can have a session policy:

- `lock N`: pad N receives no mutations.
- `unlock N`: pad N returns to mutation eligibility.
- `pad N gentle|normal|strong|wild`: pad N overrides the global depth.
- `pad N off`: alias for `lock N`.

Per-pad settings override global depth. Locked pads override all depth settings.

## Live Default Profile

When the shell starts in `live` mode, it should use these defaults:

| Pad | Typical Role | Default Policy |
|---:|---|---|
| 1 | kick / bass drum | gentle |
| 2 | snare or synth | normal |
| 3 | rim or synth | normal |
| 4 | clap, snare, or synth | normal |
| 5 | bass tom | gentle |
| 6 | low tom | gentle |
| 7 | mid tom | gentle |
| 8 | high tom | gentle |
| 9 | closed hat | gentle |
| 10 | open hat | gentle |
| 11 | cymbal / ride | normal |
| 12 | cowbell / cymbal | normal |

Pad 1 is gentle by default, not locked. It should change enough to stay alive
during a long set, but not enough to lose low-end weight unless the performer
explicitly raises its depth.

## Kick Guardrails

Pad 1 remains the most protected pad in live mode:

- Filter mode stays anchored.
- Filter frequency stays close to the captured value.
- Filter resonance stays close to the captured value.
- Tune and body/decay movement are smaller than comparable non-kick movement.
- Delay/reverb send changes remain small.

The performer can intentionally override Pad 1 with `pad 1 strong` or `pad 1
wild`, but live mode should still keep the existing Pad 1 filter safeguards.

## Status and Preview

Add `status` to show:

- current mode
- global depth
- locked pads
- per-pad depth overrides
- active event count

`preview` should continue showing the staged plan. It may include a compact
guardrail summary so the operator can see the current session setup before
sending.

`changes` should continue showing the actual parameter deltas, including
current-machine SRC rows on later pads.

## Mutation Semantics

For each event:

1. If the pad is locked, keep the current value unchanged.
2. Otherwise determine effective depth:
   - per-pad depth if set
   - global depth otherwise
3. Convert effective depth plus mode into an anchor-relative bounded delta
   window.
4. Apply the command's musical direction and generation jitter inside that
   window.
5. Apply existing parameter-specific guardrails, especially Pad 1 filter
   protection.

The command's intent still matters. For example, `Y` targets source rows, `V`
targets filter rows, and `N` targets grit-related rows. Session depth controls
how far eligible rows move, not which zone the command targets.

Live and studio depth windows are total movement envelopes around the captured
kit anchor, not per-command increments. Repeating `4`, `again`, or another
mutation command should create new variations inside the selected lane instead
of walking farther and farther away from the received kit.

## Error Handling

Invalid commands should be non-destructive and print a clear message:

- unknown mode
- unknown depth
- pad number outside 1-12
- missing pad number
- missing depth/policy

No invalid setup command should send MIDI or mutate the staged plan.

## Testing

Add focused tests for:

- default live session policy sets Pad 1 gentle and tom/hat pads gentle.
- `lock N` prevents that pad from changing during full-kit mutation.
- `unlock N` restores mutation eligibility.
- `pad N strong` overrides a gentle global depth.
- `mode live` produces smaller Pad 1 movement than `mode studio`.
- `status` reports mode, global depth, locks, and overrides.
- invalid setup commands do not mutate state and do not send MIDI.
- existing `send`, `again`, `changes`, and live-receive tests still pass.

Run the focused snapshot-shell tests, app tests, architecture tests, lint
checks, fast suite, and full suite before hardware testing.

## Hardware Retest

After implementation:

1. Start a fresh live snapshot shell.
2. Receive the current kit from the Rytm.
3. Set live guardrails:

   ```text
   mode live
   depth gentle
   pad 1 gentle
   status
   ```

4. Run a full-kit mutation such as `4`.
5. Inspect `changes`, especially Pad 1 and later-pad SRC rows.
6. Send and listen.
7. Use `again` for another controlled variation.
8. Try one intentional override such as `pad 3 strong`, then repeat mutation.

Stop if the kick loses low end, the wrong pad changes, monitoring becomes
unsafe, or the device shows any save/write/transport/pattern behavior.

## Later Upgrade

Saved presets come after session-only controls feel right. A later version can
add commands such as:

```text
savepreset live-safe
loadpreset live-safe
presets
```

That later work should define storage location, overwrite behavior, migration,
and validation separately.
