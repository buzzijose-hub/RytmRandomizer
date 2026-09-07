# Show Kit Forge Remaining Studio Checklist

Prepared: 2026-09-04

Status: **pending operator-present hardware validation**

This is the exact remaining physical checklist for Show Kit Forge. Every box
is intentionally blank. Repository tests, successful file transfer, a manual
save attestation, or a semantic match must not be rewritten as an unobserved
hardware result.

## Fixed authority boundary

- Analog Four Filter 1 Frequency candidate generation is local-file-only and
  reports `hardware_send_validated = false`.
- There is no Show Kit Forge A4 SEND action. Do not arm an A4 output.
- Cockpit may send only the selected Rytm RAM-only plan through the existing
  PREPARE, exact plan-id/port confirmation, and `ArmedApply` boundary.
- **Reset Cockpit audition to source** changes Cockpit state only. It sends no
  restore bytes; hardware restoration is a manual source-KIT load followed by
  recapture.
- Cockpit never performs a persistent KIT SAVE. Save on each instrument, then
  recapture.
- OXI project/pattern/chapter/cue values are metadata only. OXI keeps ownership
  of sequencing, notes, triggers, mutes, and pattern motion.
- Favorite recapture compares promoted semantic values. Show-time preflight is
  stricter: it compares both whole-decoded-payload fingerprints exactly. The
  retained SysEx frame SHA-256 is a separate evidence field.

## Session record

Fill these fields during the studio session, not beforehand.

| Field | Observation |
|---|---|
| Date/time/time zone | |
| Operator | |
| Cockpit build/commit | |
| Analog Rytm model/OS | |
| Analog Four model/OS | |
| Manual SysEx librarian/tool and version | |
| Exact Rytm input port | |
| Exact Rytm output port | |
| Exact A4 input port | |
| A4 output port opened? (required result: No) | |
| OXI connection/role | |
| Monitoring level | |
| Disposable Rytm source slot | |
| Disposable Rytm favorite slot | |
| Protected A4 source slot (different from scratch slot 20) | |
| Disposable A4 favorite slot | |
| Show bank id/revision | |
| Cue/entry id | |

## 1. Before any output

- [ ] Use disposable projects/KIT slots on both Elektron instruments; preserve
      the real show project separately.
- [ ] Manually save the starting Rytm and A4 KITs.
- [ ] Request an input-only current-KIT dump from each device.
- [ ] Confirm family, frame length, checksum, and exact codec re-encode pass for
      both frames.
- [ ] Explicitly retain both source frames in Show Kit Forge.
- [ ] Record each full-frame SHA-256 and each whole-payload capture fingerprint
      below; these are different hashes.
- [ ] Confirm no output port was auto-selected or auto-armed.
- [ ] Confirm OXI still owns sequencing and the Cockpit shows direct OXI
      control disabled.

| Source evidence | Value |
|---|---|
| Rytm source filename | |
| Rytm source frame SHA-256 | |
| Rytm source whole-payload fingerprint | |
| A4 source filename | |
| A4 source frame SHA-256 | |
| A4 source whole-payload fingerprint | |
| Source bank revision | |

Stop if either frame fails validation, the exact ports are ambiguous, a source
slot is not disposable, or either source fingerprint was not retained.

## 2. A4 four-track offline candidate return

Repository artifact under test:

`tests/fixtures/analog_four_saved_kit/filter1_freq_tracks_16_25_48_50_80_75_112_25_pending.syx`

Expected immutable facts:

| Fact | Expected |
|---|---|
| Source SHA-256 | `3d38dd4369cbd6ea496adcfb7698025cd57e21332ffae1dd5a98e18ae767ea95` |
| Generated SHA-256 | `829eee0209a248012a968e96df33acd007619a0078255c4fd034b5afda3520dd` |
| Frame/native/packed bytes | `2770 / 2410 / 2755` |
| Generated checksum / encoded length | `9533 / 2760` |
| Encoding/range | unsigned big-endian Q8.8, `0x0000..0x7F00` |
| Native offsets | `128,129,478,479,828,829,1178,1179` |
| Native track stride | `350` bytes |
| Track values | T1 `16.25`; T2 `48.50`; T3 `80.75`; T4 `112.25` |

- [ ] Recompute the generated file's SHA-256 and confirm it is exactly the
      value above.
