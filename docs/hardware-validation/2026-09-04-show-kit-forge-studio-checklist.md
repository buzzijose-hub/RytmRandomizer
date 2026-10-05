# Show Kit Forge Remaining Studio Checklist

Prepared: 2026-09-04
Updated guidance: 2026-10-05 (no new physical observations recorded)

Status: **pending operator-present hardware validation**

This is the exact remaining physical checklist for Show Kit Forge. Every box
is intentionally blank. Repository tests, successful file transfer, a manual
save attestation, or a semantic match must not be rewritten as an unobserved
hardware result.

## Next Studio Session: One Bounded Rehearsal

Use the exact portable build and hashes in the PR #254 software delivery
receipt, not an older running server. Close FL Studio/Overbridge before the
session. Record both firmware versions, configured track channels, unique
exact port names, backed-up source files and operator-selected disposable
source/favorite slots in the table below. Do not overwrite a show KIT.

1. Start disarmed. Capture and explicitly retain the saved source KITs; verify
   their identities. Cancel an input capture once and confirm the source is
   unchanged. No output authority is needed for these steps.
2. Target only Rytm Pad 2, protect Pad 1, and lock all A4 tracks. Start at 10%
   using previously observed non-paired common controls (amp decay, overdrive
   and reverb send). Filter frequency remains held by the paired-precision gate
   despite its earlier bounded observation. Inspect the exact plan before arming. New SRC
   eligibility is documented-only, not permission to skip its own rehearsal.
3. Follow Section 2 for one exact-plan audition and manual saved-KIT reload.
   Confirm listening/front-panel recovery, unaffected pads and a matching fresh
   saved-KIT capture. Local UNDO/reset is not hardware recovery.
4. Only after recovery passes, select the retained candidate again, save it as
   a local favorite, and save the local bank. Restart disarmed and verify the
   favorite/source identity persists. This still does not save the hardware.
5. Audition that same candidate with a new matching source capture and new
   exact-plan confirmation. Manually save the intended result to a separate
   disposable favorite KIT, dump it back, compare the candidate fields, reload
   it manually and rehearse recovery again. Record the actual result separately.

Small/large local mutations and show-pack inspection can be rehearsed offline;
large live changes, hardware favorite reload and show use remain NOT READY
until their exact workflow/recovery has passed. A4/BOTH SEND, fractional paired
controls and automatic hardware restore remain unavailable. Pi validation is
separate from this computer build.

The CY Ride experiment comes later on a disposable KIT copy: collect a saved
baseline, change/save/dump one SRC control, return/save/dump its original value,
then compare decoded bytes against the canonical address. Start with Hit Decay
and retain the three frames plus the displayed values/firmware. An inbound CC
alone cannot resolve a saved-slot association; one passing field cannot unlock
its neighbours. Every CY Ride SRC control remains blocked until its own
association is positively established.

## Fixed authority boundary

- Analog Four Filter 1 Frequency candidate generation is local-file-only and
  reports `hardware_send_validated = false`.
- There is no Show Kit Forge A4/BOTH SEND action. Do not arm an A4 output in
  Cockpit. Section 2a is a separately approved legacy single-CC probe, not a
  Forge plan or a bypass for a blocked plan.
- Cockpit may send only the selected Rytm RAM-only plan through the existing
  PREPARE, exact plan-id/port confirmation, and `ArmedApply` boundary.
- **Reset Cockpit audition to source** changes Cockpit state only. It sends no
  restore bytes; hardware restoration is a manual source-KIT load followed by
  recapture.
- Cockpit never performs a persistent KIT SAVE. Save on each instrument, then
  recapture. Local candidate retention, favorite selection and bank save do not
  save or reload either instrument.
- Any changed paired-control row in the effective target-minus-lock scope
  blocks the whole Rytm plan with `paired_control_precision_unverified`,
  including a mixed safe/paired plan.
  Preserve the blocked plan/reasons; do not filter a subset, send its MSB only,
  round a value or substitute the legacy probe. No fractional MIDI is approved.
