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
- Payload fingerprint: `8800dcf6f5467e85`
- Decoded machine values by pad:
  `{1: 0, 2: 26, 3: 32, 4: 28, 5: 7, 6: 30, 7: 0, 8: 0, 9: 24, 10: 33, 11: 25, 12: 12}`
- Important limitation: current SysEx decoder trusts the dump for kit identity
  and machine identity, but does not yet decode every current SRC/filter/amp
  knob value. Live-safe still needs conservative anchors until the per-parameter
  offset decoder is added.

## Commands That Exist Now

Dry-run the latest captured kit:

```powershell
python -m rytm_randomizer.app --dry-run --rytm-performance-snapshot captures\20260528-232829-analog-rytm-current-kit-reassembled.syx --rytm-performance-mode live-safe --rytm-performance-style flow-shift --rytm-performance-depth safe --rytm-performance-seed 890002068
```

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

## Safe Resume Steps For Tomorrow

1. Start with a fresh current-kit SysEx capture from the Rytm.
2. Decode and dry-run before sending. Do not assume the previous capture is still
   representative if the hardware kit changed.
3. Inspect Pad 1 values before every send. For live-safe `safe` depth, kick
   tune and filter frequency should remain near their anchors.
4. Send one seed at a time and listen.
5. If the kick loses punch again, stop sending and record the exact seed plus
   Pad 1 planned values before changing code.
6. Do not use `flow-shift` live unless explicitly testing machine switching;
   it is a discovery/studio mode until separately validated.

## Next Engineering Work

- Add the Rytm current-kit per-parameter offset decoder so mutations can anchor
  to the actual captured SRC/filter/amp values, not just recipe anchors.
- Add a plan-inspection CLI/report that prints Pad 1 planned values before armed
  send.
- Consider a stricter `performance-safe` profile for live sets:
  - Pad 1 kick: tiny tune window, tiny filter window, delay/reverb locked low.
  - Non-kick pads: moderate filter/FX/pan variation.
  - Machine switching locked out unless user explicitly selects studio/discovery.
- Record accepted and rejected seeds from listening sessions so future ranges can
  be tightened from real outcomes.
