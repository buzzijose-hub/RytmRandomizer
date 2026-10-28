# October 14 Reliability Candidate

**READY for offline rehearsal and an operator-supervised, backed-up single-Pad2
scratch test. NOT SHOW-READY.** Physical observations and protected human approval
remain pending. Unsigned Windows copy; WebView2 required; no developer Python
environment required. No Arduino implementation or full hardware certification.

## Launch

Close another Studio window through its own UI before launching this copy.

```powershell
Set-Location "C:\Users\Jose Buzzi\Documents\ShowKitForgeStudio\show-kit-forge-studio-d5634cae4ecd"
.\Launch-Offline.ps1 -Hidden:$false
```

The launcher verifies both hashes, forces MIDI/updates off, clears developer/debug
overrides and uses only this build's `user-data`. It refuses an occupied4317 port.
The exact copied launcher was actually started in an isolated namespace with
invalid developer overrides and `auto` supplied beforehand: healthy, disarmed,
no MIDI port, owned cleanup passed. Four fake-process cases separately verify
wrong source/hash/busy-port refusal and valid offline startup. Operator-present
hardware launch was syntax-reviewed, not executed.

## Exact Identity

- Source `d5634cae4ecdde78fe54ae49c99c373a49935753`, version1.34.0.
- Assembly `codex/studio-rytm-mapping`; published `codex/studio-evidence-handoff`;
  PR254 direct base `modularize-v1.34`.
- Windows build38633750348 succeeded:
  https://github.com/buzzijose-hub/RytmRandomizer/actions/runs/38633750348
- Portable artifact11927058247,114127444bytes, archive digest
  `bfa876752de507ad8b52e18022418ae304c8a1adeb46172a76edbb910e2e53c2`.
- Shell7024128bytes, SHA256
  `16e3b58cb7d68aa4b72f75daad89cc65a40cd72b74ded6bbf5e2a5f3e4b1e9b0`.
- Sidecar111776220bytes, SHA256
  `ddc280b12d36e5d4eb18db9ad68c687f5ffb110a719be2dd25b6323a55751891`.
- Launcher2409bytes, SHA256
  `011c5373070e06e0176fa24d8b799e5c0937d5ff47fd033ca6c2505e7ee4b81e`.
- Clean build; sole tracked override `desktop/shell/tauri.conf.json`.
  Python3.11.9/Rust1.99.0/Node20.20.2/Tauri2.11.4.
- Embedded MIDI Guide notice826bytes, SHA256
  `cfbc5ab629d71a6d740bd3fc5a9f469abaea18e36652406c0816d322f9179dd9`,
  extracted from the sidecar and byte-compared with canonical data.

## Supported Update

Noise Fade inference now produces verified signed display values before the
existing centered native encoder. No clamping, encoder widening, scope removal
or substitution of CSV MIDI values. Legacy legal bytes/favorites remain exact;
authenticated schema2 migration changes only the envelope on explicit writes.
Old reads do not rewrite files. Old unlocked Noise Fade sessions require fresh
generation before new refinement.

Qualified pYIN pitch/octave diagnostics are separate from Welch spectral peaks
and the unchanged eleven-feature weighted normalized L1 distance. Neither
voicing estimates nor scores are sound-match accuracy probabilities. Original
quiet/clipping/note-activity checks and exact selected samples persist through
restart; unsuitable or uncertain audio holds refinement. No normalization,
silent crop, automatic tuning or played-note change.

The ledger preserves552CSV rows:403complete contextual address matches,24unique
partial matches,125reference-only A4 rows, and one independently supported BT
Classic Sweep Depth omission. Pinned hashes/upstream blobs, CC-BY-SA4 attribution,
ranges/orientations/enums/units/conflicts/protection and software/native/physical
evidence are distinct. It grants no new authoring/SEND. FX/CV, sequencing,
routing, selectors and OXI-owned controls remain protected. CY Ride saved slots,
UT numeric polarity, SY Chip Speed modes and wire/native machine identities
remain unresolved where no independent evidence establishes them.

## Actual Verification

