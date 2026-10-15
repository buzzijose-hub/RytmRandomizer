# AL02 LOCK Rytm Validation

## Result

**BLOCKED: no SysEx was emitted.**

The initialized reference decoded and re-encoded byte-for-byte, but critical requested writer mappings remain unverified. This report is not a successful kit build and is not a forensic recreation claim.

## Verified offline evidence

- The reference frame passed envelope, payload-size, checksum, and length checks.
- Reference decode then encode was byte-for-byte identical.
- The recipe contract, permanent pad roles, and pad/machine compatibility were audited.
- No requested field was written because the full critical preflight did not pass.
- Unknown and reserved reference bytes therefore remain byte-identical.

## Critical mapping gaps

- `destination_slot`: The Rytm kit object-number header byte is not writer-validated on this branch. Evidence required: One scratch-slot import/dump proving the destination header byte.
- `tracks.1.machine`: Saved-kit machine selection has a candidate location but is not writer-validated. Evidence required: A saved-kit before/after capture proving the machine byte and adjacent validity bits.
- `tracks.1.source.dec`: Rytm source parameters are live-addressed but not saved-kit writer-validated. Evidence required: A saved-kit before/after capture proving the machine-specific field location and typed display-to-raw conversion.
- `tracks.1.source.hld`: Rytm source parameters are live-addressed but not saved-kit writer-validated. Evidence required: A saved-kit before/after capture proving the machine-specific field location and typed display-to-raw conversion.
- `tracks.1.source.swd`: Rytm source parameters are live-addressed but not saved-kit writer-validated. Evidence required: A saved-kit before/after capture proving the machine-specific field location and typed display-to-raw conversion.
- `tracks.1.source.swt`: Rytm source parameters are live-addressed but not saved-kit writer-validated. Evidence required: A saved-kit before/after capture proving the machine-specific field location and typed display-to-raw conversion.
- `tracks.1.source.trn`: Rytm source parameters are live-addressed but not saved-kit writer-validated. Evidence required: A saved-kit before/after capture proving the machine-specific field location and typed display-to-raw conversion.
- `tracks.1.source.tun`: Rytm source parameters are live-addressed but not saved-kit writer-validated. Evidence required: A saved-kit before/after capture proving the machine-specific field location and typed display-to-raw conversion.
- `tracks.1.source.wav`: Rytm source parameters are live-addressed but not saved-kit writer-validated. Evidence required: A saved-kit before/after capture proving the machine-specific field location and typed display-to-raw conversion.
- `tracks.1.amp.vol`: This common field is not in the strict saved-kit writer allowlist. Evidence required: A promoted saved-kit location and converter with round-trip evidence.
- `tracks.3.machine`: Saved-kit machine selection has a candidate location but is not writer-validated. Evidence required: A saved-kit before/after capture proving the machine byte and adjacent validity bits.
- `tracks.3.amp.vol`: This common field is not in the strict saved-kit writer allowlist. Evidence required: A promoted saved-kit location and converter with round-trip evidence.
- `tracks.6.source.decay`: Rytm source parameters are live-addressed but not saved-kit writer-validated. Evidence required: A saved-kit before/after capture proving the machine-specific field location and typed display-to-raw conversion.
- `tracks.6.source.target_note`: No approved tuning observation exists for this machine/note pair. Evidence required: A hardware-verified displayed-note/raw-tune observation for this machine.
- `tracks.6.amp.vol`: This common field is not in the strict saved-kit writer allowlist. Evidence required: A promoted saved-kit location and converter with round-trip evidence.
- `tracks.9.machine`: 'ch_basic' is not an exact Analog Rytm machine catalog key. Verified catalog choices for pad 9: ch_classic (CH Classic), oh_classic (OH Classic), ut_noise (UT Noise), ut_impulse (UT Impulse), ch_metallic (CH Metallic), oh_metallic (OH Metallic), hh_basic (HH Basic), hh_lab (HH Lab). Evidence required: Choose the intended existing machine explicitly. The recipe's CH BASIC wording must not be silently translated to CH Classic or HH Basic.
- `tracks.9.source.decay`: Rytm source parameters are live-addressed but not saved-kit writer-validated. Evidence required: A saved-kit before/after capture proving the machine-specific field location and typed display-to-raw conversion.
- `tracks.9.amp.vol`: This common field is not in the strict saved-kit writer allowlist. Evidence required: A promoted saved-kit location and converter with round-trip evidence.

## Safety

- MIDI ports enumerated: 0
- MIDI ports opened: 0
- MIDI or SysEx transmitted: 0
- Partial output files emitted: 0
- Reference file modified: no
- Manual hardware import authorized: no; there is no AL02 SysEx to load

## Deferred output checks

Generated-kit decode, requested-value verification, changed-byte allowlist, output checksum, and hardware import proof are not applicable until all critical mapping gaps are resolved and a complete SysEx is emitted.
