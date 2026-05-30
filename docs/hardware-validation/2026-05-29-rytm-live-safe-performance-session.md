# Analog Rytm Live-Safe Performance Mutation Session - 2026-05-29

Purpose: preserve the live hardware lessons from the first snapshot-grounded
Analog Rytm performance mutation session so work can resume without rebuilding
context.

## Hardware Context

- Device under test: Elektron Analog Rytm MKII over USB.
- Output port used during this session: `Elektron Analog Rytm MKII 2`.
- Output index observed in this Windows session: `2`.
- Input/capture workflow: user sends current kit from the Rytm SysEx menu.
- SysEx receive note: raw `rtmidi` input with SysEx enabled captured the kit
  reliably; the earlier `mido` listener did not reliably see the SysEx frame in
  this setup.

## Latest Captured Kit

- SysEx file:
  `captures/20260528-232829-analog-rytm-current-kit-reassembled.syx`
- JSON decode:
  `captures/20260528-232829-analog-rytm-current-kit-reassembled.json`
- Kit name decoded: `KIT 1`
- Current raw-kit fingerprint: `e882fbf28513c226` (the older JSON sidecar was
  produced before raw-kit header/trailer stripping was corrected).
- Decoded machine values by pad after masking the stored high bit:
  `{1: 0, 2: 26, 3: 32, 4: 28, 5: 7, 6: 8, 7: 8, 8: 8, 9: 24, 10: 33, 11: 25, 12: 12}`
- The snapshot shell now decodes current SRC/filter/amp/LFO raw-kit fields from
  the 2610-byte kit payload and stages live-safe CC MSB sends from those
  captured values. It includes the current loaded machine's SRC rows on all 12
  pads while still excluding source level, track level, amp volume, and machine
  switching.
- The snapshot shell also has session-only guardrails: `mode live|studio`,
  `depth gentle|normal|strong|wild`, `lock N`, `unlock N`, `pad N
  gentle|normal|strong|wild|off`, `preset live|kick-safe|all-gentle|studio`,
  `guards reset`, and `status`. These reset when the shell exits; saved preset
  persistence remains a later upgrade. `status` separates active pad overrides
  from inactive overrides parked behind locked pads. Depth lanes are total
  anchor-relative envelopes, so repeated mutations must not drift away from the
  received kit by accumulation.

## Commands That Exist Now

Dry-run the latest captured kit:

```powershell
python -m rytm_randomizer.app --dry-run --rytm-performance-snapshot captures\20260528-232829-analog-rytm-current-kit-reassembled.syx --rytm-performance-mode live-safe --rytm-performance-style flow-shift --rytm-performance-depth safe --rytm-performance-seed 890002068
python -m rytm_randomizer.app --dry-run --rytm-snapshot-shell captures\20260528-232829-analog-rytm-current-kit-reassembled.syx
```

Fresh live snapshot shell:

```powershell
python -m rytm_randomizer.app --arm --rytm-live-snapshot-shell --confirm-rytm-snapshot-shell-send
```

Inside that live shell, `kit` or `resnapshot` waits for another Rytm KIT SysEx
dump from the same selected input, replaces the captured anchor, clears the
staged mutation, and keeps the current session guardrails.

Armed send of the corrected same-seed plan:

```powershell
'2' | python -m rytm_randomizer.app --arm --rytm-performance-snapshot captures\20260528-232829-analog-rytm-current-kit-reassembled.syx --rytm-performance-mode live-safe --rytm-performance-style flow-shift --rytm-performance-depth safe --rytm-performance-seed 890002068 --confirm-rytm-performance-send
```

Focused verification:

```powershell
python -m pytest tests/test_analog_rytm_performance_mutation.py tests/test_app_validate_one_cc.py -n 0
python -m ruff check rytm_randomizer\devices\strategies\analog_rytm_performance_mutation.py tests\test_analog_rytm_performance_mutation.py
python -m black --check --target-version=py311 rytm_randomizer\devices\strategies\analog_rytm_performance_mutation.py tests\test_analog_rytm_performance_mutation.py
python -m isort --profile black --check-only rytm_randomizer\devices\strategies\analog_rytm_performance_mutation.py tests\test_analog_rytm_performance_mutation.py
```

## What Live-Safe Means After Tonight

- `live-safe` must not send `Track Machine Type` CCs.
- `live-safe` must not write SysEx, save kits, save projects, change patterns,
  send transport, or touch volume/level defaults.
