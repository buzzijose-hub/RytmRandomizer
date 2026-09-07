# Show Kit Forge architecture before and after

Date: 2026-09-04

Status: in-flight — architecture delta recorded; root closeout and studio
validation remain pending.

| Concern | Before this bundle | After this bundle |
| --- | --- | --- |
| Paired preparation | Dual-device capture, scope, stage, and Rytm send existed as separate Cockpit controls. | `cockpit/show_bank/workspace.py` composes those controls into one ordered paired-cue workflow without owning MIDI. |
| A4 captured-KIT mutation | A4 current-KIT bytes could be captured exactly, but operator-facing saved-KIT mutation remained mapping-blocked. | `devices/strategies/analog_four_filter1_frequency_candidate.py` renders only fixture-proven Filter 1 Frequency Q8.8 fields on Tracks 1-4; its result is file-only and carries no SEND authority. |
| Durable favorites | Incoming captures stayed in memory unless handled by older general library/export paths; there was no paired favorite lifecycle. | Versioned Show Bank DTOs distinguish source, candidate, favorite, manual save attestation, recapture verification, and current-session preflight. Exact frames are retained only by explicit source/favorite/candidate actions. |
| Persistence | Profile/library stores and atomic export writers supplied the established local-I/O pattern. | `cockpit/show_bank/store.py` reuses the atomic writer for immutable canonical revisions and content-addressed `.syx`; paired evidence publishes in one write set. |
| Portable handoff | Passive live-kit package-audition/operator-package reports described review/recovery but did not store operator-selected hardware captures. | `cockpit/show_bank/export.py` applies the same review/recovery vocabulary to self-contained, checksummed show packs. Imported packs are catalog-only and cannot lend candidates to ArmedApply. |
| Rytm audition | Preview, history, PREPARE, exact plan/port confirmation, and guarded `ArmedApply` existed. | Show Kit Forge selects an existing candidate into those exact seams; only a successful live send records a process-local unsaved-hardware audition. No second sender exists. |
| A4 audition | No captured-KIT transmit boundary was validated. | The UI exposes the exact offline file for manual scratch-slot validation while A4 Cockpit SEND stays blocked. |
| Readiness | Stage readiness described device lanes, not saved paired favorites. | Promoted semantic recapture proves a saved favorite; a later full-fingerprint paired dump grants show readiness only for the current Cockpit process. Restart/import makes the prior grant historical. |
| OXI | OXI ownership was declarative. | Project/pattern/chapter remain metadata; no OXI transport or state mutation was added. |

## Dependency direction

```text
cockpit/ws + frontend
        |
        v
cockpit/show_bank  ---> cockpit capture/history/stage/send-plan/export writer
        |                           |
        v                           v
cockpit/data/show_bank       snapshot + devices public codecs/strategies
```

The new nested package owns orchestration and local evidence only. It does not
introduce a package-root module, device registry, generic library replacement,
hardware sender, or dependency from a lower layer back into Cockpit.

## Deliberately unchanged authority

- V1.34 engines/runners and all 505 golden files remain byte-frozen.
- `mido==1.3.3` and `python-rtmidi==1.5.8` remain pinned and lazily imported.
- Only the existing armed Rytm boundary may open output; A4 generated files are
  never transmitted by Show Kit Forge.
- SAVE remains refused. A hardware favorite exists only after the operator
  saves on each instrument and supplies newer recaptures.
