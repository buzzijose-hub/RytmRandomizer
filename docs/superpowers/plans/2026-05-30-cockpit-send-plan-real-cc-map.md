# Cockpit Send-Plan Real CC Map

> Status: in-flight

**Goal:** Make the cockpit SEND preflight produce real Analog Rytm MKII CC packets for the 12-pad cockpit surface instead of deterministic synthetic placeholder CCs.

**Context:** Jose's local GUI test showed preview knobs moving but SEND did not produce useful hardware behavior. PR #145 expanded the cockpit mock surface to 12 pads and richer Overbridge-style parameter groups, but the prepared SEND plan still emitted synthetic parameter hashes on MIDI channel 0. The repo's May 26 hardware validation confirmed the track-channel model: Rytm pad N maps to mido channel N - 1 for the outbound one-CC validation path.

**Architecture:** Keep the cockpit passive/mock-first by default. The send-plan builder stays deterministic and inert; it only creates packet metadata. The real adapter remains the only component that opens a MIDI port, and only in armed mode. Unknown machine/parameter pairs fail closed by omitting packets and blocking SEND when no sendable packet remains.

## Scope

- Add a cockpit data-layer map from compact UI parameter keys to Analog Rytm MKII CC numbers.
- Use snapshot pad machines to resolve machine-specific short keys such as `tun`, `dec`, and `snap`.
- Use common Rytm page mappings for Sample, Filter Envelope, Amp Envelope, and LFO controls.
- Map pad 1 through pad 12 to mido channel 0 through 11.
- Remove the stale send-plan `_DEFAULT_MIDI_CHANNEL` Final-constant allowlist entry.

## Deliberate Boundaries

- No real MIDI send in tests.
- No MIDI port opening.
- No SysEx, kit save, transport, pattern, or unattended hardware behavior.
- No V1.34 parity fixture regeneration.
- No frontend layout work; the UI surface already landed in the local-testing feedback bundle.
- Analog Four remains outside this Rytm-specific send-plan slice.

## Verification

- RED first: updated `tests/cockpit/test_engine_send_plan.py` failed against the synthetic CC/channel implementation.
- Focused cockpit send-plan tests pass.
- Full cockpit test suite passes.
- Architecture gate passes.
- Full pytest suite passes.
- Ruff, Black, and isort pass.

## Follow-Ups

- Expand the map with any remaining official machine-specific keys after manual review of the Rytm manual/Overbridge UI.
- Surface unsendable omitted-parameter counts in the GUI send-plan review panel.
- Add a later hardware-validation runbook entry for a reviewed, explicit cockpit SEND smoke test on a disposable kit.
