# Analog Four Audio Patch Genome Replay Playbook

> Status: in-flight

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

## Fresh-Clone Questions

1. Where does A4 inference live? `rytm_randomizer/style_analysis/analog_four_patch_inference.py`.
2. Where are writable hardware facts? `rytm_randomizer/data/analog_four_sysex_calibration.py`.
3. What writes a complete saved kit? The pure renderer under `devices/strategies/`, guarded by `cockpit/export/analog_four_kit.py`.
4. How is a batch committed? Immutable generation artifacts first, stable manifest last.
5. What may currently reach A4 saved-kit SysEx? Filter2 Resonance only; every other DNA row is sidecar/live-dial guidance.
