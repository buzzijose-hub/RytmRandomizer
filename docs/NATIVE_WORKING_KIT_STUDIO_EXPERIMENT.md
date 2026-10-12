# A4 Saved Versus Working KIT Studio Experiment

Status: prepared; no physical observation or query has been performed by this
software session. The tested Windows delivery is source `096be3ed94ec` at
`C:/Users/Jose Buzzi/Documents/ShowKitForgeStudio/show-kit-forge-studio-096be3ed94ec`.
Its `studio-procedure/DELIVERY-RECEIPT.md` records binary hashes and actual
offline acceptance. Prior verified packages remain preserved.

```powershell
Set-Location "C:\Users\Jose Buzzi\Documents\ShowKitForgeStudio\show-kit-forge-studio-096be3ed94ec"
.\Launch-Offline.ps1 -Hidden:$false
```

## One Preflight

Record actual model/firmware (static research targets A4 MKII OS 1.55), exact
input/output names, T1 MIDI channel, disposable KIT name/slot, original backup
path/hash, operator and times. Stop if firmware differs; do not update it to
make this experiment pass. Stop the sequencer and external clock/automation;
keep KIT/track selection stable and monitoring low. Never use a show KIT.

This delivery does not acquire query replies. Future supervised request
acquisition requires a separately reviewed operator-present tool through the
sanctioned output boundary, explicit arming and exact request confirmation.
The inert research request vectors are not permission to bypass that boundary.
The comparison command below only reads supplied files; MIDI stays disabled.

## Six Ordered Files

1. Manually save the disposable baseline and retain an indexed `0x52` dump as
   `01_manual_B.syx`. Read exact native F1 word **B** and record the forward
   panel label. Protocol 1/1, KIT storage 11 and four Sound storage-6 bindings
   are formats, not installed firmware. Never infer B from a screen label.
2. Make one clearly separated T1 F1 panel change without SAVE, reload or KIT
   switch. Record action/time and displayed label. Obtain supervised indexed
   `0x62` request / `0x52` reply as `02_indexed_after_edit_B.syx`; it should
   still contain B. A preliminary pre-edit queried dump is optional evidence,
   not a substitute for this post-edit indexed observation.
3. Obtain supervised working `0x68` request / `0x58` reply as
   `03_working_U.syx`. Require valid exact **U != B** and forward label agreement.
   Header slot alone does not establish coherent working data selection.
4. Repeat under the same quiescent conditions as `04_working_repeat_U.syx`.
   Require exact U again and retain all raw/body differences, including unknowns.
5. Explicitly SAVE manually. Obtain indexed reply as `05_post_save_U.syx`;
   its F1 should now equal exact U. Record the save action separately.
6. DISARM. Restore the backed-up B state manually to the same disposable slot,
   reload it and retain fresh indexed `06_recovered_B.syx`. Require full body
   recovery; investigate every raw/header discrepancy. Local UNDO, favorites
   and report output do not restore the instrument.

## File-Only Report

Place the six files in the example directory, or change each explicit path.
This is a developer CLI using the existing repository environment, not a
hardware transmission command. It writes JSON to stdout; it does not overwrite
inputs. Origin is a declaration, not a physical certification.

```powershell
Set-Location "C:\Users\Jose Buzzi\.codex\worktrees\rytm-studio-mapping\RytmRandomizer"
$env:RYTM_RAND_MIDI_BACKEND = "off"
& "C:\Users\Jose Buzzi\Documents\RytmRandomizer\.venv\Scripts\python.exe" -m rytm_randomizer.cli a4-working-kit-compare `
  --manual-baseline "output\local\a4-working-kit\01_manual_B.syx" `
  --indexed-baseline "output\local\a4-working-kit\02_indexed_after_edit_B.syx" `
  --working-first "output\local\a4-working-kit\03_working_U.syx" `
  --working-repeat "output\local\a4-working-kit\04_working_repeat_U.syx" `
  --post-save "output\local\a4-working-kit\05_post_save_U.syx" `
  --recovered "output\local\a4-working-kit\06_recovered_B.syx" `
  --track 1 `
  --evidence-origin operator_supplied_files
```

This command uses the verified assembly checkout, not the unchanged primary
checkout. The report includes SHA-256 identities,
source kinds/slots/format versions, all four exact F1 words and labels, every
raw/body difference and separate repeat/save/recovery checks. Optional
`--baseline-label` and `--changed-label` compare recorded forward labels only;
identical labels cannot prove identical native words.

## Stop Conditions And Permissions

| Observation | Meaning / Next Action |
| --- | --- |
| B / U / repeat / explicit save / recovery agree | Evidence only for this quiescent F1 experiment on this unit/firmware. Review a separately gated readback capability; do not unlock general synchronization. |
| Working stays B | Freshness hypothesis not established. Investigate binding/timing; no promotion. |
| Indexed already contains U before SAVE | Saved/indexed separation not established. Preserve files and investigate. |
| Repeat, slot, structure or integrity differs | Stop. No coherent usable baseline is established. |
| Non-F1 body differences | Keep every difference unresolved until evidenced; do not whitelist them to manufacture a pass. |
| Recovery differs | Stop hardware work and restore the known backup manually before another experiment. |

The report never claims operator chronology, pending/concurrent freshness,
complete KIT atomicity, installed firmware, query authority or automatic restore.
A4/BOTH sending, CY Ride SRC and paired precision remain held. Rytm ordinary
LFO Depth is a separate later experiment using its own OS 1.72 contract; do not
borrow A4 CC-preservation or NRPN-row timing rules for it.
