# Analog Four saved-kit wire fixtures

These 2,770-byte files are disposable initialized-kit captures and generated
scratch candidates used to pin narrow Analog Four MKII saved-KIT behavior.

## Filter 2 Resonance hardware-write evidence

- `filter2_res_000_source.syx`: Track 1 Filter2 Resonance `0`; SHA256
  `a8fbb0552b953815fc1f6358299116866b0d94002692933abccf83655023cc6b`.
- `filter2_res_127_expected.syx`: Track 1 Filter2 Resonance `127`; SHA256
  `5ebb386677aff324ef96d631e7888a9681caefbd976bdc2eac69b52a0fb0e26b`.

The renderer test changes the source value to `127` and requires every output
byte to match the expected hardware file. The project is initialized and the
fixtures contain no user performance pattern or audio recording.

## Filter 1 Frequency offline-candidate evidence

The August 28 input-only capture pass used saved KIT 20. The application did
not enumerate or open an output port and sent zero MIDI messages.

- `filter1_freq_127_source.syx`: initialized Track 1-4 value `127.00`; SHA256
  `3d38dd4369cbd6ea496adcfb7698025cd57e21332ffae1dd5a98e18ae767ea95`.
- `filter1_freq_000_expected.syx`: saved Track 1 value `0.00`; SHA256
  `5c8406010e86d11caeb628935820967d698b739b2d588ae949a807d358c9bde7`.
- `filter1_freq_063_50_expected.syx`: saved Track 1 value `63.50`; SHA256
  `d6710ca7368e59b8ac136081e61282dd538d49cddeaa5f81571dcff972819429`.

The generated
`filter1_freq_tracks_16_25_48_50_80_75_112_25_pending.syx` fixture has SHA256
`829eee0209a248012a968e96df33acd007619a0078255c4fd034b5afda3520dd`.
It proves deterministic local Q8.8 encoding, four-track stride, canonical
repacking, checksum, and re-decode behavior. It has not been loaded into the
instrument. Its exact pending status and empty observation list are recorded
in `filter1_frequency_pending_scratch_validation.json`.

This evidence authorizes local candidate generation for Filter 1 Frequency
only. It does not grant hardware-send authority or promote any other field.

Jose Buzzi created the sanitized source captures from disposable initialized
kits on project-owned hardware specifically for this repository's round-trip
tests. They contain no commercial sample-pack content and may be redistributed
under the repository license for test and verification use.