- OXI project/pattern/chapter/cue values are metadata only. OXI keeps ownership
  of sequencing, notes, triggers, mutes, and pattern motion.
- Favorite recapture compares promoted semantic values. Show-time preflight is
  stricter: it compares both whole-decoded-payload fingerprints exactly. The
  retained SysEx frame SHA-256 is a separate evidence field.
- The passive `device-support-inventory-report` (text or `--json`) describes
  independent catalog, saved-file, transport/precision and physical-evidence
  dimensions. It does not enumerate hardware or grant send/show readiness.
  See [Device Support Inventory](../DEVICE_SUPPORT_INVENTORY.md).
- Pi #252 is touch UI/packaging groundwork: non-simulation APPLY is refused,
  deployment is on hold, and touch/display behavior and packaging remain
  unvalidated pending focused work and their own acceptance.

## Ordered isolated gates

Use [Cockpit Quickstart sections 1-4](../COCKPIT_QUICKSTART.md#1-prerequisites)
for exact Windows prerequisites, `Set-Location`, launch and build spellings;
[section 6a](../COCKPIT_QUICKSTART.md#6a-remaining-operator-present-studio-rehearsal)
contains the passive report and bounded legacy command. Verify the actual
build receipt: an older portable copy does not acquire new safety fixes from
these instructions. No new tests/builds or hardware actions are recorded here.

| Order | Gate | Expected result and limit |
|---|---|---|
| 1 | Input-only sources (Section 1) | Exact unambiguous inputs, valid retained source frames; no output authority. |
| 2 | First physical output (Section 2) | One Pad 2 Rytm candidate at 10%, Pad 1 protected, all A4 tracks locked; one ready plan/SEND, then stop and restore. |
| 3 | Separately approved legacy probe (Section 2a) | One integer non-paired A4 CC on one configured spare-kit track; manually restore before proceeding. |
| 4 | Existing A4 offline scratch (Section 3) | Transfer/save/recapture the existing four values in disposable slot 20; offline field evidence only. |
| 5 | Favorite/show gates (Sections 4-6) | Manual instrument saves, fresh semantic recaptures and another exact paired preflight. |

Stop at each restored baseline. No exhaustive per-pad/per-track offset or
stride mapping rounds are requested; do not repeat the August 28 matrix.
The first physical gate ends after Section 2, not after a bank-wide rehearsal.

## Session record

Use the identified Windows portable copy and record its full source commit from
`BUILD-MANIFEST.json`, together with both binary hashes. The current PR review
state and downloaded artifact receipt belong in the software closeout record;
they do not fill any observation below.

Fill these fields during the studio session, not beforehand.

| Field | Observation |
|---|---|
| Date/time/time zone | |
| Operator | |
| Cockpit build/commit | |
| Manifest source commit / shell SHA-256 / sidecar SHA-256 | |
| Passive support report source/evidence reference | |
| Analog Rytm model/OS | |
| Analog Four model/OS | |
| Manual SysEx librarian/tool and version | |
| Exact Rytm input port | |
| Exact Rytm output port | |
| Exact A4 input port | |
| Legacy A4 probe output (separate from Cockpit) | |
| Cockpit A4 output port opened? (required result: No) | |
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
- [ ] Select an exact input name that occurs once in the fresh backend listing.
      Duplicate exact names must refuse before open, not choose the first.
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
| Rytm source capture id/time | |
| A4 source filename | |
| A4 source frame SHA-256 | |
| A4 source whole-payload fingerprint | |
| A4 source capture id/time | |
| Source bank revision | |
| Capture failure/cancellation evidence reference, if observed | |
| Passive candidate/plan identity evidence reference, if observed | |

Stop if either frame fails validation, the exact ports are ambiguous, a source
slot is not disposable, or either source fingerprint was not retained.

**Cancellation and passive persistence:** an accepted DISARM during pending
input capture or transport teardown cancels polling. A cancelled or stale
late result must not adopt a source; keep the previous verified capture. A
passive browser disconnect/reconnect or rejected DISARM must preserve offline
candidate, plan and source identity within the same running sidecar session.
Armed teardown instead revokes live authority; reconnect never re-arms.
Explicit local retention/bank save is needed for durable work, and still is
not a hardware save. Record any violation and stop. Do not introduce duplicate
ports, stale results or live failures just to fill a box; fake-regression
receipts and actual physical observations remain separate.

## 2. First physical test: Rytm one-pad ArmedApply and restoration

- [ ] Adopt the retained Rytm source capture as the cue's immutable source.
- [ ] Select Pad 2 only, set depth to 10%, and lock Pad 1. Confirm effective
      scope contains Pad 2 only; all other pads are untargeted or locked and
      all A4 tracks are locked.
- [ ] Generate the candidate and record its id and expected semantic
      fingerprint.
- [ ] Manually reload the source KIT and make a fresh matching input-only
      source dump through the device rail. This clears the current candidate
      and prepared plan; the dump alone does not prove unsaved RAM was restored.
- [ ] Click **Select for audition** on that candidate after the fresh capture,
      then **Preview Rytm**. Arm only the exact Rytm output with the launch
      token, then **Prepare exact plan**. Record the exact output port, current
      send-plan id, affected pad ids, packet count, and message count.
- [ ] Verify the plan names Pad 2 only and excludes every locked/untargeted pad.
- [ ] Require `ready=true` with no blockers before confirming SEND. If a mixed
      safe/paired candidate is blocked, retain its plan id/reasons and stop;
      `paired_control_precision_unverified` refuses the entire plan even if
      safe single-CC packets are visible. Do not deliberately manufacture this
      case on the live rig or send a filtered subset.
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
- [ ] Observe actual front-panel/listening recovery and unaffected pads; a
      saved-state dump alone cannot prove unsaved RAM was restored.
- [ ] Request a fresh input-only Rytm dump and preserve it.
- [ ] Confirm its whole-payload fingerprint exactly equals the retained Rytm
      source whole-payload fingerprint; separately preserve the returned frame
      SHA-256.

| Rytm observation | Value |
|---|---|
| Candidate id | |
| Expected semantic fingerprint | |
| Fresh matching source capture id/time | |
| Exact output port | |
| Send-plan id | |
| Plan readiness/blockers | |
| Affected pads | |
| Packet/message count | |
| ArmedApply result | |
| Pad 2 observation | |
| Locked/untargeted pad comparison | |
| Cockpit log/screenshot reference | |
| Manually reloaded source slot | |
| Front-panel/listening recovery observation | |
| Returned filename | |
| Returned frame SHA-256 | |
| Returned whole-payload fingerprint | |
| Recovery capture id/time | |
| Exact baseline match | |
| Operator verdict | |

Stop after this one confirmation and restored baseline. On any refusal, port
ambiguity, transport error or unexpected change, preserve the plan/log,
DISARM and manually reload the protected source. Assume partial delivery after
a transport error; never retry the old plan. Recapture the exact source and
observe recovery before any later candidate/attempt, then reselect, preview,
arm and PREPARE again. If transport is wedged, close Cockpit/stop the sidecar,
disconnect the selected path after disarming, reconnect and rebuild fresh
evidence; reconnect does not re-arm. Never save an audition over the source.

### 2a. Separate legacy A4 single-CC probe

Run only with separate operator approval and Cockpit closed; keep one output
path active. This is the existing `app.py --arm --a4-send-param` helper, not
Show Kit Forge A4/BOTH SEND. Follow the exact Windows command in
[Quickstart section 6a](../COCKPIT_QUICKSTART.md#6a-remaining-operator-present-studio-rehearsal).

- [ ] On a disposable saved A4 KIT, set Track 1 OSC1 PWM Depth to `31` and save
      manually. Confirm MIDI channel 1 actually targets Track 1 (`--channel 0`
      is zero-based); cancel on uncertainty.
- [ ] At the helper's prompt, select the exact intended A4 output and send
      `--parameter 'OSC1 PWM Depth' --channel 0 --value 32` once. Expected
      console text: `Sent exactly one A4 parameter CC message.` The helper
      closes its output and exits.
- [ ] Separately observe only that track/control at `32`, listen, manually
      reload the saved source, verify `31` returns, and make a fresh input-only
      recapture. Stop on any unrelated change or failed restoration.

| Legacy A4 probe observation | Value |
|---|---|
| Separate approval / source slot / configured channel | |
| Exact output / console evidence | |
| Track/control observation / listening note | |
| Manual reload / restored value / recapture id/time | |
| Unexpected change / operator verdict | |

This proves only one integer non-paired CC in that setup. It does not validate
native saved-KIT offsets, paired CC/NRPN precision, fractional MIDI, recipes or
general A4/BOTH SEND. It must never bypass a blocked Cockpit candidate.

## 3. A4 four-track offline candidate return

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
      `filter1_frequency_pending_scratch_validation.json` in a separately
      resource-approved verification run; no re-run is recorded here.
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
      fingerprint. If any slot/header normalization occurred, document it
      explicitly and do not call the returned frame byte-identical to the
      generated file. Check unrelated-byte isolation, not only four values.
- [ ] Manually reload the protected A4 source, observe physical recovery, and
      make a fresh baseline capture before proceeding.
- [ ] Leave Show Kit Forge A4 SEND and every unpromoted saved-KIT field blocked.

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
| Manual source reload / physical recovery / baseline capture | |
| Operator verdict | |

Stop on a wrong value/track, any unrelated visible change, transfer ambiguity,
checksum/re-encode failure, or uncertainty about whether the KIT was saved.

### What this A4 test does and does not complete

The offline preparation report revalidates the selected candidate against the
retained source and records scope, current capture, recovery slot and exact
output-name intent. It always remains blocked. Imported evidence, a typed port
name, and a successful scratch return cannot arm an output.

After the scratch result is physically verified, a separately reviewed transport
decision is still required. Filter 1 Frequency's paired CC18/50 and NRPN(1,40)
address facts do not prove how the saved Q8.8 value maps to a live message value.
The current event planner rejects paired CC and the Cockpit renderer accepts
seven-bit CC triples. Do not infer or test guessed packets on the instrument.
Capture documented transport-specific value/destination behavior before adding
that transport to the existing guarded seam. A persistent SysEx route also needs
an implemented and physically verified capture/restore contract; Cockpit's
persistent KIT SAVE refusal remains in force.

Future activation must bind the final candidate/source hashes, selected tracks
minus locks, current capture/reload proof, connection generation, exact port,
per-action confirmation and recovery slot to one expiring plan. Exercise those
conditions with fakes first, then perform the reviewed operator-present send
and restoration test. None of these observations or activation approvals is
inferred by this checklist.

## 4. Favorite, manual saves, and semantic recaptures

- [ ] Mark the intended paired candidate favorite and confirm the UI says it is
      not saved on either instrument.
- [ ] Explicitly retain the favorite artifacts required by export.
- [ ] Confirm local retention/bank save did not save or reload hardware; keep
      favorite destination slots distinct from both immutable source slots.
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

The bounded first Rytm gate passes only with Section 1 source evidence and the
one scoped Section 2 audition plus actual manual recovery observation and exact
baseline recapture. It supports only that audition/recovery, not show readiness,
general A4/BOTH SEND or persistent KIT writes. The separately approved Section
2a probe supports only its single integer CC; Section 3 supports review of its
offline field only. Neither unlocks live paired/fractional transport.

The full studio gate passes only when Sections 1-6 are completed with preserved
evidence, the A4 candidate is physically returned after a manual save, the Rytm
one-pad audition is followed by an exact-baseline manual reload/recapture, and
every cue passes the fresh paired whole-payload-fingerprint preflight. Anything
less remains pending; leave the corresponding boxes and observation fields
blank.