- `live-safe` may send CC MSB values only.
- `live-safe` should vary values by seed while preserving the event shape.
- `live-safe` should cover all 12 pads when compatible safe/manual events exist.
- Pad 1 kick remains the low-end anchor. It needs narrower guardrails than the
  rest of the kit.

## Hardware Lesson: Pad 1 Filter Frequency

Bad result:

- Seed: `890002068`
- Mode/depth: `live-safe` / `safe`
- First hardware send gave Pad 1:
  - `SRC Tune`: `61`
  - `SRC Decay`: `71`
  - `Filter Frequency`: `62`
- User feedback: terrible result. The kick disappeared because the filter
  frequency jumped from the low anchor area around `25` up to `62`.

Root cause:

- The Pad 1 kick-specific live-safe filter guardrail allowed `48..82`.
- That treated a midrange filter value as safe even though the captured/style
  anchor was low and the filter mode may not be decoded yet.

Fix applied:

- Pad 1 `Filter Frequency` at `safe` depth is now anchored near the style/current
  low value with a window of `4`.
- Regression test added for seed `890002068`; Pad 1 kick filter must stay within
  `21..29`.
- Corrected same-seed plan now gives Pad 1:
  - `SRC Tune`: `61`
  - `SRC Decay`: `71`
  - `Filter Frequency`: `24`

Corrected plan was sent to hardware after verification.

## Hardware Lesson: Session Presets

Latest live snapshot-shell validation used KIT 4 from the Analog Rytm MKII:

- Live receive: `KIT 4`, fingerprint `3ad9669b30e1ef27`.
- MIDI input index: `0`, `Elektron Analog Rytm MKII 0`.
- MIDI output index: `1`, `Elektron Analog Rytm MKII 1`.
- `preset live` applied `mode: live`, `global depth: gentle`, no locks, no
  active or inactive overrides, and `active event count: 335`.
- `preset live` + `4` + `send` sent `335` messages. Pad 1 remained present and
  stayed inside the gentle kick lane.
- `preset kick-safe` applied `mode: live`, `global depth: gentle`, `locked pads:
  1`, no overrides, and `active event count: 306`.
- `preset kick-safe` + `4` + `changes` omitted Pad 1 entirely; `send` sent
  `306` messages.
- `preset all-gentle` cleared locks and overrides, returned to `active event
  count: 335`, and sent `335` messages after mutation.
- `preset studio` applied `mode: studio`, `global depth: wild`, no locks, no
  overrides, and `active event count: 335`. Status showed studio caps of
  Pad 1=`strong` and pads 2-12=`wild`, and `changes` showed the expected wider
  deltas.
- `guards reset` restored `mode: live`, `global depth: normal`, no locks, no
  active or inactive overrides, and `active event count: 335`.
- Total shell send count for this validation run: `1311` messages.

Conclusion: the session preset UX is structurally hardware-validated. It should
remain session-only for now; saved preset persistence is still separate work.

## Hardware Lesson: Pad 1 Foundation Policy

Follow-up studio testing on KIT 5 (`1af76ee2729f862b`) showed that Pad 1 needs a
stricter kick-foundation role even when it is not fully locked by `preset
kick-safe`.

- Pre-policy `preset live` and `preset all-gentle` kept Pad 1 active, but still
  staged and sent Pad 1 filter, LFO, and AMP attack-time changes.
- Pre-policy `preset studio` made the problem much louder: Pad 1 filter, LFO,
  AMP attack, and wide source changes moved together, which is too risky for a
  techno kick foundation.
- The adopted policy keeps Pad 1 available for controlled character movement,
  but omits every Pad 1 filter event, every Pad 1 LFO event, and Pad 1
  `AMP Amp Attack Time` from the active send plan.
- Pad 1 source tuning parameters now stay within plus or minus 3 of the
  captured kit value in all modes, including `studio`.
- `preset kick-safe` remains the full lock option when the kick should be
  completely untouched.

KIT 13 (`4e32243208cc7fe5`) validated the policy on hardware:

- `preset live` reported `active event count: 326`, omitted Pad 1 filter, LFO,
  and `AMP Amp Attack Time`, kept Pad 1 `Tune: 59 -> 58`, and sent `326`
  messages.
