# Digitakt saved-kit wire fixtures

Captured by: Steve
Date: 2026-09-30
Device: Digitakt (MK1) (`digitakt_mk1`)
OS version: 1.52A
Dump menu path: SETTINGS > SYSEX DUMP > SYSEX SEND > PATTERN

Note: the on-screen menu item is labeled **PATTERN**, not KIT. Digitakt does
not have a separately-named Kit object the way the Analog Rytm / Analog Four
do; PATTERN is the closest equivalent — it carries the per-track sound
settings (the "Kit" role) *and* the sequencer/trig data together. The
`digitakt_saved_kit` naming in this fixture directory, and the "kit"-flavored
naming throughout `rytm_randomizer/data/digitakt_saved_kit_layout.py` and
`rytm_randomizer/devices/strategies/digitakt_snapshot_decoder.py`, was
inherited from the Rytm/A4 Kit/Pattern split and does not accurately describe
the Digitakt object model. Renaming that is tracked as follow-up work, not
done in this PR.

## Files

- `digitakt_mk1_kit_filter_low.syx`: initialized kit, track 1 filter frequency LOW; SHA256 `737061d28779e8891755cbc7909b9d3ba3d7ada256bef6b1be885d5d4fa1da0f`.
- `digitakt_mk1_kit_filter_high.syx`: same kit, ONLY track 1 filter frequency changed to HIGH; SHA256 `68997250165e6a08415385324d8de2831df71513c2aba478f6fe38ffce733bd4`.

## Status

These captures are **evidence**, not send authority. The first MK1 pair
promoted exactly one fact: the location of track 1 filter frequency
(`DIGITAKT_MK1_TRACK1_FILTER_FREQUENCY_OFFSET` in
`rytm_randomizer/data/digitakt_saved_kit_layout.py`), pinned byte for byte by
`tests/test_digitakt_real_captures.py` and
`tests/test_devices_strategies_digitakt_pattern_codec.py`. Anything further
needs its own fixture-backed byte isolation, checksum and exact re-encode
evidence per `.claude/rules/targeted-mutation-safety.md` #6, and nothing here
enables a send (`DIGITAKT_OFFSETS_PROMOTED = False`).

## Provenance

Steve created these from a disposable initialized kit on their own
hardware specifically for this repository's verification work. They contain
no commercial sample-pack content and no personal performance material, and
may be redistributed under the repository licence for test and verification
use.