- [ ] Re-run local decode/re-encode and confirm checksum, re-decoded values,
      and intended-native-byte isolation agree with
      `filter1_frequency_pending_scratch_validation.json`.
- [ ] Preserve the source in another slot or project first. This artifact
      addresses slot 20 (native slot byte 19); slot 20 must be disposable and
      must not be an immutable source anchor in the current Show bank.
- [ ] Keep Cockpit's A4 MIDI output unarmed. Use the studio's known working
      manual SysEx receive procedure to load the file into disposable A4 KIT
      slot 20. Record the actual tool and observed destination above.
- [ ] Confirm only Filter 1 Frequency is under test and inspect T1 `16.25`, T2
      `48.50`, T3 `80.75`, and T4 `112.25` on the front panel.
- [ ] Audition at a safe monitoring level and write an actual listening note.
- [ ] Save the KIT on the A4 before requesting a dump. The captured evidence
      shows that an unsaved panel edit is not reflected by this dump path.
- [ ] Request a fresh input-only current-KIT dump and preserve its exact bytes.
- [ ] Confirm the returned frame passes codec/checksum/re-encode validation.
- [ ] Decode the returned Filter 1 Frequency values and confirm all four exact
      Q8.8 values.
- [ ] Compare and record both the returned frame SHA-256 and whole-payload
      fingerprint. If any slot/header
      normalization occurred, document it explicitly and do not call the
      returned frame byte-identical to the generated file.
- [ ] Leave A4 SEND and every non-Filter-1-Frequency field blocked.

| A4 observation | Value |
|---|---|
| Transfer destination slot observed | |
| Front-panel values observed | |
| Listening note | |
| Saved before recapture | |
| Returned filename | |
| Returned frame SHA-256 | |
| Returned whole-payload fingerprint | |
| Returned decoded values | |
| Returned codec/checksum/re-encode result | |
| Generated-vs-returned byte comparison | |
| Unexpected parameter/track change | |
| Operator verdict | |

Stop on a wrong value/track, any unrelated visible change, transfer ambiguity,
checksum/re-encode failure, or uncertainty about whether the KIT was saved.

## 3. Rytm one-pad ArmedApply and manual restoration

- [ ] Adopt the retained Rytm source capture as the cue's immutable source.
- [ ] Select Pad 2 only, set depth to 10%, and lock Pad 1. Confirm effective
      scope contains Pad 2 only; all other pads are untargeted or locked.
- [ ] Generate the candidate and record its id and expected semantic
      fingerprint.
- [ ] Manually reload the source KIT and make a fresh matching input-only
      source dump through the device rail. This clears the current candidate
      and prepared plan; the dump alone does not prove unsaved RAM was restored.
- [ ] Click **Select for audition** on that candidate after the fresh capture,
      then **Preview Rytm** and **Prepare exact plan**. Record the exact output
      port, current send-plan id, affected pad ids, packet count, and message count.
- [ ] Verify the plan names Pad 2 only and excludes every locked/untargeted pad.
- [ ] Arm the exact Rytm output with the launch token. Do not arm A4.
- [ ] Acknowledge the manual source reload in the SEND form and confirm this
      exact current plan once. Record the outcome and log evidence. Repeat the
      source reload, capture, selection, and preparation before any later audition.
- [ ] Audition with OXI still providing sequencing/triggers; verify Pad 2
      changed as intended.
- [ ] Compare Pad 1 and every other untargeted pad against the source evidence;
      record any difference and stop on an unintended change.
- [ ] Disarm Rytm.
- [ ] Click **Reset Cockpit audition to source** and confirm only Cockpit's
      active selection/live audition state clears; do not claim this restored
      the instrument.
- [ ] Manually reload the saved Rytm source KIT.
- [ ] Request a fresh input-only Rytm dump and preserve it.
- [ ] Confirm its whole-payload fingerprint exactly equals the retained Rytm
      source whole-payload fingerprint; separately preserve the returned frame
      SHA-256.

| Rytm observation | Value |
|---|---|
| Candidate id | |
| Expected semantic fingerprint | |
| Exact output port | |
| Send-plan id | |
| Affected pads | |
| Packet/message count | |
| ArmedApply result | |
| Pad 2 observation | |
| Locked/untargeted pad comparison | |
| Cockpit log/screenshot reference | |
| Manually reloaded source slot | |
| Returned filename | |
| Returned frame SHA-256 | |
| Returned whole-payload fingerprint | |
| Exact baseline match | |
| Operator verdict | |