- `again` preserved the same Pad 1 protection and sent `326` messages.
- `preset studio` + `pad 1 wild` + `S3A` reported `active event count: 326`,
  kept Pad 1 `Tune: 59 -> 62`, omitted protected Pad 1 pages, and sent `326`
  messages.
- `preset kick-safe` fully locked Pad 1, reported `active event count: 313`,
  showed no `Pad 01` change lines, and sent `313` messages.
- `preset all-gentle` cleared the Pad 1 lock and returned to `active event
  count: 326`.
- Fresh `Y strong` allowed Pad 1 source movement, kept `Tune: 59 -> 60`,
  omitted protected Pad 1 pages, and sent `326` messages.
- Fresh `V micro` showed filter-only changes on pads 2-12, no `Pad 01` lines,
  and sent `326` messages.
- Zone commands were observed to layer on the current staged plan. Use `fresh`
  or `Z` before `Y`, `V`, or `N` when testing an anchor-only zone mutation.

## Hardware Lesson: Live Lane Guardrails

Follow-up live testing validated the tune/noise/fx/filter/amp/lfo lane
guardrail model as a musical performance layer, not just a mechanical safety
layer.

KIT `SIDECHN05` (`0e1ce3fd186e4b92`) validated the current defaults on hardware:

- MIDI input index: `0`, `Elektron Analog Rytm MKII 0`.
- MIDI output index: `1`, `Elektron Analog Rytm MKII 1`.
- `preset live`, `lane lfo off`, `lane fx micro`, `randomize`, `send` sent
  `242` messages and was reported as musical and usable on the first pass.
- `fresh`, `lane fx normal`, `randomize`, `changes`, `send` still sent `242`
  messages because LFO remained off; FX movement behaved as a controlled
  section-change lane.
- `fresh`, `lane fx micro`, `lane lfo micro`, `randomize`, `send` sent `319`
  messages. The added LFO rows were small micro moves and stayed musically
  usable.
- Repeated `go` with LFO micro enabled sent `319` messages per variation and
  stayed inside the live-performance trust envelope.
- `Z`, `send`, `changes` restored the captured anchor; `changes` ended with
  `no parameter changes staged`.
- Total shell send count for this validation run: `2717` messages.

User feedback was the strongest acceptance signal so far: repeated `go`
auditioning was fun enough that generated kits were saved on the Analog Rytm for
future performances. The current live model feels performance-usable beside the
OXI: OXI controls note, trigger, mute, and pattern motion while RytmRandomizer
rides sound-design variation between sections.

Conclusion: keep the current live lane defaults for this PR. Further work should
push expressiveness through explicit performer controls such as per-pad
amount/density/bias and optional saved performance presets, not by making the
default live profile riskier.

## Hardware Lesson: Selector Discovery Target

Follow-up listening on `SIDECHN05` found that `pad 2 amount wide` and `pad 2
density full` produced excellent BD Acoustic variations, but the BD Acoustic
`Waveform` selector did not move when it sat at the edge of its legal range.
This is expected from the first live-safe selector rule: selector rows moved one
step without wrapping, so a top-edge selector could clamp back to the same
value.

The next selector-discovery behavior is intentionally opt-in. Default live
commands and non-wide randomizer contracts stay cautious, but explicit
`amount wide` randomizer contracts may pick a different legal selector value
when lane policy allows it. Lane `micro` remains stronger than amount-wide
discovery for lane-owned selectors such as LFO waveform.

Hardware target for the next pass:

```text
preset live
lane lfo off
lane fx micro
pad 2 amount wide
pad 2 density full
pad 2 bias looser
pad 3 amount wide
pad 3 density full
pad 3 bias grittier
randomize
changes
send
go
changes
send
Z
send
```

Listen specifically for whether Pad 2 BD Acoustic waveform changes feel like
useful kick-shape discovery or too much identity drift.

## Hardware Lesson: Selector Discovery Validation

Follow-up hardware testing confirmed that explicit `amount wide` selector
discovery now moves BD Acoustic waveform choices during live snapshot
randomization while still restoring cleanly to the captured anchor.

KIT `SIDECHN05` (`0e1ce3fd186e4b92`) was captured again on hardware:

- MIDI input index: `0`, `Elektron Analog Rytm MKII 0`.
- MIDI output index: `1`, `Elektron Analog Rytm MKII 1`.
- Commands used:
  `preset live`, `lane lfo off`, `lane fx micro`, `pad 2 amount wide`,
  `pad 2 density full`, `pad 2 bias looser`, `pad 3 amount wide`,
  `pad 3 density full`, `pad 3 bias grittier`, then repeated
  `randomize` / `go`, `changes`, and `send`.
