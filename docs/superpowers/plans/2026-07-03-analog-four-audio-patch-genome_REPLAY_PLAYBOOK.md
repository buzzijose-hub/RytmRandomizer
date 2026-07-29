# Analog Four Audio Patch Genome Replay Playbook

> Status: in-flight

Closeout hardening, touched-file coverage, parity, typing, lint, and mechanical
review are verified. Follow-up publication and online state are tracked on
PR #214. Fresh approval and the physical full-patch rehearsal remain pending.

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
  --batch-manifest "<batch-dir>\a4-t1-audio-patch-batch.json" `
  --batch-manifest-sha256 "<reviewed-manifest-sha256>" `
  --candidate 1

# Pending supervised physical validation only, after the dry-run and
# single-parameter track/channel check in MANUAL_HARDWARE_VALIDATION.md:
python -m rytm_randomizer.app --arm --a4-patch-send-plan `
  --batch-manifest "<batch-dir>\a4-t1-audio-patch-batch.json" `
  --batch-manifest-sha256 "<reviewed-manifest-sha256>" `
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
6. How is the auditioned candidate selected for live send? `--batch-manifest`, its reviewed `--batch-manifest-sha256`, and `--candidate`; the manifest digest, nested hashes, and event routing are verified before output opens.
7. How does hardware feedback enter? Record candidate renders and run `analog-four-audio-patch-rank`; reviewed captures can then become corpus evidence.
8. What can open a real MIDI port? Only `python -m rytm_randomizer.app --arm`
   after feature-specific validation/confirmation. Passive commands and the
   local-model copilot have no provider-construction or hardware-send route.

## Current Local Verification

- Focused touched-file A4/operator regression suite: 1,717 passed, 1 skipped.
- Architecture: 705 passed.
- Last uninterrupted production-equivalent full suite: 6,811 passed,
  3 skipped. The exact final tree collects 6,824 tests; online CI is its
  authoritative full-suite result.
- Ruff, Black, isort: clean.
- Touched-file coverage: 100% across 7,952 statements and 1,884 branches.
- V1.34 parity: 685 passed; Vulture, strict Pyright across all 63 touched
  production modules, `git diff --check`, and the mechanical review gate
  passed.
- Dynamic test-harness typing remains the accepted scoped Gate 3 debt;
  production typing remains clean and mandatory.
- Follow-up publication and online reviewer status are recorded on PR #214.
