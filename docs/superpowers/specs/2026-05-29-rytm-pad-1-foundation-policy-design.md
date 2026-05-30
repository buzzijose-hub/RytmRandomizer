# Rytm Pad 1 Foundation Policy Design

## Context

Hardware testing on May 29, 2026 showed that the all-12-pad snapshot shell is
musically useful, but Pad 1 needs a stricter role than the other tracks. In
techno, Pad 1 is normally the kick foundation. The current shell lets Pad 1
participate in live, all-gentle, and studio mutations, but it still stages and
sends filter, LFO, and AMP attack-time changes. On hardware, those are too
destructive for the kick anchor.

## Approved Behavior

Pad 1 remains available for controlled character movement when it is not locked,
but the shell treats the following events as foundation-protected:

- Every Pad 1 `FILTER` page parameter.
- Every Pad 1 `LFO` page parameter.
- Pad 1 `AMP Amp Attack Time`.

Foundation-protected events must not be mutated and must not be sent. This keeps
the Rytm from receiving redundant CC messages for protected kick controls.

Pad 1 tuning parameters use the captured kit value as their anchor. The shell may
move any Pad 1 source parameter whose name contains `Tune`, but the staged value
must stay within plus or minus 3 of the captured value in every session mode,
including `studio`.

Other Pad 1 source and AMP parameters continue to use the existing live/studio
depth lanes for now. `preset kick-safe` keeps its existing stronger behavior: it
locks Pad 1 completely and auditions only the rest of the kit.

## Implementation Shape

The policy belongs in `rytm_randomizer/engines/analog_rytm_snapshot_shell.py`,
next to the snapshot-shell guardrail logic. It should be expressed as small
private predicates so mutation, status, preview, and send filtering all share the
same definition of active events.

The tests live in `tests/test_analog_rytm_snapshot_shell.py`, where the current
snapshot-shell behavior and hardware-derived guardrails are already covered.

## Verification

Focused tests should prove that:

- Pad 1 protected filter, LFO, and AMP attack events are excluded from sends.
- Pad 1 protected events do not appear as staged changes after mutation.
- Pad 1 `Tune` remains within plus or minus 3 of the captured value in `studio`
  with a wild Pad 1 override.
- Existing full-pad locks, presets, and send counts still work with the active
  event filter.

Operator docs should record the hardware lesson so future sessions start from
the same kick-foundation rule.
