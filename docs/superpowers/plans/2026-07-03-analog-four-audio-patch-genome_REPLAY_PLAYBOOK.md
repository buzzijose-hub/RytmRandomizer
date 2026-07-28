# Analog Four Audio Patch Genome Replay Playbook

> Status: in-flight

Closeout hardening, touched-file coverage, parity, typing, lint, mechanical
review, and branch publication are verified. Fresh online checks and a fresh
reviewer verdict remain pending. The physical full-patch rehearsal also remains
pending.

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
The documented/default command produces exactly four deterministic candidates.
The bounded candidate-count seam exists for focused compatibility tests.

Native decoding runs in a spawned child. If it exits abnormally, the parent
must return `inference_failed`, remain alive, and remove its private audio/SysEx
staging directory. Simulated abnormal-exit tests verify containment. Successful
native decoding on Windows remains environment-dependent and is not established.

## Rehearse And Send One Exact Candidate

```powershell
python -m rytm_randomizer.app --dry-run --a4-patch-send-plan `
  --batch-manifest <batch-dir>\a4-t1-audio-patch-batch.json `
  --candidate 1

# Pending supervised physical validation only, after the dry-run and
# single-parameter track/channel check in MANUAL_HARDWARE_VALIDATION.md:
python -m rytm_randomizer.app --arm --a4-patch-send-plan `
  --batch-manifest <batch-dir>\a4-t1-audio-patch-batch.json `
  --candidate 1 --confirm-a4-patch-send-plan `
  --a4-output-port "<exact configured Analog Four output name>"
```

Candidate 1 currently contains 33 live-routable rows and 53 transport
messages. The manifest reader verifies hashes, DNA/event identity, transport
status, and canonical A4 addresses before the armed path opens a port. Six
paired-CC rows remain manual pending 14-bit hardware verification. The guarded
transport rehearsal remains pending and must use a disposable project with
operator-present recovery.

## Rank Hardware Renders

```powershell
python -m rytm_randomizer.cli analog-four-audio-patch-rank `
  --reference <audio-dir>\reference.wav `
  --manifest <batch-dir>\a4-t1-audio-patch-batch.json `
  --render 1=<render-dir>\candidate-1.wav `
  --render 2=<render-dir>\candidate-2.wav `
  --json
```

The reference must hash to the batch source. Add candidates 3 and 4 when their
recordings are available.

## Fresh-Clone Questions

1. Where does A4 inference live? `rytm_randomizer/style_analysis/analog_four_patch_inference.py`.
2. Where are writable hardware facts? `rytm_randomizer/data/analog_four_sysex_calibration.py`.
3. What writes a complete saved kit? The pure renderer under `devices/strategies/`, exposed through the registered A4 saved-kit capability and guarded by `cockpit/export/analog_four_kit.py`.
4. How is a batch committed? Immutable generation artifacts first, stable manifest last.
5. What may currently reach A4 saved-kit SysEx? Filter2 Resonance only; every other DNA row is deferred from SysEx. The verified sidecar exposes 33 live-routable rows and keeps six paired-CC rows manual.
6. How is the auditioned candidate selected for live send? `--batch-manifest` plus `--candidate`; nested hashes and event routing are verified before output opens.
7. How does hardware feedback enter? Record candidate renders and run `analog-four-audio-patch-rank`; reviewed captures can then become corpus evidence.
8. What can open a real MIDI port? Only `python -m rytm_randomizer.app --arm`
   after feature-specific validation/confirmation. Passive commands and the
   local-model copilot have no provider-construction or hardware-send route.

## Current Local Verification

- Focused A4/operator regression suite: 1,577 passed, 1 skipped.
- Architecture: 702 passed.
- Full suite: 6,773 passed, 3 skipped.
- Ruff, Black, isort: clean.
- Touched-file coverage: 100% across 7,573 statements and 1,762 branches.
- V1.34 parity: 685 passed; Vulture, strict Pyright across all 60 touched
  production modules, `git diff --check`, and the mechanical review gate
  passed.
- The literal strict audit across all 109 touched Python paths reports 4,204
  dynamic test-harness typing errors; preserve that Gate 3 exception until
  CODEOWNER acceptance or a dedicated cleanup.
- The pushed SHA and online reviewer status will be recorded on PR #214.
