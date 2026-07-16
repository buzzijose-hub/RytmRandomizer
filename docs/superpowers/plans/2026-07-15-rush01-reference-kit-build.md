# RUSH01 Reference-Anchored Kit Build Plan

Status: archived (completed with both device builds blocked by mapping gaps)

Review-repair note: device-assisted MIDI does not relax this result. Offline
KIT output remains blocked until critical saved-kit mappings are verified; the
armed app path sends approved live CC only and never emits or saves SysEx.

**Goal:** Attempt the RUSH01 Analog Rytm MKII and Analog Four MKII semantic
kit builds from the approved local reference dumps. Generate a device output
only when every requested critical field has a positively mapped raw location,
typed conversion, and integrity rule. Otherwise produce an exact mapping-gap
report without emitting a partial kit.

## Workstreams

1. Verify both YAML specifications and both single-frame reference dumps.
2. Add a shared, passive Elektron kit-envelope codec that starts from a decoded
   reference frame, preserves its header and unknown object bytes, and
   recalculates verified 7-bit packing, checksum, and length fields.
3. Prove byte-identical reference decode/encode round trips in tests.
4. Audit every requested semantic field against repository mappings, enum
   tables, converters, capture evidence, and machine/track compatibility.
5. Generate each device independently only if its critical audit is complete.
   Always write the build report; write a mapping-gap report for blocked
   devices.
6. Run focused tests, architecture tests, the full suite, coverage for touched
   production files, and the lint trio. No MIDI ports are opened and no files
   are sent to hardware.

## Current Audit Findings

- The approved references are valid single SysEx frames and are the binary
  compatibility anchors. Firmware remains `UNVERIFIED_FROM_DEVICE`.
- Analog Four has only three candidate-promoted SysEx parameter calibrations
  in the repository. The requested oscillator, noise, amp, envelope, and most
  filter fields therefore remain critical mapping gaps.
- Analog Rytm has verified sound-record offsets for NRPN rows `0..39` and
  machine type `103`, but no promoted raw-kit offset for requested track level
  NRPN `100`. CB Metallic `PW1` and `PW2` are absent from the established
  machine mapping, and several requested selectors are numeric-only without a
  verified enum label mapping.

## Abstraction Review

- The shared `snapshot/envelope.py` helper is the existing canonical Elektron
  packing boundary, so packing, u14 integrity fields, and the reference-bound
  codec extend that module rather than creating per-device copies.
- Device-specific envelope facts remain beside the existing device snapshot
  strategies and consume constants from the current Rytm kit layout and A4
  offset manifest.
- The codec is generic and parameterized; there will not be parallel A4 and
  Rytm implementations of the same packing/integrity algorithm.

## Plan-Requirements Conformance

Per docs/PLAN_REQUIREMENTS.md, this plan commits to:

- [x] Gate 1 (100% branch coverage on touched files) - focused branch coverage
  will be run for every touched production module.
- [x] Gate 2 (V1.34 parity byte-identical) - no parity fixture regeneration;
  the existing suite will verify unchanged output.
- [x] Gate 3 (lint/format/type clean) - ruff, black, isort, and available type
  checks will run before closeout.
- [x] Gate 4 (dead-code purge) - new public codec surfaces are directly tested
  and no commented-out implementation is added.
- [x] Gate 5 (docs updated) - this plan, build artifacts, status, and relevant
  architecture wording are updated together.
- [x] Gate 6 (type-system hygiene) - frozen dataclasses and concrete byte/int
  types; no `Any`, ABC, or unchecked DTO boundary.
- [x] Gate 7 (observability adoption) - N/A: the codec is a pure bytes-in,
  bytes-out helper with no state transition, send, or runtime guardrail.
- [x] Gate 8 (test hygiene) - intent-named tests mirror the snapshot and device
  strategy surfaces and reuse repository reference files.
- [x] Gate 9 (module organization) - work remains in existing `snapshot/`,
  `devices/strategies/`, `data/`, and `tests/` locations.
- [x] Gate 10 (string dispatch hygiene) - no mode/intensity/page dispatch is
  introduced.
- [x] Gate 11 (shared fixtures) - no duplicated multi-file fixture body is
  introduced.
- [x] Gate 12 (Final constants) - new module-level configuration values use
  `Final` or frozen dataclass instances.
- [x] Gate 13 (environment variables) - no environment variable is added.
- [x] Gate 14 (maintainability) - pre-change mapping audit completed; final
  diff receives a post-change audit.
- [x] Gate 15 (learning phase) - reusable envelope findings will update the
  existing Elektron envelope documentation rather than create a duplicate
  skill.
- [x] Gate 16 (execution shape) - the user explicitly selected the currently
  opened repository; independent reads/tests are parallelized and all writes
  remain one bundled logical change with no stacked PR.
- [x] Gate 17 (abstraction reuse) - extends the canonical Elektron envelope
  helper and existing device strategy/data facts.
- [x] Gate 18 (architecture freshness) - snapshot-envelope documentation and
  its diagram are updated if the codec changes the documented boundary.