- First `randomize` showed Pad 2 `bd_acoustic Waveform: 6 -> 11` and sent
  `242` messages.
- First `go` showed Pad 2 `bd_acoustic Waveform: 6 -> 8` and sent `242`
  messages.
- Second `go` showed Pad 2 `bd_acoustic Waveform: 6 -> 1` and sent `242`
  messages.
- Pad 3 `sd_fm` also moved as intended under its wide/grittier contract,
  including FM/noise rows and filter-mode changes.
- `Z`, `send`, and `changes` restored the captured anchor; the shell reported
  `no parameter changes staged`.
- Total shell send count for this validation run: `1452` messages.

Conclusion: selector discovery is hardware-validated for the original concern:
Pad 2 BD Acoustic `Waveform` can now change during explicit wide discovery
without requiring default live selector behavior to become riskier. This keeps
the live-performance model intact: wide per-pad contracts are discovery moves,
while `preset live` defaults remain trustworthy for repeated section changes.

## Hardware Lesson: Drum-Core Bias Shorthand

The first drum-core discovery pass added Pad 4 to the explicit wide-discovery
target beside pads 2 and 3. The shell correctly applied `pad 4 amount wide` and
`pad 4 density full`, but the natural performance command `pad 4 grittier` was
rejected because the shell previously required the longer `pad 4 bias grittier`
form.

Follow-up code makes `pad N darker|brighter|tighter|looser|grittier|neutral`
an operator shorthand for `pad N bias VALUE`. This is a live-UX improvement
only; it changes the command surface, not the randomizer contract semantics.

## Safe Resume Steps For Tomorrow

1. Start with a fresh current-kit SysEx capture from the Rytm.
2. If the hardware kit changes during the same shell session, type `kit` or
   `resnapshot`, send a new KIT dump from the Rytm, and confirm the new kit name
   and fingerprint before mutating.
3. Decode and dry-run before sending. Do not assume the previous capture is still
   representative if the hardware kit changed.
4. Inspect Pad 1 values before every send. Pad 1 filter, LFO, and AMP attack
   controls should be absent from the active send plan, and Pad 1 tune-style
   source values should stay within plus or minus 3 of the captured kit value.
5. Start with `preset live` or `preset kick-safe`, then `status` before the
   first mutation during live validation.
6. Use `changes` before `send` to confirm later pads show SRC rows such as
   BT/XT/HH/CY/CB source parameters, not only filters and LFOs.
7. `Y`, `V`, and `N` layer on the current staged plan. Use `fresh` or `Z` first
   when you want an anchor-only zone mutation.
8. `send` repeats the currently staged plan. Type `go` to generate the next
   variation and send it in one command, or type another mutation command,
   `again`, or `next` before the next `send` to stage a variation without
   sending. Repeated variations should stay inside the selected anchor-relative
   lane.
9. Use `lock N` for pads that should remain untouched, `pad N strong` or
   `pad N wild` only for intentional performance moments, and `guards reset`
   when you want to clear the session guardrails. Locked pads are omitted from
   the next `send`.
10. Use `lane lfo off` as the trusted default. Open `lane lfo micro` when you
    want subtle motion and use `Z` plus `send` to return those LFO rows to the
    captured anchor.
11. Use `lane fx micro` for normal variation and `lane fx normal` for deliberate
    section changes.
12. Send one variation at a time and listen.
13. If the kick loses punch again, stop sending and record the exact command plus
   Pad 1 planned values before changing code.
14. Do not use `flow-shift` live unless explicitly testing machine switching;
   it is a discovery/studio mode until separately validated.

## Next Engineering Work

- Collect amount/density/bias listening notes for hats, cymbals, synth voices,
  and noise pads so performer-friendly randomizer presets can be derived from
  real outcomes.
- Validate selector discovery on BD Acoustic `Waveform`, SY Raw waveform rows,
  filter mode, and LFO waveform before making any named `discover` macro.
- Add a plan-inspection CLI/report that prints Pad 1 planned values before armed
  send.
- Consider whether `send` should optionally support changed-only sends. The
  current shell sends the full active snapshot plan, which is clearer and
  repeatable, but can be verbose.
