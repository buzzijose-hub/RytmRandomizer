# Closeout Failure Propagation Checkpoint

## Purpose

Record the safety hardening that makes closeout fail when any Python test step
fails.

This is a closeout reliability improvement. It does not change runtime
behavior, command behavior, MIDI behavior, active behavior, or hardware
behavior.

## Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this slice:

- `8bda703 Add project identity name shortlist`

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## Root Cause

The closeout script logged every test step, but a failed native command could
be followed by later successful commands and still allow the outer PowerShell
process to exit `0`.

That meant a failed test step could be visible in the log but not reliably
reflected by the closeout process exit code.

## What Changed

Files changed by this milestone:

- `Scripts/closeout_check.ps1`
- `tests/test_closeout_contract.py`

Closeout now:

- tracks failed Python test steps with `$script:closeoutFailures`
- registers each test step exit code with `Register-CloseoutStepExit`
- writes a failure line into the closeout summary when a test step exits
  nonzero
- exits `1` if any registered test step fails
- includes a new `=== Test: Closeout Contract ===` section

## New Test Coverage

`tests/test_closeout_contract.py` verifies:

- the closeout script tracks failed test steps
- the closeout script has an explicit failure exit path
- every Python test invocation registers its exit status
- the closeout contract test itself is included in closeout

## Why This Matters

Closeout is the project's safety net. This hardening makes the safety net more
trustworthy by ensuring failed test steps cannot be treated as a clean
closeout.

This reduces the chance of future bugs slipping through during larger work
packets.

## Confirmed Boundaries

This milestone adds no:

- runtime execution
- dispatch
- command execution
- mutation execution
- active CLI command
- real MIDI
- MIDI dependency
- port discovery
- port opening
- package metadata change
- active behavior
- hardware behavior

## Verification

Targeted red/green evidence:

- `python .\tests\test_closeout_contract.py` failed before the closeout
  hardening.
- `python .\tests\test_closeout_contract.py` passed after the closeout
  hardening.

Full closeout evidence:

- `powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1`
  passed.
- V1.34 reference diff was empty.
- package metadata diff was empty.

## Decision

Closeout failure propagation is now guarded by tests and included in the full
closeout suite.

Next recommended task:

- continue with another mock-only/passive software slice, or create a small
  checkpoint update after this closeout hardening