Stop and disarm on stale-plan refusal, port/device ambiguity, transport error,
unexpected pad change, or any mismatch after manual reload. Do not save the
audition over the source slot.

## 4. Favorite, manual saves, and semantic recaptures

- [ ] Mark the intended paired candidate favorite and confirm the UI says it is
      not saved on either instrument.
- [ ] Explicitly retain the favorite artifacts required by export.
- [ ] Manually load/apply the favorite on each device, then save each KIT to its
      recorded disposable favorite slot.
- [ ] Record both manual save attestations. Confirm the state remains
      `hardware-saved` / attested-unverified.
- [ ] Make fresh input-only Rytm and A4 current-KIT dumps after both saves.
- [ ] Retain the exact recapture frames and record both their frame SHA-256
      values and whole-payload fingerprints.
- [ ] Run paired recapture verification. Confirm the promoted semantic
      fingerprint for each device matches its selected favorite.
- [ ] Confirm the cue advances to `verified`, not `show-ready`.

| Favorite/recapture evidence | Rytm | Analog Four |
|---|---|---|
| Favorite candidate/artifact id | | |
| Manual save slot | | |
| Save attestation time | | |
| Recapture filename | | |
| Recapture frame SHA-256 | | |
| Recapture whole-payload fingerprint | | |
| Expected semantic fingerprint | | |
| Observed semantic fingerprint | | |
| Semantic match | | |
| Retained artifact id | | |

Stop if a favorite artifact was not explicitly retained, either capture was
made before its manual save, a semantic projection mismatches, or the UI skips
directly from an attestation to show-ready.

## 5. Exact show-time whole-payload-fingerprint preflight

Run this immediately before the rehearsal/show use for each cue; a prior pass
is not a standing grant after device state changes.

- [ ] Manually load the recorded favorite slots on both instruments.
- [ ] Request new input-only current-KIT dumps from Rytm and A4.
- [ ] Confirm both fresh frames pass family/checksum/length/exact-reencode
      validation.
- [ ] Run **Run show-time preflight**.
- [ ] Confirm the fresh Rytm whole-payload fingerprint exactly equals the
      retained successful Rytm recapture fingerprint.
- [ ] Confirm the fresh A4 whole-payload fingerprint exactly equals the
      retained successful A4 recapture fingerprint.
- [ ] Confirm `show-ready` appears only when both exact comparisons pass.
- [ ] Introduce no mismatch merely to satisfy this checklist. If a naturally
      observed mismatch occurs, confirm readiness is revoked, preserve the
      mismatch evidence/reason, recover the correct KIT, recapture, and rerun.
- [ ] Repeat the whole-payload-fingerprint preflight for every ordered cue.
- [ ] Confirm bank-level readiness names no missing or mismatched cue.

| Show-time evidence | Rytm | Analog Four |
|---|---|---|
| Expected retained-recapture fingerprint | | |
| Fresh current fingerprint | | |
| Exact whole-payload-fingerprint match | | |
| Mismatch/recovery evidence, if any | | |

| Final bank evidence | Value |
|---|---|
| Cue order checked | |
| Every cue show-ready | |
| Bank readiness result | |
| Operator go/no-go | |

## 6. Show-pack and OXI boundary

- [ ] Export only after all required source/favorite/recapture frames were
      explicitly retained.
- [ ] Verify the `.show-pack` manifest, complete file set, SHA-256 list, SysEx
      framing, cue order, and recovery text before import/use.
- [ ] Confirm package/import identifiers are filename-safe names resolved below
      server-owned roots; no client-supplied filesystem path was used.
- [ ] Confirm each cue's OXI project/pattern/chapter/cue fields are descriptive
      metadata only.
- [ ] Confirm no OXI command was emitted and OXI remained the sequencer.

## Acceptance rule

The studio gate passes only when Sections 1–6 are completed with preserved
evidence, the A4 candidate is physically returned after a manual save, the Rytm
one-pad audition is followed by an exact-baseline manual reload/recapture, and
every cue passes the fresh paired whole-payload-fingerprint preflight. Anything
less remains pending; leave the corresponding boxes and observation fields
blank.
