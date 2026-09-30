# Digitakt saved-kit wire fixtures

Captured by: Steve
Date: 2026-09-30
Device: Digitakt (MK1) (`digitakt_mk1`)
OS version: 1.52A
Dump menu path: SETTINGS > SYSEX DUMP > SYSEX SEND > KIT

## Files

- `digitakt_mk1_kit_filter_low.syx`: initialized kit, track 1 filter frequency LOW; SHA256 `737061d28779e8891755cbc7909b9d3ba3d7ada256bef6b1be885d5d4fa1da0f`.
- `digitakt_mk1_kit_filter_high.syx`: same kit, ONLY track 1 filter frequency changed to HIGH; SHA256 `68997250165e6a08415385324d8de2831df71513c2aba478f6fe38ffce733bd4`.

## Status

These are **candidate** captures. They are evidence for a future
offset-promotion workstream and grant no send authority: Digitakt
saved-project byte offsets remain unpromoted
(`DIGITAKT_OFFSETS_PROMOTED = False`), and promotion requires
fixture-backed byte isolation, checksum and exact re-decode evidence
per `.claude/rules/targeted-mutation-safety.md` #6.

## Provenance

Steve created these from a disposable initialized kit on their own
hardware specifically for this repository's verification work. They contain
no commercial sample-pack content and no personal performance material, and
may be redistributed under the repository licence for test and verification
use.
