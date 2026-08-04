# AL16 R2 Analog Rytm Mapping Closure

> Status: in-flight
>
> Review repair is complete; studio evidence is pending.

## Goal

Replace the Phase R1 list of 18 independent Analog Rytm writer blockers with a
bounded, offline evidence workflow. This phase does not emit an AL02 kit and
does not promote candidate offsets as verified mappings.

## Safety boundary

- Decode saved-kit files offline through the existing validated codec.
- Never enumerate, open, or write a MIDI port.
- Never transmit MIDI or SysEx.
- Never mutate the initialized reference file.
- Treat manual-backed addresses plus decoded-kit layout offsets as candidate
  evidence until a saved-kit before/after comparison is reviewed.
- Keep the ambiguous `ch_basic` recipe key unresolved. It must not be silently
  translated to `ch_classic` or `hh_basic`.

## Bounded proof plan

### Session 1: configured saved-kit capture

Create one disposable AL02-like kit by hand, save it once, and export one
saved-kit dump. Compare that dump with the initialized reference offline. This
is a multi-gap capture, not a sequence of independent calibration rounds. One
comparison can provide candidate evidence for:

- machine selection on pads 1, 3, and 9;
- BD Classic source parameters on pad 1;
- XT Classic decay and F2 tuning on pad 6;
- the selected pad-9 hat decay parameter after the machine ambiguity is
  resolved; and
- amp volume on pads 1, 3, 6, and 9.

The analyzer reports candidate changed/unchanged locations and all other raw
changes. A human review remains required before any location or converter is
added to the strict writer allowlist.

The report is accepted only when its inputs agree on four provenance facts:

- SHA-256 of the exact recipe bytes;
- SHA-256 of the exact R1 gap-manifest bytes;
- the deterministic recipe identifier recomputed from the recipe; and
- the initialized-reference SHA-256 recorded in the manifest.

### Session 2: destination-slot proof

Import one harmless scratch kit into an explicitly selected scratch slot,
dump it back, and compare only the object-number/header evidence. This is a
separate proof because the Phase R1 codec deliberately does not claim which
header byte owns the destination slot.

## Verification strategy

- Synthetic saved-kit frames exercise the analyzer without private reference
  dumps.
- Every current blocker must be assigned to exactly one evidence class.
- Unknown blocker paths fail closed.
- Ambiguous machine/source combinations remain unlocated.
- Reports are deterministic and explicitly marked `review_required`.
- Report provenance, evidence counts, status literals, and review state are
  typed and tested.
- Path-role collisions and unsafe paths fail before file I/O; operator output
  uses safe basenames and structured error codes.
- The CLI records one observability operation and bounded success/failure
  metrics without exposing machine-local paths.
- Focused tests run single-process to keep workstation load bounded.

## Plan-requirement decisions

- **Gate 14 - maintainability:** canonical Rytm track layout, machine aliases,
  and CC/NRPN mappings are reused; duplicate exporter offsets, pad bounds, and
  controls are removed. The learned Elektron workflow records the multi-gap
  capture pattern below.
- **Gate 15 - dependency policy:** no dependency or lock-file change is part of
  R2. The hardware-pinned `mido` and `python-rtmidi` versions remain untouched,
  and the passive command does not import either backend.
- **Gate 16 - integration strategy:** this is one direct PR against
  `modularize-v1.34`, not a stacked PR. The implementation, tests, deterministic
  evidence, docs, and learned workflow ship together on the same branch.

## Exit criteria

R2 is ready for a studio handoff when the offline analyzer and tests pass and
the operator can complete the two proof sessions without running hundreds of
single-parameter calibration rounds. AL02 compilation remains blocked until
the resulting evidence is reviewed and promoted in a later writer change.

## Passive comparison command

After the single manually configured AL02 saved-kit dump is available, run:

```powershell
Set-Location (Join-Path $env:USERPROFILE "Documents\RytmRandomizer")

.\.venv\Scripts\python.exe -m rytm_randomizer.cli `
  al16-rytm-mapping-evidence `
  --reference output\local\reference\RYTM_Test1_Init_Kit.syx `
  --configured output\local\al16\AL02_LOCK_RYTM_CONFIGURED.syx `
  --recipe specs\al16\AL02_LOCK_RYTM.yaml `
  --gap-manifest output\al16\AL02_LOCK_RYTM_manifest.json `
  --report output\local\al16\AL02_LOCK_RYTM_mapping_evidence.json
```

This command only decodes local files and writes a review-required JSON
report. Its inputs are provenance-bound before comparison. It does not
enumerate MIDI ports, open hardware, transmit MIDI, or promote candidate
mappings automatically.