| Check | Result |
| --- | --- |
| Python full |12343pass/6skip/6known warnings1115.89s, two workers. |
| Fresh coverage |89touched production files100%line/branch;99.44%project purebranch,99%floor unchanged. |
| Final test-only recheck |43pass/6known warnings4.45s. |
| Frontend |1326pass/81files98.69s/allfourcoverage100%; final type/lint/build pass with existing import/chunk warnings. |
| Actual browser reference |Both real-analyzer device paths pass35.0s; octave hold then matching-pitch refinement; no added retry/skip/timeout. |
| Normal push gates |Strict89/defaultlint/black987/isort;910architecture72.92s;697nonfast8.22s including685frozenparity; no bypass. |
| CSV/CLI |103pass23.50s, including eight private malformed/duplicate/missing JSON subprocess refusals preserving inputs/publication. |
| QA verifier |38Node tests3.014s; omission witnesses plus exact separate F1 source/rendered annotations. |
| Packaged Pad2 plan |16.167s/22commands/0fail/7checks; exact packets,1440/600 layout, stale invalidation, disarmed restart/cleanup. |
| Packaged native precision |40.769s/22commands/0fail/10checks; exact values/labels/loss, protected scope, retention/export/recall/restart/cleanup. |
| Packaged reference + real input |88.240s/111commands/0fail; both synthetic devices9candidates/1refinement/1favorite/2recordings each; real A4 eight alternatives across18controls, every selected field independently decoded, two takes retained/held and exact favorite/session reopened. |
| Exact offline launcher |Four fake guards plus actual copied startup, disarmed/no port, owned cleanup. |

Real-input run20:59:01.591Z-21:00:31.098Z. Reference original SHA
`98311dccc2396bc440061186d316a9aa0d71e71b068c76639cf8d69a853faffd`;
selected first8s SHA
`dd28567ceb9427aed4399ebebb1ac77ae4eb14876af4a2b4a10df81668462add`.
Historical takes are quality/persistence exercises, not auditions of the new
18-control candidate; association/physical flags remain false. The reference's
82.095Hz peak is not a qualified fundamental. Quiet/multi-note audio cannot force
refinement. Owned measured samples:310.29-611.72MiB private memory, at most12
processes/4626handles, at least15.78GiBfree RAM; pending high water7. These are
bounded journeys, **not** a new90-minute endurance run or acoustic validation.

Prior failures remain failed evidence: six old schema-expectation failures,
and packaged real01/diagnostic02 failed a QA-only F1 units-equality assumption.
Separate canonical source/rendered witnesses repair that assertion without
weakening raw readback. Final fresh namespace passes. The helper-only repair
does not change production, so this exact binary is retained without rebuilding.
All owned processes/listeners stopped; no observed PC crash/network interruption
or real MIDI/USB enumeration/opening/arming/writes. Originals/fallback untouched.

## Review And Physical Gates

Eight post-push dimensions atd563returnedNoFindings; targeted QA closure also
found none. CodeQL38633717656 succeeds, zero open branch alerts;21-25 dispositions
unchanged. Seven separate default-branch dependency advisories are not resolved.
Exactd563source CI38633717517/38633707798 succeeds33checks/1skip/0fail. Final
receipt publication is recorded in repository closeout. Eddie's renewed
approval/historical14/16 remain pending.
No protected merge. General A4/BOTH, all CY Ride SRC, unverified paired precision,
unsaved synchronization and automatic restore remain held. Local favorites/UNDO/
export are not hardware SAVE/reload. AL02 still fails closed with no new SysEx.

At9p.m., presence alone grants no hardware authorization. Follow
`OCT14-STUDIO-HANDOFF.md`: one backed-up scratch source, four-control Pad2 10%
exact plan, one explicit audition, DISARM, manual KIT reload, front-panel/listening
recovery and fresh whole-payload comparison. Only after recovery passes consider
separate disposable CY Ride mapping, then a separate declared-note A4 take.
Matching operator-present launch: `SUPERVISED-PAD2-PROCEDURE.md`.

Fallback53a935d08582 and its data, original WAVs/CSV/KITs and existing sessions are
preserved. Private configs/audio/KITs/tokens/runtime state are excluded; only
sanitized summaries are in `qa/`. Session start2026-10-14T15:45Z; final end time,
elapsed work, CI/review state and stop reason are accounted at publication.
