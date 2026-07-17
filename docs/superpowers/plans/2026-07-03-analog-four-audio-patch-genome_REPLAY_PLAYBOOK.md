# Analog Four Audio Patch Genome Replay Playbook

> Status: in-flight

Implementation is complete; the physical full-patch rehearsal remains pending.

## Resume This Run

1. Open the `codex/a4-sysex-roundtrip-writer` worktree and read the plan, state file, and append-only run log.
2. Reconcile the local branch with PR #214 using `git status --short --branch` and `gh pr view 214`.
3. Run the focused A4 export, batch, inference, and writer tests before editing.
4. Preserve all hardware-accepted fixture hashes. Do not regenerate V1.34 parity fixtures.
5. Promote a new writable A4 field only after exact reference reconstruction, a novel uncaptured value, and independent cross-track hardware confirmation.
6. Keep generated SysEx passive. The batch command writes local files and never opens a MIDI port.
7. Run full pytest, architecture, parity, coverage, lint, Pyright, vulture, and `scripts/code_review_gate.py` before push.
8. Append material milestones and review findings to the run log; update the state file atomically.

## Reproduce One Batch

```powershell
python -m rytm_randomizer.cli analog-four-audio-patch-batch `
  --audio C:\path\to\reference.wav `
  --source-kit C:\path\to\initialized-kit.syx `
  --output-dir C:\path\to\batch `
  --track 1 `
  --candidates 4 `
  --json
```

Verify that the response contains `generation_id`, `manifest_path`, and `manifest_sha256`; each manifest candidate must match the SHA-256 of its `.syx` and sidecar.

## Rehearse And Send One Exact Candidate

```powershell
python -m rytm_randomizer.app --dry-run --a4-patch-send-plan `
  --batch-manifest C:\path\to\batch\a4-t1-audio-patch-batch.json `
  --candidate 1

python -m rytm_randomizer.app --arm --a4-patch-send-plan `
  --batch-manifest C:\path\to\batch\a4-t1-audio-patch-batch.json `
  --candidate 1 --confirm-a4-patch-send-plan
```

Candidate 1 currently contains 39 live-routable rows and 59 transport
messages. The manifest reader verifies the sidecar and nested plan before the
armed path opens a port.

## Rank Hardware Renders

```powershell
python -m rytm_randomizer.cli analog-four-audio-patch-rank `
  --reference C:\path\to\reference.wav `
  --manifest C:\path\to\batch\a4-t1-audio-patch-batch.json `
  --render 1=C:\path\to\candidate-1.wav `
  --render 2=C:\path\to\candidate-2.wav `
  --json
```

The reference must hash to the batch source. Add candidates 3 and 4 when their
recordings are available.

## Fresh-Clone Questions

1. Where does A4 inference live? `rytm_randomizer/style_analysis/analog_four_patch_inference.py`.
2. Where are writable hardware facts? `rytm_randomizer/data/analog_four_sysex_calibration.py`.
3. What writes a complete saved kit? The pure renderer under `devices/strategies/`, guarded by `cockpit/export/analog_four_kit.py`.
4. How is a batch committed? Immutable generation artifacts first, stable manifest last.
5. What may currently reach A4 saved-kit SysEx? Filter2 Resonance only; every other DNA row is deferred from SysEx but live-routable through the verified sidecar.
6. How is the auditioned candidate selected for live send? `--batch-manifest` plus `--candidate`; nested hashes and event routing are verified before output opens.
7. How does hardware feedback enter? Record candidate renders and run `analog-four-audio-patch-rank`; reviewed captures can then become corpus evidence.
