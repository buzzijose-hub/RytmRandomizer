# Analog Four Audio Patch Genome Architecture Before and After

> Status: in-flight

## Before

| Capability | State |
|---|---|
| Audio analysis | General style `FeatureReport`; no A4 candidate renderer. |
| A4 parameter representation | Manual-backed DNA and MIDI facts; no generated batch contract. |
| Elektron encoding | Shared 7-bit unpacking; no canonical inverse packer for saved-kit rendering. |
| A4 saved-kit handling | Passive decode and differential calibration only. |
| Publication | General atomic writer; no multi-artifact transaction identity or stable manifest. |
| Operator path | Reports and manual dialing; no audio-to-batch command. |

## After

| Capability | State |
|---|---|
| Audio analysis | One decoded recording produces typed measured features and deterministic A4 inference. |
| A4 parameter representation | Four candidate genomes carry complete front-panel DNA plus CC/NRPN/manual/deferred plans. |
| Elektron encoding | Canonical pack/unpack helpers and one shared A4 saved-kit codec validate complete frames. |
| A4 saved-kit handling | Pure renderer is exposed through an optional capability on the registered A4 device; guarded exporters write hardware-validated mutations only. |
| Publication | Shared batch codec/contracts/publication modules provide canonical hashes, immutable artifacts, per-track lock, and manifest-last commit. |
| Operator path | Passive batch generation emits `.syx`, complete DNA sidecars, and a hashed manifest; the verified reader feeds dry-run/armed plans and recorded renders feed a passive acoustic ranker. |

## New Contracts

- `AnalogFourPatchGenome` and inference DTOs represent deterministic candidate DNA.
- `AnalogFourPatchSendPlan` separates live-sendable, front-panel, and deferred rows.
- `AnalogFourSavedKitRenderResult` reports validated frame output without file I/O.
- `AnalogFourAudioPatchBatchExportResult` acknowledges one committed generation and manifest.
- `AnalogFourPatchTransportPlan` lets the app consume canonical or verified stored plans structurally.
- `AudioSynthesisFeatures` and the pure render-rank DTOs separate reusable acoustic evidence from A4 artifact I/O.
- `AnalogFourExportErrorCode` is the shared bounded service/CLI failure vocabulary.

## Reuse Decisions

- Reused `FeatureReport`, `cli_registry`, the registered `AnalogFourDevice`, observability metrics/logging, calibration data, strategy modules, and `atomic_write`.
- Extended the generic Elektron envelope with its canonical inverse rather than adding an A4-only packer.
- Added no parallel device package, registry, MIDI adapter, or top-level module.
- Deleted no V1.34 API and renamed no parity-owned symbol.
