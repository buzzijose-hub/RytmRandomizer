# Analog Four saved-kit wire fixtures

These two 2,770-byte files are the disposable `Test 1` hardware captures used
to pin the first Analog Four MKII saved-kit writer result.

- `filter2_res_000_source.syx`: Track 1 Filter2 Resonance `0`; SHA256
  `a8fbb0552b953815fc1f6358299116866b0d94002692933abccf83655023cc6b`.
- `filter2_res_127_expected.syx`: Track 1 Filter2 Resonance `127`; SHA256
  `5ebb386677aff324ef96d631e7888a9681caefbd976bdc2eac69b52a0fb0e26b`.

The renderer test changes the source value to `127` and requires every output
byte to match the expected hardware file. The project is initialized and the
fixtures contain no user performance pattern or audio recording.
