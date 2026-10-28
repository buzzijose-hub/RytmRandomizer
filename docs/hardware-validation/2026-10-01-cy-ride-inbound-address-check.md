# CY Ride inbound address check

Operator-present input-only observation on Analog Rytm MKII OS1.72, saved
disposable KIT01, pad11 CY Ride. The observer ran from source
`76634665a719eed661724dfa31cca004a5cbe75a` using the existing
`python -m rytm_randomizer.app --arm --rytm-cc-observe` entry point. This mode
opens one MIDI input and reports that it opens no output and sends no MIDI.
The studio server was not restarted; its loaded source remained `2a19b094`.

The operator read existing settings without changing them: OUTPUT TO
`MIDI+USB`, ENCODER DEST `INT+EXT`, PARAM OUTPUT `CC`, OUTPUT CH `TRK CH`.
Fresh enumeration selected `Elektron Analog Rytm MKII 4`. Separate observer
sessions captured one physical control at a time with playback stopped.

| Physical control | Operator-reported movement | Actual inbound messages |
| --- | --- | --- |
| TYP / Cymbal Type | C → D → C | Channel10 (MIDI channel11), CC20, values3 →2 |
| HIT / Hit Decay | 48 →49 →50 →49 →48 | Channel10, CC19, values49 →50 →49 →48 |

The HIT instruction requested one step up; the operator reported two steps
up and back. The receipt preserves the actual sequence. An initial TYP pass
recorded zero messages after an ambiguous reply of `c`; it supplied no
address evidence. The subsequent isolated TYP pass supplied the two messages
listed above. Printed catalog labels were treated as hypotheses; the raw
addresses and the operator's isolated control movement establish this result.

Both successful sessions observed no NRPN or out-of-scope messages. The
operator then manually reloaded saved KIT01 using NO + PLAY MODE, without
saving, and separately confirmed TYP C and HIT48. No output, hardware SAVE,
new saved-KIT frame or unsaved-RAM readback was performed.

This supports the current catalog's live CC association for these controls
and only the displayed/received values observed here. It does not prove a
complete selector domain, outbound behavior, NRPN addresses or the native
saved-slot association. The CY Ride slot discrepancy remains blocked in
captured mutation and live planning. No safe range, automatic restoration,
Pi acceptance or touring readiness is granted.

Private local output retains the raw observer logs and structured receipt
`cyride-inbound-receipt-2026-10-01.json`. SHA256 of the TYP log is
`f34c9f8892038e76532f6d8da77ecde324584fe70d6b2ca6083f095038ef1c29`;
HIT log is `ac3f67d444f84f546dfbaa48a66f9e4e9ed05c3b48bf6cd3023dbc322f427a6e`.
These identify observation logs, not native KIT frames. The raw private logs
are not committed.
